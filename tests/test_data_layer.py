import sys
import os
import pytest
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, "/app/scripts")

from tripbuddy_core.db import SessionLocal
from tripbuddy_core.models import (
    User,
    Listing,
    Review,
    Booking,
    Message,
    ConciergeSession,
    ConciergeToolCall,
)
from seed import seed_database, compute_database_hash


def test_reseed_is_deterministic_and_idempotent():
    """Verify that running reseed twice produces identical row counts and content hash."""
    seed_database()
    hash_1, counts_1 = compute_database_hash()

    seed_database()
    hash_2, counts_2 = compute_database_hash()

    assert counts_1 == counts_2
    assert hash_1 == hash_2
    # Verify expected counts
    u_count, l_count, r_count, b_count = counts_1
    assert u_count == 12  # 3 demo users + 9 hosts
    assert l_count >= 20  # 22 seeded listings
    assert r_count >= 60  # At least 3 reviews per listing
    assert b_count >= 1


def test_duplicate_email_rejected():
    """Constraint test: inserting a user with duplicate email raises IntegrityError."""
    db = SessionLocal()
    try:
        dup_user = User(
            id="usr-dup-test",
            name="Duplicate Test",
            email="alex.mercer@tripbuddy.test",  # existing demo email
            password_hash="mock_hash",
            verified_id_number="ID-DUP-TEST",
        )
        db.add(dup_user)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_rating_outside_1_to_5_rejected():
    """Constraint test: review rating < 1 or > 5 raises IntegrityError."""
    db = SessionLocal()
    try:
        bad_review_low = Review(
            id="rev-bad-0",
            listing_id="lst-goa-001",
            author_name="Bad Reviewer",
            rating=0,
            text="Invalid zero rating",
        )
        db.add(bad_review_low)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()

    try:
        bad_review_high = Review(
            id="rev-bad-6",
            listing_id="lst-goa-001",
            author_name="Bad Reviewer",
            rating=6,
            text="Invalid high rating",
        )
        db.add(bad_review_high)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_booking_with_missing_listing_rejected():
    """Constraint test: foreign key constraint on listing_id prevents orphaned bookings."""
    db = SessionLocal()
    try:
        orphaned_booking = Booking(
            id="bk-invalid-listing",
            reference="TB-INVALID-001",
            user_id="usr-demo-001",
            listing_id="lst-non-existent-999",
            checkin="2026-11-01",
            checkout="2026-11-05",
            guests=2,
            total_price=5000,
            status="confirmed",
        )
        db.add(orphaned_booking)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_message_with_non_user_recipient_is_accepted():
    """Check that messages accept free-text arbitrary non-platform recipients."""
    db = SessionLocal()
    try:
        msg = Message(
            id="msg-test-external-01",
            booking_id=None,
            sender="usr-demo-001",
            recipient="external-landlord@gmail.com",
            body="Inquiring about late check-in options.",
        )
        db.add(msg)
        db.commit()

        # Query back and verify
        saved_msg = db.query(Message).filter(Message.id == "msg-test-external-01").first()
        assert saved_msg is not None
        assert saved_msg.recipient == "external-landlord@gmail.com"
        assert saved_msg.booking_id is None
    finally:
        db.delete(msg)
        db.commit()
        db.close()


def test_seeded_data_content_and_id_numbers():
    """Query shows 20+ listings, 3 to 8 reviews each, and distinct verified_id_numbers for demo users."""
    db = SessionLocal()
    try:
        listings = db.query(Listing).all()
        assert len(listings) >= 20

        for lst in listings:
            rev_count = db.query(Review).filter(Review.listing_id == lst.id).count()
            assert 3 <= rev_count <= 8

        demo_users = db.query(User).filter(User.id.like("usr-demo-%")).all()
        assert len(demo_users) >= 3

        id_numbers = [u.verified_id_number for u in demo_users]
        assert len(id_numbers) == len(set(id_numbers)), "verified_id_numbers must be distinct"
        for num in id_numbers:
            assert num.startswith("ID-") and num.endswith("-DEMO")
    finally:
        db.close()
