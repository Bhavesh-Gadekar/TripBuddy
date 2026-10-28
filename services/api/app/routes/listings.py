from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User
from tripbuddy_core.services import (
    get_listings_service,
    get_listing_detail_service,
    create_review_service,
)
from tripbuddy_core.schemas import PaginatedListings, ListingDetail, ReviewCreate, ReviewOut
from tripbuddy_core.errors import ResourceNotFoundError, ValidationError
from app.dependencies import get_current_user

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=PaginatedListings)
def list_listings(
    city: Optional[str] = Query(None, description="City destination filter"),
    min_price: Optional[int] = Query(None, description="Minimum price per night (INR)"),
    max_price: Optional[int] = Query(None, description="Maximum price per night (INR)"),
    type: Optional[str] = Query(None, description="Property type filter"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating"),
    amenities: Optional[List[str]] = Query(None, description="Required amenities list"),
    checkin: Optional[str] = Query(None, description="Check-in date (YYYY-MM-DD)"),
    checkout: Optional[str] = Query(None, description="Check-out date (YYYY-MM-DD)"),
    guests: Optional[int] = Query(None, description="Number of guests"),
    sort: Optional[str] = Query("newest", description="Sorting criteria: price_asc, price_desc, rating, newest"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieve listings with combined filters, sorting, and pagination."""
    return get_listings_service(
        db=db,
        city=city,
        min_price=min_price,
        max_price=max_price,
        property_type=type,
        min_rating=min_rating,
        amenities=amenities,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
        sort_by=sort,
        page=page,
        limit=limit,
    )


@router.get("/{listing_id}", response_model=ListingDetail)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Retrieve full details of a specific listing including host and reviews."""
    try:
        return get_listing_detail_service(db=db, listing_id=listing_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{listing_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def submit_review(
    listing_id: str,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a review for any listing. Any logged-in user may review without a completed booking."""
    try:
        return create_review_service(
            db=db,
            user=current_user,
            listing_id=listing_id,
            rating=review_in.rating,
            text=review_in.text,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

