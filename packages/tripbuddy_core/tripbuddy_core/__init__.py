"""TripBuddy Core package - shared across FastAPI backend and FastMCP server."""

from tripbuddy_core.models import (
    User,
    Listing,
    Review,
    Booking,
    Message,
    ConciergeSession,
    ConciergeToolCall,
)

from tripbuddy_core.services import (
    get_listings_service,
    get_listing_detail_service,
)
from tripbuddy_core.schemas import (
    ListingCard,
    ListingDetail,
    PaginatedListings,
    HostSummary,
    ReviewOut,
)

__version__ = "0.1.0"

__all__ = [
    "User",
    "Listing",
    "Review",
    "Booking",
    "Message",
    "ConciergeSession",
    "ConciergeToolCall",
    "get_listings_service",
    "get_listing_detail_service",
    "ListingCard",
    "ListingDetail",
    "PaginatedListings",
    "HostSummary",
    "ReviewOut",
]

