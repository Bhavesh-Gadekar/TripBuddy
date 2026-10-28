from typing import List, Optional, Any
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User, ConciergeSession
from app.dependencies import get_current_user
from app.concierge import run_concierge_loop

router = APIRouter(prefix="/concierge", tags=["concierge"])


class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


class ChatStep(BaseModel):
    tool: str
    arguments: dict
    result: Any


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    steps: List[ChatStep]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_concierge(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Authenticated chat endpoint for AI Concierge.

    Writes concierge_sessions row BEFORE calling model tools via MCP client.
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty",
        )

    session_id = req.session_id or f"sess-{uuid.uuid4().hex[:12]}"

    # Persist session with original user request BEFORE model runs
    existing = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
    if not existing:
        session_row = ConciergeSession(
            session_id=session_id,
            user_id=current_user.id,
            user_prompt=req.prompt,
            created_at=datetime.datetime.utcnow(),
            status="in_progress",
        )
        db.add(session_row)
        db.commit()

    try:
        reply, steps = await run_concierge_loop(
            prompt=req.prompt,
            session_id=session_id,
            user_id=current_user.id,
        )

        # Update session with final reply
        session_to_update = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        if session_to_update:
            session_to_update.final_reply = reply
            session_to_update.status = "completed"
            db.commit()

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            steps=[
                ChatStep(
                    tool=s["tool"],
                    arguments=s["arguments"],
                    result=s["result"],
                )
                for s in steps
            ],
        )
    except Exception as e:
        session_to_update = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        if session_to_update:
            session_to_update.status = "failed"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Concierge execution error: {str(e)}",
        )
