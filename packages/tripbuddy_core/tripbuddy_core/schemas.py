from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class HostSummary(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None
    superhost: bool
    joined_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewOut(BaseModel):
    id: str
    listing_id: str
    author_name: str
    rating: int
    text: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ListingCard(BaseModel):
    id: str
    title: str
    city: str
    type: str
    price_per_night: int
    max_guests: int
    images: List[str]
    rating: float
    review_count: int

    model_config = ConfigDict(from_attributes=True)


class ListingDetail(BaseModel):
    id: str
    title: str
    city: str
    type: str
    price_per_night: int
    max_guests: int
    description: str
    amenities: List[str]
    images: List[str]
    rating: float
    review_count: int
    host: HostSummary
    reviews: List[ReviewOut]

    model_config = ConfigDict(from_attributes=True)


class PaginatedListings(BaseModel):
    items: List[ListingCard]
    total: int
    page: int
    limit: int
    pages: int

