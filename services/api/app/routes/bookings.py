from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User
from tripbuddy_core.schemas import BookingCreate, BookingOut, PriceBreakdown
from tripbuddy_core.services import (
    create_booking_service,
    cancel_booking_service,
    get_user_trips_service,
    calculate_pricing,
)
from tripbuddy_core.errors import (
    DatesUnavailableError,
    InvalidGuestsError,
    InvalidDatesError,
    ResourceNotFoundError,
    UnauthorizedError,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new booking. Business logic lives entirely in create_booking_service."""
    try:
        return create_booking_service(
            db=db,
            user_id=current_user.id,
            listing_id=data.listing_id,
            checkin=data.checkin,
            checkout=data.checkout,
            guests=data.guests,
        )
    except DatesUnavailableError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (InvalidGuestsError, InvalidDatesError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a booking before check-in date."""
    try:
        return cancel_booking_service(db=db, user_id=current_user.id, booking_id=booking_id)
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidDatesError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-trips", response_model=List[BookingOut])
def get_my_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all trips for the authenticated user."""
    return get_user_trips_service(db=db, user_id=current_user.id)

