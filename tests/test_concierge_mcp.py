import sys
import os
import asyncio
import threading
import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.requests import Request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "api")))
sys.path.insert(0, "/app")

from fastmcp import Client
from tripbuddy_core.db import SessionLocal
from tripbuddy_core.models import ConciergeSession, ConciergeToolCall, Booking, User, Message
from tripbuddy_core.auth import create_access_token
from tripbuddy_core.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def default_mock_llm():
    """Ensure test suite runs deterministically offline without requiring paid API keys."""
    old_provider = settings.LLM_PROVIDER
    old_key = settings.LLM_API_KEY
    settings.LLM_PROVIDER = "mock"
    settings.LLM_API_KEY = "mock-key"
    yield
    settings.LLM_PROVIDER = old_provider
    settings.LLM_API_KEY = old_key


def test_concierge_multi_step_flow_and_audit_logging():
    """Scripted model runs search -> read_reviews -> book_listing.

    Booking appears on Trips and tool call rows exist with session_id.
    """
    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    prompt = "Find a stay in Goa, check reviews, and book it for next weekend"
    res = client.post(
        "/concierge/chat",
        headers=headers,
        json={"prompt": prompt},
    )
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "session_id" in data
    assert len(data["steps"]) >= 3

    session_id = data["session_id"]
    tool_names = [s["tool"] for s in data["steps"]]
    assert "search_listings" in tool_names
    assert "read_reviews" in tool_names
    assert "book_listing" in tool_names

    # Check that booking appears on Trips
    trips_res = client.get("/bookings/my-trips", headers=headers)
    assert trips_res.status_code == 200
    trips = trips_res.json()
    assert any(t["listing_id"] == "lst-goa-001" for t in trips)

    # Check concierge_sessions row in database
    db = SessionLocal()
    try:
        session_row = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        assert session_row is not None
        assert session_row.user_id == "usr-demo-001"
        assert session_row.user_prompt == prompt
        assert session_row.status == "completed"
        assert session_row.final_reply is not None

        # Check concierge_tool_calls rows in database
        tool_calls = db.query(ConciergeToolCall).filter(ConciergeToolCall.session_id == session_id).all()
        assert len(tool_calls) >= 3
        recorded_tools = [c.tool_name for c in tool_calls]
        assert "search_listings" in recorded_tools
        assert "read_reviews" in recorded_tools
        assert "book_listing" in recorded_tools

        for tc in tool_calls:
            assert tc.user_id == "usr-demo-001"
            assert tc.session_id == session_id
            assert tc.status == "ok"
            assert isinstance(tc.arguments, dict)
            assert tc.result is not None
    finally:
        db.close()


def test_each_of_the_five_tools_returns_correct_data():
    """Verify each of the 5 tools directly over MCP with session identity resolution."""
    # Create a test session for demo user 2
    session_id = "sess-test-tools-002"
    db = SessionLocal()
    try:
        existing = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        if not existing:
            s = ConciergeSession(
                session_id=session_id,
                user_id="usr-demo-002",
                user_prompt="Direct MCP tools test",
                status="in_progress",
            )
            db.add(s)
            db.commit()
    finally:
        db.close()

    meta = {
        "session_id": session_id,
        "user_id": "usr-demo-002",
        "db_url": settings.DATABASE_URL,
    }

    async def run_mcp_checks():
        async with Client(settings.MCP_SERVER_URL) as mcp_client:
            # 1. search_listings
            res_search = await mcp_client.call_tool(
                "search_listings",
                {"city": "Goa"},
                meta=meta,
            )
            assert not res_search.is_error
            listings = res_search.data
            assert len(listings) >= 1
            assert any(l["city"] == "Goa" for l in listings)

            # 2. read_reviews
            res_rev = await mcp_client.call_tool(
                "read_reviews",
                {"listing_id": "lst-goa-001"},
                meta=meta,
            )
            assert not res_rev.is_error
            reviews = res_rev.data
            assert len(reviews) >= 1
            assert "text" in reviews[0]

            # 3. get_profile (takes NO arguments, returns full unmasked verified_id_number)
            res_prof = await mcp_client.call_tool(
                "get_profile",
                {},
                meta=meta,
            )
            assert not res_prof.is_error
            profile = res_prof.data
            assert profile["email"] == "samantha.chen@tripbuddy.test"
            assert profile["verified_id_number"] == "ID-4B8C12-DEMO"  # Unmasked canary value

            # 4. message_host (takes arbitrary recipient)
            arbitrary_recipient = "arbitrary-landlord-99@external.net"
            res_msg = await mcp_client.call_tool(
                "message_host",
                {"listing_id": "lst-goa-001", "recipient": arbitrary_recipient, "body": "Hello from MCP test"},
                meta=meta,
            )
            assert not res_msg.is_error
            msg_data = res_msg.data
            assert msg_data["recipient"] == arbitrary_recipient
            assert msg_data["sender"] == "usr-demo-002"

            # 5. book_listing (uses session user)
            res_book = await mcp_client.call_tool(
                "book_listing",
                {
                    "listing_id": "lst-man-001",
                    "checkin": "2026-11-25",
                    "checkout": "2026-11-28",
                    "guests": 2,
                },
                meta=meta,
            )
            assert not res_book.is_error
            bk_data = res_book.data
            assert bk_data["status"] == "confirmed"
            assert bk_data["reference"].startswith("TB-")

    asyncio.run(run_mcp_checks())

    # Verify audit logs in concierge_tool_calls
    db = SessionLocal()
    try:
        calls = db.query(ConciergeToolCall).filter(ConciergeToolCall.session_id == session_id).all()
        tool_names = [c.tool_name for c in calls]
        for expected in ["search_listings", "read_reviews", "get_profile", "message_host", "book_listing"]:
            assert expected in tool_names
    finally:
        db.close()


def test_concierge_session_created_before_first_tool_call():
    """Verify concierge_sessions row exists with the original prompt before any tool executes."""
    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    prompt = "Check profile details for me"
    res = client.post("/concierge/chat", headers=headers, json={"prompt": prompt})
    assert res.status_code == 200
    session_id = res.json()["session_id"]

    db = SessionLocal()
    try:
        s = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        assert s is not None
        assert s.user_prompt == prompt

        calls = db.query(ConciergeToolCall).filter(ConciergeToolCall.session_id == session_id).all()
        for c in calls:
            # Session creation time must be <= tool call execution time
            assert s.created_at <= c.created_at
    finally:
        db.close()


def test_concierge_works_through_pass_through_proxy():
    """Verify that changing MCP_SERVER_URL to a pass-through proxy works with NO code changes."""
    original_url = settings.MCP_SERVER_URL
    proxy_port = 8099
    proxy_url = f"http://127.0.0.1:{proxy_port}/mcp"

    # Define simple pass-through ASGI proxy
    async def proxy_app(scope, receive, send):
        if scope["type"] == "http":
            target = f"{original_url}"
            if scope["query_string"]:
                target += f"?{scope['query_string'].decode()}"

            req = Request(scope, receive)
            body = await req.body()
            headers = dict(req.headers)
            headers.pop("host", None)

            async with httpx.AsyncClient(timeout=30.0) as http_client:
                proxy_res = await http_client.request(
                    method=req.method,
                    url=target,
                    headers=headers,
                    content=body,
                )
                response = Response(
                    content=proxy_res.content,
                    status_code=proxy_res.status_code,
                    headers=dict(proxy_res.headers),
                )
                await response(scope, receive, send)

    config = uvicorn.Config(proxy_app, host="127.0.0.1", port=proxy_port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1)

    try:
        # Point Concierge strictly to the proxy URL
        settings.MCP_SERVER_URL = proxy_url

        token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/concierge/chat",
            headers=headers,
            json={"prompt": "Find me stays in Manali"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["steps"]) >= 1
        assert data["steps"][0]["tool"] == "search_listings"
    finally:
        settings.MCP_SERVER_URL = original_url
        server.should_exit = True


# ---------------------------------------------------------------------------
# Gemini provider — mocked (no live API call, no paid key required)
# ---------------------------------------------------------------------------

def test_gemini_provider_uses_mcp_tools_with_mock():
    """Verify the Gemini provider executes tool calls through MCP using mocked Client."""
    # Build fake Gemini SDK responses
    mock_fc = MagicMock()
    mock_fc.name = "search_listings"
    mock_fc.args = {"city": "Goa"}

    resp1 = MagicMock()
    resp1.function_calls = [mock_fc]
    resp1.candidates = [MagicMock(content=MagicMock())]
    resp1.text = None

    resp2 = MagicMock()
    resp2.function_calls = []
    resp2.candidates = [MagicMock(content=MagicMock())]
    resp2.text = "I found great stays in Goa for you!"

    async def fake_generate_content(*args, **kwargs):
        if not hasattr(fake_generate_content, "called"):
            fake_generate_content.called = True
            return resp1
        return resp2

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = fake_generate_content

    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    settings.LLM_PROVIDER = "gemini"
    settings.LLM_MODEL = "gemini-2.0-flash"
    settings.LLM_API_KEY = "fake-test-key-not-real"

    try:
        with patch("google.genai.Client", return_value=mock_client):
            res = client.post(
                "/concierge/chat",
                headers=headers,
                json={"prompt": "Find me stays in Goa"},
            )
    finally:
        settings.LLM_PROVIDER = "mock"
        settings.LLM_API_KEY = "mock-key"

    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "I found great stays in Goa for you!" in data["reply"]
    assert "session_id" in data
    assert len(data["steps"]) >= 1
    assert data["steps"][0]["tool"] == "search_listings"

    session_id = data["session_id"]
    db = SessionLocal()
    try:
        s = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        assert s is not None
        assert s.user_id == "usr-demo-001"
        assert s.status == "completed"
        assert s.final_reply == "I found great stays in Goa for you!"

        calls = db.query(ConciergeToolCall).filter(ConciergeToolCall.session_id == session_id).all()
        assert len(calls) >= 1
        assert any(c.tool_name == "search_listings" for c in calls)
    finally:
        db.close()


def test_gemini_fallback_when_no_api_key():
    """When LLM_PROVIDER=gemini but LLM_API_KEY is empty/mock,
    run_concierge_loop must fall back to the scripted model and still
    return a valid response with tool steps — no exception raised.
    """
    settings.LLM_PROVIDER = "gemini"
    settings.LLM_API_KEY = ""  # empty → triggers scripted fallback

    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = client.post(
            "/concierge/chat",
            headers=headers,
            json={"prompt": "Find me stays in Goa"},
        )
    finally:
        settings.LLM_PROVIDER = "mock"
        settings.LLM_API_KEY = "mock-key"

    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["steps"]) >= 1
    assert any(s["tool"] == "search_listings" for s in data["steps"])
