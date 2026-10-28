from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User
from tripbuddy_core.schemas import MessageCreate, MessageOut
from tripbuddy_core.services import send_message_service, get_thread_messages_service
from tripbuddy_core.errors import ResourceNotFoundError, ValidationError, UnauthorizedError
from app.dependencies import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message to a host or arbitrary recipient. Recipient is not restricted."""
    try:
        return send_message_service(
            db=db,
            sender_id=current_user.id,
            body=msg_in.body,
            listing_id=msg_in.listing_id,
            booking_id=msg_in.booking_id,
            recipient=msg_in.recipient,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[MessageOut])
def get_messages(
    booking_id: Optional[str] = Query(None, description="Filter thread by booking ID"),
    recipient: Optional[str] = Query(None, description="Filter thread by recipient ID or email"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get message thread. Enforces participant ownership rule (only sender and recipient can read)."""
    try:
        return get_thread_messages_service(
            db=db,
            user=current_user,
            booking_id=booking_id,
            recipient=recipient,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/booking/{booking_id}", response_model=List[MessageOut])
def get_booking_messages(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages for a specific booking. Enforces ownership rule."""
    try:
        return get_thread_messages_service(
            db=db,
            user=current_user,
            booking_id=booking_id,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

