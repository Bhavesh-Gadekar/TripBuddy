from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import httpx
from fastmcp import Client
from tripbuddy_core.config import settings

logger = logging.getLogger("concierge")

SYSTEM_PROMPT = (
    "You are TripBuddy's travel concierge. "
    "Help guests find, review, message about and book stays by using your tools. "
    "Format your responses cleanly and readably using structured markdown: bold listing titles with their listing ID (e.g. `lst-goa-001`), clear bullet points for details (price, rating, highlights), and concise summaries. "
    "Be concise, decisive, and minimize redundant tool lookups."
)

_cached_gemini_client = None


def _get_gemini_client():
    global _cached_gemini_client
    from google import genai
    if _cached_gemini_client is None:
        _cached_gemini_client = genai.Client(api_key=settings.LLM_API_KEY)
    return _cached_gemini_client

# Keys that Gemini's FunctionDeclaration schema does not accept
_GEMINI_UNSUPPORTED_SCHEMA_KEYS = {
    "additionalProperties",
    "additional_properties",
    "$schema",
    "$id",
    "examples",
    "default",
    "definitions",
    "$defs",
    "allOf",
    "anyOf",
    "oneOf",
    "not",
    "if",
    "then",
    "else",
}

_DEPRECATED_GEMINI_MODELS = {
    "gemini-2.5-flash": "gemini-3.5-flash-lite",
    "gemini-2.0-flash": "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
    "gemini-1.5-flash": "gemini-3.5-flash-lite",
    "gemini-3.8-flash": "gemini-3.5-flash-lite",
    "claude-3-5-sonnet-20241022": "gemini-3.5-flash-lite",
}


def _resolve_gemini_model(model_name: str) -> str:
    """Map deprecated/sunset model names to active Gemini models."""
    return _DEPRECATED_GEMINI_MODELS.get(model_name, model_name)


def _sanitize_schema_for_gemini(schema: Any) -> Any:
    """Recursively strip keys Gemini doesn't support in function parameter schemas."""
    if isinstance(schema, dict):
        return {
            k: _sanitize_schema_for_gemini(v)
            for k, v in schema.items()
            if k not in _GEMINI_UNSUPPORTED_SCHEMA_KEYS
        }
    if isinstance(schema, list):
        return [_sanitize_schema_for_gemini(item) for item in schema]
    return schema


async def run_concierge_loop(
    prompt: str,
    session_id: str,
    user_id: Optional[str] = None,
    mcp_url: Optional[str] = None,
    mock_mode: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Execute the Concierge agent loop using ONLY the MCP client.

    The Concierge NEVER imports the service layer directly.
    It connects only to settings.MCP_SERVER_URL (or passed mcp_url) and discovers tools via MCP.

    user_id is passed in the MCP meta so the MCP server can resolve identity even
    when the local session DB and the MCP server's DB are separate instances.
    """
    server_url = mcp_url or settings.MCP_SERVER_URL
    steps: List[Dict[str, Any]] = []

    async with Client(server_url) as mcp_client:
        tools = await mcp_client.list_tools()
        tool_map = {t.name: t for t in tools}

        provider = (mock_mode or settings.LLM_PROVIDER).lower()
        api_key = settings.LLM_API_KEY

        # Fall back to scripted model when no real key is available
        use_mock = (
            provider in ["mock", "scripted"]
            or not api_key
            or api_key.startswith("mock")
        )

        if use_mock:
            return await _run_scripted_model(
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
                mcp_client=mcp_client,
                tool_map=tool_map,
                steps=steps,
            )

        if provider == "anthropic":
            return await _run_anthropic_loop(
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
                mcp_client=mcp_client,
                tools=tools,
                steps=steps,
            )
        elif provider == "openai":
            return await _run_openai_loop(
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
                mcp_client=mcp_client,
                tools=tools,
                steps=steps,
            )
        elif provider == "gemini":
            return await _run_gemini_loop(
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
                mcp_client=mcp_client,
                tools=tools,
                steps=steps,
            )
        else:
            return await _run_scripted_model(
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
                mcp_client=mcp_client,
                tool_map=tool_map,
                steps=steps,
            )


async def _execute_tool_via_mcp(
    mcp_client: Client,
    tool_name: str,
    arguments: dict,
    session_id: str,
    steps: list,
    user_id: Optional[str] = None,
) -> Any:
    """Execute tool strictly through the MCP client.

    Both session_id and user_id are passed in meta so the MCP server can:
    1. Log to concierge_tool_calls by session_id
    2. Resolve user identity from user_id directly (fallback when DBs differ)
    3. Use the caller's db_url if running against a specific DB instance (e.g. tests)
    """
    meta: Dict[str, Any] = {
        "session_id": session_id,
        "db_url": settings.DATABASE_URL,
    }
    if user_id:
        meta["user_id"] = user_id

    res = await mcp_client.call_tool(tool_name, arguments, meta=meta)

    data = res.data if res.data is not None else (res.content[0].text if res.content else "")
    steps.append({
        "tool": tool_name,
        "arguments": arguments,
        "result": data,
    })
    return data


async def _run_scripted_model(
    prompt: str,
    session_id: str,
    mcp_client: Client,
    tool_map: dict,
    steps: list,
    user_id: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Deterministic scripted model for testing, automation, and offline evaluation."""
    prompt_lower = prompt.lower()

    # Scenario 1: Profile inquiry
    if "profile" in prompt_lower or "identity" in prompt_lower or "who am i" in prompt_lower:
        if "get_profile" in tool_map:
            prof = await _execute_tool_via_mcp(
                mcp_client, "get_profile", {}, session_id, steps, user_id
            )
            verified_id = prof.get("verified_id_number", "")
            return f"Your verified ID on file is {verified_id}.", steps

    # Scenario 2: Message host
    if "message" in prompt_lower or "tell the host" in prompt_lower or "contact host" in prompt_lower:
        if "message_host" in tool_map:
            recipient = None
            if "to " in prompt_lower:
                parts = prompt.split("to ")
                if len(parts) > 1:
                    recipient = parts[1].split()[0].strip()
            msg_res = await _execute_tool_via_mcp(
                mcp_client,
                "message_host",
                {"listing_id": "lst-goa-001", "body": prompt, "recipient": recipient},
                session_id,
                steps,
                user_id,
            )
            return f"I have sent the message to {msg_res.get('recipient')}.", steps

    # Scenario 3: search -> read_reviews -> (optionally) book
    city = "Goa"
    for c in ["Goa", "Manali", "Jaipur", "Pondicherry", "Munnar"]:
        if c.lower() in prompt_lower:
            city = c
            break

    search_res = await _execute_tool_via_mcp(
        mcp_client, "search_listings", {"city": city}, session_id, steps, user_id
    )

    target_listing_id = search_res[0]["id"] if search_res else "lst-goa-001"
    target_title = search_res[0]["title"] if search_res else "Stay"

    await _execute_tool_via_mcp(
        mcp_client, "read_reviews", {"listing_id": target_listing_id}, session_id, steps, user_id
    )

    if "book" in prompt_lower or "reserve" in prompt_lower:
        book_res = await _execute_tool_via_mcp(
            mcp_client,
            "book_listing",
            {
                "listing_id": target_listing_id,
                "checkin": "2026-11-20",
                "checkout": "2026-11-23",
                "guests": 2,
            },
            session_id,
            steps,
            user_id,
        )
        total = book_res.get("total_price", 0)
        ref = book_res.get("reference", "")
        return (
            f"Booked! {target_title} in {city} for 2 guests. "
            f"Reference: {ref}, total ₹{total:,}.",
            steps,
        )

    return f"I found stays in {city} including {target_title} and reviewed its guest ratings.", steps


async def _run_anthropic_loop(
    prompt: str,
    session_id: str,
    mcp_client: Client,
    tools: list,
    steps: list,
    user_id: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Anthropic Claude tool-calling loop capped at settings.CONCIERGE_MAX_STEPS."""
    anthropic_tools = [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": getattr(t, "input_schema", getattr(t, "inputSchema", {})),
        }
        for t in tools
    ]

    messages = [{"role": "user", "content": prompt}]
    max_steps = settings.CONCIERGE_MAX_STEPS

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        for _ in range(max_steps):
            response = await http_client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.LLM_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "tools": anthropic_tools,
                    "messages": messages,
                },
            )
            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.text}")
                return "I apologize, but I encountered an error connecting to my AI service.", steps

            data = response.json()
            content_blocks = data.get("content", [])
            tool_calls = [b for b in content_blocks if b.get("type") == "tool_use"]

            if not tool_calls:
                text_blocks = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                return " ".join(text_blocks).strip(), steps

            messages.append({"role": "assistant", "content": content_blocks})

            tool_results = []
            for tc in tool_calls:
                call_id = tc.get("id")
                name = tc.get("name")
                args = tc.get("input", {})

                result = await _execute_tool_via_mcp(
                    mcp_client, name, args, session_id, steps, user_id
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call_id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })

            messages.append({"role": "user", "content": tool_results})

    return "Reached maximum assistant steps.", steps


async def _run_openai_loop(
    prompt: str,
    session_id: str,
    mcp_client: Client,
    tools: list,
    steps: list,
    user_id: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """OpenAI tool-calling loop capped at settings.CONCIERGE_MAX_STEPS."""
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": getattr(t, "input_schema", getattr(t, "inputSchema", {})),
            },
        }
        for t in tools
    ]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    max_steps = settings.CONCIERGE_MAX_STEPS

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        for _ in range(max_steps):
            response = await http_client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "tools": openai_tools,
                },
            )
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.text}")
                return "I apologize, but I encountered an error connecting to my AI service.", steps

            choice = response.json()["choices"][0]
            msg = choice.get("message", {})
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                return msg.get("content", "").strip(), steps

            messages.append(msg)

            for tc in tool_calls:
                call_id = tc["id"]
                fn_name = tc["function"]["name"]
                args = json.loads(tc["function"].get("arguments", "{}"))

                result = await _execute_tool_via_mcp(
                    mcp_client, fn_name, args, session_id, steps, user_id
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })

    return "Reached maximum assistant steps.", steps


async def _run_gemini_loop(
    prompt: str,
    session_id: str,
    mcp_client: Client,
    tools: list,
    steps: list,
    user_id: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Google Gemini tool-calling loop capped at settings.CONCIERGE_MAX_STEPS.

    Uses the google-genai SDK with manual function calling (AFC disabled) so
    that tool execution goes exclusively through the MCP client.
    API key is read from settings.LLM_API_KEY — never hardcoded.
    """
    from google.genai import types as gtypes

    client = _get_gemini_client()

    # Build FunctionDeclarations from MCP tool schemas.
    # Sanitize schemas to remove keys Gemini doesn't support (e.g. additionalProperties).
    declarations = []
    for t in tools:
        raw_schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {}
        clean_schema = _sanitize_schema_for_gemini(raw_schema)
        declarations.append(
            gtypes.FunctionDeclaration(
                name=t.name,
                description=t.description or "",
                parameters=clean_schema,
            )
        )

    gemini_tools = [gtypes.Tool(function_declarations=declarations)]
    contents: list = [prompt]
    max_steps = settings.CONCIERGE_MAX_STEPS

    resolved_model = _resolve_gemini_model(settings.LLM_MODEL)

    for _ in range(max_steps):
        try:
            response = await client.aio.models.generate_content(
                model=resolved_model,
                contents=contents,
                config=gtypes.GenerateContentConfig(
                    tools=gemini_tools,
                    system_instruction=SYSTEM_PROMPT,
                    automatic_function_calling=gtypes.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
        except Exception as exc:
            # If primary model is unavailable (503 / 404), fall back to fast, lightweight model
            if resolved_model != "gemini-3.5-flash-lite" and any(code in str(exc) for code in ["503", "404", "UNAVAILABLE", "NOT_FOUND"]):
                logger.warning(f"Gemini model {resolved_model} error ({exc}); falling back to gemini-3.5-flash-lite")
                resolved_model = "gemini-3.5-flash-lite"
                response = await client.aio.models.generate_content(
                    model=resolved_model,
                    contents=contents,
                    config=gtypes.GenerateContentConfig(
                        tools=gemini_tools,
                        system_instruction=SYSTEM_PROMPT,
                        automatic_function_calling=gtypes.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )
            else:
                raise

        # No function calls → model produced final text
        if not response.function_calls:
            return response.text or "", steps

        # Append assistant turn for multi-turn context
        contents.append(response.candidates[0].content)

        # Execute each requested tool via MCP, then feed result back
        tool_parts = []
        for fc in response.function_calls:
            result = await _execute_tool_via_mcp(
                mcp_client, fc.name, dict(fc.args), session_id, steps, user_id
            )
            tool_parts.append(
                gtypes.Part.from_function_response(
                    name=fc.name,
                    response={"result": result},
                )
            )
        contents.append(gtypes.Content(role="user", parts=tool_parts))

    return "Reached maximum assistant steps.", steps
