from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User, Booking, Message
from tripbuddy_core.schemas import UserProfilePublic
from tripbuddy_core.services import get_user_profile_masked
from app.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserProfilePublic)
def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enforce ownership: A user can only view their own user profile (returns 403 otherwise)."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only view your own user profile",
        )
    return get_user_profile_masked(db, user_id)


@router.get("/{user_id}/bookings")
def get_user_bookings(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enforce ownership: A user can only access their own bookings."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view another user's bookings",
        )
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return bookings


@router.get("/{user_id}/messages")
def get_user_messages(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enforce ownership: A user can only access messages where they are sender or recipient."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view another user's messages",
        )
    messages = (
        db.query(Message)
        .filter((Message.sender == user_id) | (Message.recipient == current_user.email) | (Message.recipient == user_id))
        .all()
    )
    return messages

