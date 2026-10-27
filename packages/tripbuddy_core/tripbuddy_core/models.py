import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from tripbuddy_core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    verified_id_number = Column(String(100), nullable=False)
    # Host attributes if user acts as a host
    is_host = Column(Boolean, default=False, nullable=False)
    avatar = Column(String(500), nullable=True)
    superhost = Column(Boolean, default=False, nullable=False)
    joined_date = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    listings = relationship("Listing", back_populates="host")
    bookings = relationship("Booking", back_populates="user")
    concierge_sessions = relationship("ConciergeSession", back_populates="user")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(String, primary_key=True)
    host_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "Beachfront", "Villa", "Cottage", "Apartment"
    price_per_night = Column(Integer, nullable=False)
    max_guests = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    amenities = Column(JSONB, nullable=False, default=list)  # List of strings e.g. ["Wifi", "Pool"]
    images = Column(JSONB, nullable=False, default=list)  # List of image URLs
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    host = relationship("User", back_populates="listings")
    reviews = relationship("Review", back_populates="listing", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="listing")

    __table_args__ = (
        Index("idx_listings_city_price", "city", "price_per_night"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True)
    listing_id = Column(String, ForeignKey("listings.id", ondelete="RESTRICT"), nullable=False)
    author_name = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)  # raw text, never filtered or sanitized in db
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    listing = relationship("Listing", back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        Index("idx_reviews_listing_id", "listing_id"),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True)
    reference = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    listing_id = Column(String, ForeignKey("listings.id", ondelete="RESTRICT"), nullable=False)
    checkin = Column(String(10), nullable=False)  # ISO Date YYYY-MM-DD
    checkout = Column(String(10), nullable=False)  # ISO Date YYYY-MM-DD
    guests = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="bookings")
    listing = relationship("Listing", back_populates="bookings")
    messages = relationship("Message", back_populates="booking")

    __table_args__ = (
        Index("idx_bookings_listing_dates", "listing_id", "checkin", "checkout"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=True, index=True)
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)  # Free text, arbitrary recipient string
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    booking = relationship("Booking", back_populates="messages")


class ConciergeSession(Base):
    __tablename__ = "concierge_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    final_reply = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="in_progress")  # in_progress, completed, failed

    user = relationship("User", back_populates="concierge_sessions")
    tool_calls = relationship("ConciergeToolCall", back_populates="session")


class ConciergeToolCall(Base):
    __tablename__ = "concierge_tool_calls"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("concierge_sessions.session_id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(String, nullable=False)  # Recorded user ID
    tool_name = Column(String(100), nullable=False)
    arguments = Column(JSONB, nullable=False)
    result = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default="ok")  # ok, error
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    session = relationship("ConciergeSession", back_populates="tool_calls")

    __table_args__ = (
        Index("idx_concierge_tool_calls_session", "session_id"),
    )
