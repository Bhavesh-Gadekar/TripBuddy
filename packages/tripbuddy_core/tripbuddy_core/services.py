import datetime
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, not_, exists
from tripbuddy_core.models import Listing, Review, User, Booking
from tripbuddy_core.errors import (
    ResourceNotFoundError,
    DatesUnavailableError,
    InvalidGuestsError,
    InvalidDatesError,
    UnauthorizedError,
)
from tripbuddy_core.schemas import (
    ListingCard,
    ListingDetail,
    HostSummary,
    ReviewOut,
    PaginatedListings,
    UserProfilePublic,
    UserProfileFull,
    PriceBreakdown,
    BookingOut,
)


def get_listings_service(
    db: Session,
    city: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    property_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    amenities: Optional[List[str]] = None,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    guests: Optional[int] = None,
    sort_by: Optional[str] = "newest",  # price_asc, price_desc, rating, newest
    page: int = 1,
    limit: int = 12,
) -> PaginatedListings:
    """Shared query for browsing listings with combined AND filters, sorting, and pagination."""
    query = db.query(Listing)

    if city:
        query = query.filter(Listing.city.ilike(f"%{city.strip()}%"))

    if min_price is not None:
        query = query.filter(Listing.price_per_night >= min_price)

    if max_price is not None:
        query = query.filter(Listing.price_per_night <= max_price)

    if property_type:
        query = query.filter(Listing.type.ilike(property_type.strip()))

    if guests is not None:
        query = query.filter(Listing.max_guests >= guests)

    if amenities:
        for amen in amenities:
            amen_clean = amen.strip()
            if amen_clean:
                # Amenities is stored as JSONB array of strings
                query = query.filter(Listing.amenities.contains([amen_clean]))

    # Date availability filter: exclude listings with overlapping confirmed bookings
    if checkin and checkout:
        # Overlap rule: booking.checkin < req_checkout AND booking.checkout > req_checkin
        overlap_stmt = exists().where(
            Booking.listing_id == Listing.id,
            Booking.status == "confirmed",
            Booking.checkin < checkout,
            Booking.checkout > checkin,
        )
        query = query.filter(not_(overlap_stmt))

    # Min rating filter requires calculating average review rating
    if min_rating is not None:
        subquery = (
            db.query(Review.listing_id, func.avg(Review.rating).label("avg_rating"))
            .group_by(Review.listing_id)
            .subquery()
        )
        query = query.outerjoin(subquery, Listing.id == subquery.c.listing_id).filter(
            func.coalesce(subquery.c.avg_rating, 0.0) >= min_rating
        )

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(Listing.price_per_night))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Listing.price_per_night))
    elif sort_by == "rating":
        rating_subquery = (
            db.query(Review.listing_id, func.avg(Review.rating).label("avg_rating"))
            .group_by(Review.listing_id)
            .subquery()
        )
        query = query.outerjoin(rating_subquery, Listing.id == rating_subquery.c.listing_id).order_by(
            desc(func.coalesce(rating_subquery.c.avg_rating, 0.0)), desc(Listing.created_at)
        )
    else:  # newest default
        query = query.order_by(desc(Listing.created_at))

    total = query.count()
    offset = (max(1, page) - 1) * limit
    listings = query.offset(offset).limit(limit).all()

    # Build response cards
    items = []
    for l in listings:
        reviews = db.query(Review.rating).filter(Review.listing_id == l.id).all()
        ratings = [r[0] for r in reviews]
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0

        items.append(
            ListingCard(
                id=l.id,
                title=l.title,
                city=l.city,
                type=l.type,
                price_per_night=l.price_per_night,
                max_guests=l.max_guests,
                images=l.images or [],
                rating=avg_rating,
                review_count=len(ratings),
            )
        )

    pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedListings(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


def get_listing_detail_service(db: Session, listing_id: str) -> ListingDetail:
    """Shared query for single listing detail with host info and full raw review list."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise ResourceNotFoundError(f"Listing with id '{listing_id}' not found")

    host = db.query(User).filter(User.id == listing.host_id).first()
    reviews = (
        db.query(Review)
        .filter(Review.listing_id == listing_id)
        .order_by(desc(Review.created_at))
        .all()
    )

    ratings = [r.rating for r in reviews]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0

    return ListingDetail(
        id=listing.id,
        title=listing.title,
        city=listing.city,
        type=listing.type,
        price_per_night=listing.price_per_night,
        max_guests=listing.max_guests,
        description=listing.description,
        amenities=listing.amenities or [],
        images=listing.images or [],
        rating=avg_rating,
        review_count=len(reviews),
        host=HostSummary(
            id=host.id if host else "unknown",
            name=host.name if host else "Host",
            avatar=host.avatar if host else None,
            superhost=host.superhost if host else False,
            joined_date=host.joined_date if host else None,
        ),
        reviews=[
            ReviewOut(
                id=r.id,
                listing_id=r.listing_id,
                author_name=r.author_name,
                rating=r.rating,
                text=r.text,  # Stored text returned raw without filtering
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in reviews
        ],
    )


def mask_verified_id(id_number: str) -> str:
    """Mask verified ID number showing only last 4 characters, e.g. ***-DEMO."""
    if not id_number or len(id_number) <= 4:
        return "****"
    return f"***{id_number[-4:]}"


def get_user_profile_full(db: Session, user_id: str) -> UserProfileFull:
    """Service function to retrieve full unmasked user profile for tools/backend."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundError(f"User '{user_id}' not found")

    return UserProfileFull(
        id=user.id,
        name=user.name,
        email=user.email,
        verified_id_number=user.verified_id_number,  # Raw full fictional value
        is_host=user.is_host,
        avatar=user.avatar,
        superhost=user.superhost,
        joined_date=user.joined_date,
    )


def get_user_profile_masked(db: Session, user_id: str) -> UserProfilePublic:
    """Service function to retrieve profile for website UI with masked ID."""
    full_profile = get_user_profile_full(db, user_id)
    return UserProfilePublic(
        id=full_profile.id,
        name=full_profile.name,
        email=full_profile.email,
        masked_verified_id_number=mask_verified_id(full_profile.verified_id_number),
        is_host=full_profile.is_host,
        avatar=full_profile.avatar,
        superhost=full_profile.superhost,
        joined_date=full_profile.joined_date,
    )


# --- Booking Flow Service Logic ---

FIXED_SERVICE_FEE = 450


def calculate_pricing(price_per_night: int, checkin_str: str, checkout_str: str) -> PriceBreakdown:
    """Single pricing function used by every caller (REST, MCP, Frontend)."""
    try:
        d1 = datetime.date.fromisoformat(checkin_str)
        d2 = datetime.date.fromisoformat(checkout_str)
    except ValueError:
        raise InvalidDatesError("Invalid date format. Expected YYYY-MM-DD")

    nights = (d2 - d1).days
    if nights <= 0:
        raise InvalidDatesError("Check-out date must be after check-in date")

    subtotal = price_per_night * nights
    service_fee = FIXED_SERVICE_FEE
    total = subtotal + service_fee

    return PriceBreakdown(
        nights=nights,
        price_per_night=price_per_night,
        subtotal=subtotal,
        service_fee=service_fee,
        total=total,
    )


def validate_booking_request(listing: Listing, checkin_str: str, checkout_str: str, guests: int):
    """Validate check-in, check-out, and guest count."""
    try:
        d1 = datetime.date.fromisoformat(checkin_str)
        d2 = datetime.date.fromisoformat(checkout_str)
    except ValueError:
        raise InvalidDatesError("Dates must be valid YYYY-MM-DD strings")

    today = datetime.date.today()
    if d1 < today:
        raise InvalidDatesError("Check-in date cannot be in the past")
    if d2 <= d1:
        raise InvalidDatesError("Check-out date must be after check-in date")

    if guests < 1 or guests > listing.max_guests:
        raise InvalidGuestsError(
            f"Guests count must be between 1 and the maximum allowed ({listing.max_guests})"
        )


def create_booking_service(
    db: Session,
    user_id: str,
    listing_id: str,
    checkin: str,
    checkout: str,
    guests: int,
) -> BookingOut:
    """Create a confirmed booking inside a transaction with row locking to prevent double booking."""
    # 1. Lock the listing row with FOR UPDATE so concurrent booking requests wait
    listing = (
        db.query(Listing)
        .filter(Listing.id == listing_id)
        .with_for_update()
        .first()
    )
    if not listing:
        raise ResourceNotFoundError(f"Listing '{listing_id}' not found")

    # 2. Validate dates & guests
    validate_booking_request(listing, checkin, checkout, guests)

    # 3. Check for overlapping confirmed bookings
    # Overlap rule: existing.checkin < req_checkout AND existing.checkout > req_checkin
    overlap = (
        db.query(Booking)
        .filter(
            Booking.listing_id == listing_id,
            Booking.status == "confirmed",
            Booking.checkin < checkout,
            Booking.checkout > checkin,
        )
        .first()
    )
    if overlap:
        raise DatesUnavailableError(
            f"The listing is already booked for overlapping dates ({overlap.checkin} to {overlap.checkout})"
        )

    # 4. Compute pricing
    pricing = calculate_pricing(listing.price_per_night, checkin, checkout)

    # 5. Create booking row (mock payment immediately moves status to confirmed)
    booking_id = f"bk-{uuid.uuid4().hex[:8]}"
    ref_code = f"TB-{uuid.uuid4().hex[:6].upper()}"

    booking = Booking(
        id=booking_id,
        reference=ref_code,
        user_id=user_id,
        listing_id=listing_id,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
        total_price=pricing.total,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return BookingOut(
        id=booking.id,
        reference=booking.reference,
        user_id=booking.user_id,
        listing_id=booking.listing_id,
        checkin=booking.checkin,
        checkout=booking.checkout,
        guests=booking.guests,
        total_price=booking.total_price,
        status=booking.status,
        created_at=booking.created_at.isoformat() if booking.created_at else "",
        listing_title=listing.title,
        listing_city=listing.city,
        listing_image=listing.images[0] if listing.images else None,
    )


def cancel_booking_service(db: Session, user_id: str, booking_id: str) -> BookingOut:
    """Cancel a booking before check-in, freeing up the dates."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise ResourceNotFoundError(f"Booking '{booking_id}' not found")

    if booking.user_id != user_id:
        raise UnauthorizedError("Cannot cancel another user's booking")

    # Validate not already past check-in
    try:
        checkin_date = datetime.date.fromisoformat(booking.checkin)
        if checkin_date < datetime.date.today():
            raise InvalidDatesError("Cannot cancel past or ongoing bookings")
    except ValueError:
        pass

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)

    listing = db.query(Listing).filter(Listing.id == booking.listing_id).first()

    return BookingOut(
        id=booking.id,
        reference=booking.reference,
        user_id=booking.user_id,
        listing_id=booking.listing_id,
        checkin=booking.checkin,
        checkout=booking.checkout,
        guests=booking.guests,
        total_price=booking.total_price,
        status=booking.status,
        created_at=booking.created_at.isoformat() if booking.created_at else "",
        listing_title=listing.title if listing else None,
        listing_city=listing.city if listing else None,
        listing_image=listing.images[0] if listing and listing.images else None,
    )


def get_user_trips_service(db: Session, user_id: str) -> List[BookingOut]:
    """Retrieve all bookings for a user ordered by check-in date."""
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user_id)
        .order_by(desc(Booking.created_at))
        .all()
    )
    results = []
    for b in bookings:
        listing = db.query(Listing).filter(Listing.id == b.listing_id).first()
        results.append(
            BookingOut(
                id=b.id,
                reference=b.reference,
                user_id=b.user_id,
                listing_id=b.listing_id,
                checkin=b.checkin,
                checkout=b.checkout,
                guests=b.guests,
                total_price=b.total_price,
                status=b.status,
                created_at=b.created_at.isoformat() if b.created_at else "",
                listing_title=listing.title if listing else None,
                listing_city=listing.city if listing else None,
                listing_image=listing.images[0] if listing and listing.images else None,
            )
        )
    return results


