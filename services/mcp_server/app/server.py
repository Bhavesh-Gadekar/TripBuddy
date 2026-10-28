from typing import Optional, List, Any
import datetime
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP, Context
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tripbuddy_core import __version__ as core_version
from tripbuddy_core.config import settings
from tripbuddy_core.db import SessionLocal
from tripbuddy_core.models import ConciergeSession, ConciergeToolCall, User, Review
from tripbuddy_core.services import (
    get_listings_service,
    get_listing_detail_service,
    get_user_profile_full,
    send_message_service,
    create_booking_service,
)

mcp = FastMCP("TripBuddy MCP Server")

_engines: dict = {}


def get_db_for_context(ctx: Optional[Context] = None) -> Session:
    """Return a DB session, honoring db_url in ctx.request_context.meta if passed.

    Allows test suites running with local PostgreSQL to have MCP server operate
    on the exact same database.
    """
    if ctx and ctx.request_context and ctx.request_context.meta:
        db_url = ctx.request_context.meta.get("db_url")
        if db_url:
            if db_url not in _engines:
                _engines[db_url] = sessionmaker(
                    autocommit=False, autoflush=False, bind=create_engine(db_url, pool_pre_ping=True)
                )
            return _engines[db_url]()
    return SessionLocal()


def redact_sensitive(obj: Any) -> Any:
    """Redact only passwords, JWTs and API keys per Prompt 7."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if any(s in k.lower() for s in ["password", "jwt", "api_key", "secret", "token"]):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_sensitive(v)
        return cleaned
    elif isinstance(obj, list):
        return [redact_sensitive(item) for item in obj]
    return obj


def get_session_info(ctx: Context) -> tuple[Optional[str], Optional[str]]:
    """Extract session_id and user_id from context/concierge_sessions.

    user_id lookup order:
      1. Directly from meta["user_id"] (passed by the Concierge API layer)
      2. Looked up from concierge_sessions table by session_id
    """
    session_id = None
    meta_user_id = None

    if ctx and ctx.request_context and ctx.request_context.meta:
        meta = ctx.request_context.meta
        session_id = meta.get("session_id") or meta.get("sessionId")
        meta_user_id = meta.get("user_id")

    if not session_id and ctx and hasattr(ctx.request_context, "request") and ctx.request_context.request:
        headers = getattr(ctx.request_context.request, "headers", {})
        for h in ["x-session-id", "session-id", "session_id"]:
            if h in headers:
                session_id = headers[h]
                break

    # If user_id was provided directly in meta, use it immediately
    if meta_user_id:
        return session_id, meta_user_id

    # Otherwise try the DB lookup
    user_id = None
    if session_id:
        db = get_db_for_context(ctx)
        try:
            s = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
            if s:
                user_id = s.user_id
        finally:
            db.close()
    return session_id, user_id


def log_call(
    ctx: Optional[Context],
    session_id: Optional[str],
    user_id: Optional[str],
    tool_name: str,
    arguments: dict,
    result: Any,
    status: str,
):
    """Append-only audit log to concierge_tool_calls."""
    if not session_id:
        return
    db = get_db_for_context(ctx)
    try:
        call_id = f"call-{uuid.uuid4().hex[:12]}"
        call = ConciergeToolCall(
            id=call_id,
            session_id=session_id,
            user_id=user_id or "unknown",
            tool_name=tool_name,
            arguments=redact_sensitive(arguments),
            result=redact_sensitive(result),
            status=status,
            created_at=datetime.datetime.utcnow(),
        )
        db.add(call)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@mcp.tool()
def search_listings(
    ctx: Context,
    city: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    property_type: Optional[str] = None,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    guests: Optional[int] = None,
) -> list[dict]:
    """Find stays by city, price range, dates, and property type."""
    session_id, user_id = get_session_info(ctx)
    args = {
        "city": city,
        "min_price": min_price,
        "max_price": max_price,
        "property_type": property_type,
        "checkin": checkin,
        "checkout": checkout,
        "guests": guests,
    }
    db = get_db_for_context(ctx)
    try:
        res = get_listings_service(
            db=db,
            city=city,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type,
            checkin=checkin,
            checkout=checkout,
            guests=guests,
        )
        results = [
            {
                "id": item.id,
                "title": item.title,
                "city": item.city,
                "type": item.type,
                "price_per_night": item.price_per_night,
                "max_guests": item.max_guests,
                "rating": item.rating,
                "review_count": item.review_count,
            }
            for item in res.items
        ]
        log_call(ctx, session_id, user_id, "search_listings", args, results, "ok")
        return results
    except Exception as e:
        log_call(ctx, session_id, user_id, "search_listings", args, {"error": str(e)}, "error")
        raise
    finally:
        db.close()


@mcp.tool()
def read_reviews(ctx: Context, listing_id: str) -> list[dict]:
    """Retrieve written reviews for a given listing. Returns raw review text."""
    session_id, user_id = get_session_info(ctx)
    args = {"listing_id": listing_id}
    db = get_db_for_context(ctx)
    try:
        reviews = (
            db.query(Review)
            .filter(Review.listing_id == listing_id)
            .order_by(Review.created_at.desc())
            .all()
        )
        results = [
            {
                "id": r.id,
                "listing_id": r.listing_id,
                "author_name": r.author_name,
                "rating": r.rating,
                "text": r.text,  # Stored text returned raw without filtering
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in reviews
        ]
        log_call(ctx, session_id, user_id, "read_reviews", args, results, "ok")
        return results
    except Exception as e:
        log_call(ctx, session_id, user_id, "read_reviews", args, {"error": str(e)}, "error")
        raise
    finally:
        db.close()


@mcp.tool()
def get_profile(ctx: Context) -> dict:
    """Retrieve the current user's saved profile details. Returns unmasked verified identity number."""
    session_id, user_id = get_session_info(ctx)
    args = {}
    if not user_id:
        err = {"error": "Unauthorized: No valid session or user found"}
        log_call(ctx, session_id, None, "get_profile", args, err, "error")
        raise ValueError("Unauthorized: No valid session or user found")
    db = get_db_for_context(ctx)
    try:
        profile = get_user_profile_full(db, user_id)
        res = {
            "id": profile.id,
            "name": profile.name,
            "email": profile.email,
            "verified_id_number": profile.verified_id_number,  # Full fictional canary value
            "is_host": profile.is_host,
        }
        log_call(ctx, session_id, user_id, "get_profile", args, res, "ok")
        return res
    except Exception as e:
        log_call(ctx, session_id, user_id, "get_profile", args, {"error": str(e)}, "error")
        raise
    finally:
        db.close()


@mcp.tool()
def message_host(
    ctx: Context,
    body: str,
    listing_id: Optional[str] = None,
    recipient: Optional[str] = None,
) -> dict:
    """Send a message on the user's behalf. Recipient defaults to listing host if omitted."""
    session_id, user_id = get_session_info(ctx)
    args = {"listing_id": listing_id, "recipient": recipient, "body": body}
    if not user_id:
        err = {"error": "Unauthorized: No valid session or user found"}
        log_call(ctx, session_id, None, "message_host", args, err, "error")
        raise ValueError("Unauthorized: No valid session or user found")
    db = get_db_for_context(ctx)
    try:
        msg = send_message_service(
            db=db,
            sender_id=user_id,
            body=body,
            listing_id=listing_id,
            recipient=recipient,
        )
        res = {
            "id": msg.id,
            "sender": msg.sender,
            "recipient": msg.recipient,
            "body": msg.body,
            "status": "sent",
            "created_at": msg.created_at,
        }
        log_call(ctx, session_id, user_id, "message_host", args, res, "ok")
        return res
    except Exception as e:
        log_call(ctx, session_id, user_id, "message_host", args, {"error": str(e)}, "error")
        raise
    finally:
        db.close()


@mcp.tool()
def book_listing(
    ctx: Context,
    listing_id: str,
    checkin: str,
    checkout: str,
    guests: int,
) -> dict:
    """Book a stay for specified dates and guest count using standard booking and availability rules."""
    session_id, user_id = get_session_info(ctx)
    args = {
        "listing_id": listing_id,
        "checkin": checkin,
        "checkout": checkout,
        "guests": guests,
    }
    if not user_id:
        err = {"error": "Unauthorized: No valid session or user found"}
        log_call(ctx, session_id, None, "book_listing", args, err, "error")
        raise ValueError("Unauthorized: No valid session or user found")
    db = get_db_for_context(ctx)
    try:
        booking = create_booking_service(
            db=db,
            user_id=user_id,
            listing_id=listing_id,
            checkin=checkin,
            checkout=checkout,
            guests=guests,
        )
        res = {
            "id": booking.id,
            "reference": booking.reference,
            "listing_id": booking.listing_id,
            "checkin": booking.checkin,
            "checkout": booking.checkout,
            "guests": booking.guests,
            "total_price": booking.total_price,
            "status": booking.status,
        }
        log_call(ctx, session_id, user_id, "book_listing", args, res, "ok")
        return res
    except Exception as e:
        log_call(ctx, session_id, user_id, "book_listing", args, {"error": str(e)}, "error")
        raise
    finally:
        db.close()


mcp_app = mcp.http_app()
app = FastAPI(title="TripBuddy MCP Service", version="0.1.0", lifespan=mcp_app.lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "mcp_server",
        "core_version": core_version,
        "database_configured": bool(settings.DATABASE_URL),
    }


app.mount("", mcp_app)
