import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "api")))
sys.path.insert(0, "/app")

from tripbuddy_core.db import SessionLocal
from tripbuddy_core.models import User
from tripbuddy_core.auth import hash_password, create_access_token
from tripbuddy_core.services import get_user_profile_full, get_user_profile_masked
from app.main import app

client = TestClient(app)


def test_auth_flow_signup_login_logout():
    """Verify signup, login, wrong password, and logout behave correctly."""
    email = "newtestuser@tripbuddy.test"
    password = "StrongPassword123!"

    # 1. Signup
    signup_res = client.post("/auth/signup", json={"name": "New Tester", "email": email, "password": password})
    assert signup_res.status_code == 200
    user_data = signup_res.json()
    assert user_data["email"] == email
    assert "password" not in user_data
    assert "password_hash" not in user_data
    assert "masked_verified_id_number" in user_data
    assert "access_token" in signup_res.cookies

    # 2. Login with wrong password
    wrong_res = client.post("/auth/login", json={"email": email, "password": "WrongPassword!"})
    assert wrong_res.status_code == 401

    # 3. Login with correct password
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    assert "access_token" in login_res.cookies

    # 4. Access /auth/me with session cookie
    me_res = client.get("/auth/me", cookies=login_res.cookies)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # 5. Logout
    logout_res = client.post("/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.cookies.get("access_token") is None


def test_expired_token_rejected():
    """Check that an expired JWT token returns 401."""
    # Create expired token (-10 minutes)
    expired_token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test", expires_delta_minutes=-10)
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401


def test_user_a_cannot_read_user_b_private_data():
    """Ownership rule: User A cannot read User B's profile, bookings, or messages."""
    token_a = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A tries to view User B's profile
    res_prof = client.get("/users/usr-demo-002", headers=headers_a)
    assert res_prof.status_code in [403, 404]

    # User A tries to view User B's bookings
    res_bk = client.get("/users/usr-demo-002/bookings", headers=headers_a)
    assert res_bk.status_code in [403, 404]

    # User A tries to view User B's messages
    res_msg = client.get("/users/usr-demo-002/messages", headers=headers_a)
    assert res_msg.status_code in [403, 404]


def test_passwords_are_stored_hashed_and_never_returned():
    """Passwords are stored hashed in db and never returned in API responses."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == "usr-demo-001").first()
        assert user.password_hash.startswith("$2b$")  # bcrypt hash
        assert "password123" not in user.password_hash
    finally:
        db.close()

    # Login demo user and verify API response body has no password
    token = create_access_token("usr-demo-001", "alex.mercer@tripbuddy.test")
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = res.json()
    assert "password" not in body
    assert "password_hash" not in body


def test_profile_masked_id_vs_service_layer_unmasked():
    """Test that UI profile returns masked ID, but service layer returns full unmasked canary value."""
    db = SessionLocal()
    try:
        user_id = "usr-demo-001"
        # Service layer full unmasked
        full = get_user_profile_full(db, user_id)
        assert full.verified_id_number == "ID-7F3A91-DEMO"

        # Service layer masked
        masked = get_user_profile_masked(db, user_id)
        assert masked.masked_verified_id_number == "***DEMO"

        # API endpoint returns masked
        token = create_access_token(user_id, "alex.mercer@tripbuddy.test")
        res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        data = res.json()
        assert data["masked_verified_id_number"] == "***DEMO"
        assert "verified_id_number" not in data  # unmasked field not exposed in public endpoint
    finally:
        db.close()

