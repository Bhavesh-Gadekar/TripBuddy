import sys
import os
import concurrent.futures
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "api")))
sys.path.insert(0, "/app")

from tripbuddy_core.db import SessionLocal
from tripbuddy_core.services import calculate_pricing, create_booking_service
from tripbuddy_core.auth import create_access_token
from tripbuddy_core.errors import (
    DatesUnavailableError,
    InvalidGuestsError,
    InvalidDatesError,
)
from app.main import app

client = TestClient(app)


def test_pricing_function_unit_tests():
    """Unit tests for calculate_pricing with known numbers."""
    price_per_night = 3200
    checkin = "2026-11-10"
    checkout = "2026-11-13"  # 3 nights

    res = calculate_pricing(price_per_night, checkin, checkout)
    assert res.nights == 3
    assert res.price_per_night == 3200
    assert res.subtotal == 9600
    assert res.service_fee == 450
    assert res.total == 10050


def test_booking_validation_invalid_dates_and_guests():
    """Verify check-out before check-in and invalid guests are rejected."""
    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check-out before check-in
    res_bad_dates = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-goa-002",
            "checkin": "2026-11-15",
            "checkout": "2026-11-10",
            "guests": 2,
        },
    )
    assert res_bad_dates.status_code == 422

    # 2. Invalid guests: 0 guests or above max_guests (max 3 for lst-goa-002)
    res_zero_guests = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-goa-002",
            "checkin": "2026-11-10",
            "checkout": "2026-11-12",
            "guests": 0,
        },
    )
    assert res_zero_guests.status_code == 422

    res_too_many_guests = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-goa-002",
            "checkin": "2026-11-10",
            "checkout": "2026-11-12",
            "guests": 10,
        },
    )
    assert res_too_many_guests.status_code == 422


def test_overlapping_dates_rejected_and_adjacent_accepted():
    """Verify overlapping dates rejected, but checkout day equal to next checkin day accepted."""
    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    # In seed data, lst-goa-001 has confirmed booking for 2026-12-12 to 2026-12-14
    # Overlapping attempt: 2026-12-13 to 2026-12-15
    res_overlap = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-goa-001",
            "checkin": "2026-12-13",
            "checkout": "2026-12-15",
            "guests": 2,
        },
    )
    assert res_overlap.status_code == 400
    assert "already booked" in res_overlap.json()["detail"].lower()

    # Adjacent attempt (check-in on the exact checkout day of previous booking: 2026-12-14 to 2026-12-16 on lst-goa-002)
    res_adjacent = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-goa-002",
            "checkin": "2026-12-14",
            "checkout": "2026-12-16",
            "guests": 2,
        },
    )
    assert res_adjacent.status_code == 201
    assert res_adjacent.json()["status"] == "confirmed"


def test_cancellation_frees_dates():
    """Verify that cancelling a booking frees the dates for a new booking."""
    token = create_access_token("usr-demo-002", "samantha.chen@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Book stay
    res_book = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-jai-001",
            "checkin": "2026-11-20",
            "checkout": "2026-11-23",
            "guests": 3,
        },
    )
    assert res_book.status_code == 201
    booking_id = res_book.json()["id"]

    # 2. Second booking on same dates fails
    res_conflict = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-jai-001",
            "checkin": "2026-11-21",
            "checkout": "2026-11-24",
            "guests": 2,
        },
    )
    assert res_conflict.status_code == 400

    # 3. Cancel first booking
    res_cancel = client.post(f"/bookings/{booking_id}/cancel", headers=headers)
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"

    # 4. Now the dates are free, so booking succeeds
    res_retry = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-jai-001",
            "checkin": "2026-11-21",
            "checkout": "2026-11-24",
            "guests": 2,
        },
    )
    assert res_retry.status_code == 201


def test_concurrency_double_booking_prevented():
    """Verify that firing two simultaneous bookings for the same dates allows exactly one to succeed."""
    def try_book():
        db = SessionLocal()
        try:
            return create_booking_service(
                db=db,
                user_id="usr-demo-001",
                listing_id="lst-man-001",
                checkin="2026-12-20",
                checkout="2026-12-25",
                guests=2,
            )
        except Exception as e:
            return e
        finally:
            db.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(try_book)
        f2 = executor.submit(try_book)
        res1 = f1.result()
        res2 = f2.result()

    # Exactly one succeeded and one raised DatesUnavailableError
    success_count = sum(1 for r in [res1, res2] if not isinstance(r, Exception))
    failure_count = sum(1 for r in [res1, res2] if isinstance(r, DatesUnavailableError))
    assert success_count == 1
    assert failure_count == 1


def test_end_to_end_user_books_stay_and_appears_on_trips():
    """Verify that a demo user books a stay and it appears on their Trips page."""
    token = create_access_token("usr-demo-003", "rohan.deshmukh@tripbuddy.test")
    headers = {"Authorization": f"Bearer {token}"}

    # Book stay
    res_book = client.post(
        "/bookings",
        headers=headers,
        json={
            "listing_id": "lst-mun-001",
            "checkin": "2026-12-01",
            "checkout": "2026-12-05",
            "guests": 4,
        },
    )
    assert res_book.status_code == 201
    booking_ref = res_book.json()["reference"]

    # Query /bookings/my-trips
    res_trips = client.get("/bookings/my-trips", headers=headers)
    assert res_trips.status_code == 200
    trips = res_trips.json()
    assert any(t["reference"] == booking_ref for t in trips)
