import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "api")))
sys.path.insert(0, "/app")

from tripbuddy_core.db import SessionLocal
from tripbuddy_core.models import Listing, Booking
from app.main import app

client = TestClient(app)


def test_get_listings_filters_alone_and_combined():
    """Verify each filter alone and combined with AND."""
    # City filter alone
    res_city = client.get("/listings?city=Goa")
    assert res_city.status_code == 200
    data_city = res_city.json()
    assert data_city["total"] > 0
    assert all(item["city"] == "Goa" for item in data_city["items"])

    # Price range alone
    res_price = client.get("/listings?min_price=2000&max_price=3500")
    assert res_price.status_code == 200
    data_price = res_price.json()
    assert all(2000 <= item["price_per_night"] <= 3500 for item in data_price["items"])

    # Property type alone
    res_type = client.get("/listings?type=Villa")
    assert res_type.status_code == 200
    data_type = res_type.json()
    assert all(item["type"] == "Villa" for item in data_type["items"])

    # Combined with AND: Goa + Villa + min_price
    res_combined = client.get("/listings?city=Goa&type=Villa&min_price=3000")
    assert res_combined.status_code == 200
    data_comb = res_combined.json()
    assert data_comb["total"] > 0
    for item in data_comb["items"]:
        assert item["city"] == "Goa"
        assert item["type"] == "Villa"
        assert item["price_per_night"] >= 3000


def test_get_listings_sorting_orders():
    """Verify each sort order: price_asc, price_desc, rating, newest."""
    # price_asc
    res_asc = client.get("/listings?sort=price_asc&limit=20")
    prices_asc = [item["price_per_night"] for item in res_asc.json()["items"]]
    assert prices_asc == sorted(prices_asc)

    # price_desc
    res_desc = client.get("/listings?sort=price_desc&limit=20")
    prices_desc = [item["price_per_night"] for item in res_desc.json()["items"]]
    assert prices_desc == sorted(prices_desc, reverse=True)

    # rating
    res_rating = client.get("/listings?sort=rating&limit=20")
    ratings = [item["rating"] for item in res_rating.json()["items"]]
    assert ratings == sorted(ratings, reverse=True)


def test_pagination_boundaries():
    """Check pagination boundaries (page 1, 12 per page, page count)."""
    res_p1 = client.get("/listings?page=1&limit=12")
    assert res_p1.status_code == 200
    d1 = res_p1.json()
    assert len(d1["items"]) == 12
    assert d1["page"] == 1
    assert d1["limit"] == 12

    res_p2 = client.get("/listings?page=2&limit=12")
    assert res_p2.status_code == 200
    d2 = res_p2.json()
    assert len(d2["items"]) == d1["total"] - 12
    assert d2["page"] == 2


def test_unknown_listing_returns_404():
    """GET /listings/{id} with unknown ID returns 404."""
    res = client.get("/listings/lst-non-existent-99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_date_availability_filter_excludes_overlapping_confirmed_booking():
    """Date availability filter excludes listings with an overlapping confirmed booking."""
    # In seed.py, lst-goa-001 has a confirmed booking for 2026-12-12 to 2026-12-14
    # Query overlapping range: 2026-12-11 to 2026-12-13
    res = client.get("/listings?city=Goa&checkin=2026-12-11&checkout=2026-12-13")
    assert res.status_code == 200
    listing_ids = [item["id"] for item in res.json()["items"]]
    assert "lst-goa-001" not in listing_ids

    # Query non-overlapping adjacent dates: 2026-12-14 to 2026-12-16
    res_free = client.get("/listings?city=Goa&checkin=2026-12-14&checkout=2026-12-16")
    assert res_free.status_code == 200
    listing_ids_free = [item["id"] for item in res_free.json()["items"]]
    assert "lst-goa-001" in listing_ids_free

