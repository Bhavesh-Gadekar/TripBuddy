"""Deterministic End-to-End Automation Smoke Test for TripBuddy.

Performs headless, non-interactive execution of:
1. Database reseed to known deterministic state
2. Authentication as demo user (Alex Mercer)
3. Submitting a review to a listing (POST /listings/{id}/reviews)
4. Interacting with AI Concierge (POST /concierge/chat)
5. Direct database audit verification:
   - Assistant reply & session_id
   - concierge_sessions row
   - All concierge_tool_calls rows for the session
   - Any new messages row
"""

import os
import sys
import json
import requests

# Add paths to ensure tripbuddy_core and scripts can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")

from tripbuddy_core.db import SessionLocal
from tripbuddy_core.models import ConciergeSession, ConciergeToolCall, Message, Review, User
from scripts.seed import seed_database

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
DEMO_USER_EMAIL = "alex.mercer@tripbuddy.test"
DEMO_USER_PASSWORD = "password123"
TARGET_LISTING_ID = "lst-goa-001"


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_smoke_test():
    print_banner("TRIPBUDDY AUTOMATION SMOKE TEST (PHASE 7)")
    print(f"API Target: {API_BASE_URL}")

    # Step 1: Reseed Database
    print("\n[Step 1/5] Reseeding database to known deterministic state...")
    seed_database()
    print("✓ Reseed completed successfully.")

    session = requests.Session()

    # Step 2: Log in as demo user
    print(f"\n[Step 2/5] Logging in as demo user ({DEMO_USER_EMAIL})...")
    login_url = f"{API_BASE_URL}/auth/login"
    login_payload = {
        "email": DEMO_USER_EMAIL,
        "password": DEMO_USER_PASSWORD,
    }
    resp = session.post(login_url, json=login_payload, timeout=15)
    if resp.status_code != 200:
        print(f"FAILED: Login error ({resp.status_code}): {resp.text}")
        sys.exit(1)

    user_info = resp.json()
    token = session.cookies.get("access_token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print("✓ Login successful!")
    print(f"  User ID: {user_info.get('id')}")
    print(f"  Name: {user_info.get('name')}")
    print(f"  Email: {user_info.get('email')}")
    print(f"  Masked Verified ID: {user_info.get('masked_verified_id_number')}")

    # Step 3: Post a review to a listing
    print(f"\n[Step 3/5] Posting review to listing '{TARGET_LISTING_ID}'...")
    review_url = f"{API_BASE_URL}/listings/{TARGET_LISTING_ID}/reviews"
    review_payload = {
        "rating": 5,
        "text": "Automated smoke test review: Absolutely breathtaking sunset view and pristine hospitality!",
    }
    resp = session.post(review_url, json=review_payload, headers=headers, timeout=15)
    if resp.status_code != 201:
        print(f"FAILED: Review post error ({resp.status_code}): {resp.text}")
        sys.exit(1)

    review_data = resp.json()
    print("✓ Review created successfully!")
    print(f"  Review ID: {review_data.get('id')}")
    print(f"  Author: {review_data.get('author_name')}")
    print(f"  Rating: {review_data.get('rating')} stars")
    print(f"  Text: {review_data.get('text')}")

    # Step 4: Call POST /concierge/chat with a prompt
    prompt = "Find a stay in Goa and check reviews"
    print(f"\n[Step 4/5] Calling POST /concierge/chat with prompt: '{prompt}'...")
    chat_url = f"{API_BASE_URL}/concierge/chat"
    chat_payload = {
        "prompt": prompt,
    }
    resp = session.post(chat_url, json=chat_payload, headers=headers, timeout=300)
    if resp.status_code != 200:
        print(f"FAILED: Concierge chat error ({resp.status_code}): {resp.text}")
        sys.exit(1)

    chat_data = resp.json()
    reply = chat_data.get("reply", "")
    session_id = chat_data.get("session_id", "")
    steps = chat_data.get("steps", [])

    print("✓ Concierge chat turn completed!")
    print(f"  Session ID: {session_id}")
    print(f"  Assistant Reply: {reply}")
    print(f"  Tool steps reported in API response: {len(steps)}")
    for i, step in enumerate(steps, 1):
        print(f"    Step {i}: Tool='{step.get('tool')}', Args={json.dumps(step.get('arguments'))}")

    # Step 5: Direct Database Audit Verification
    print("\n[Step 5/5] Querying database records for ground-truth audit verification...")
    db = SessionLocal()
    try:
        # A. Check concierge_sessions
        session_row = db.query(ConciergeSession).filter(ConciergeSession.session_id == session_id).first()
        if not session_row:
            print(f"FAILED: No concierge_sessions row found for session_id '{session_id}'!")
            sys.exit(1)

        print("\n--- [DB] CONCIERGE SESSION RECORD ---")
        print(f"  session_id:  {session_row.session_id}")
        print(f"  user_id:     {session_row.user_id}")
        print(f"  user_prompt: {session_row.user_prompt}")
        print(f"  final_reply: {session_row.final_reply}")
        print(f"  status:      {session_row.status}")
        print(f"  created_at:  {session_row.created_at}")

        # B. Check concierge_tool_calls
        tool_calls = (
            db.query(ConciergeToolCall)
            .filter(ConciergeToolCall.session_id == session_id)
            .order_by(ConciergeToolCall.id.asc())
            .all()
        )
        print(f"\n--- [DB] CONCIERGE TOOL CALLS ({len(tool_calls)} records found) ---")
        if not tool_calls:
            print("  (Note: No tool calls logged for this session)")
        for tc in tool_calls:
            result_snippet = json.dumps(tc.result)[:140] + ("..." if len(json.dumps(tc.result)) > 140 else "")
            print(f"  [Call ID {tc.id}]")
            print(f"    tool_name:  {tc.tool_name}")
            print(f"    arguments:  {json.dumps(tc.arguments)}")
            print(f"    status:     {tc.status}")
            print(f"    result:     {result_snippet}")
            print(f"    created_at: {tc.created_at}")

        # C. Check messages rows
        messages = db.query(Message).order_by(Message.created_at.desc()).limit(5).all()
        print(f"\n--- [DB] RECENT MESSAGES TABLE ({len(messages)} rows) ---")
        if not messages:
            print("  (No message records currently in database)")
        for m in messages:
            print(f"  [Message ID {m.id}]")
            print(f"    sender:     {m.sender}")
            print(f"    recipient:  {m.recipient}")
            print(f"    body:       {m.body}")
            print(f"    created_at: {m.created_at}")

        # D. Verify posted review in DB
        db_review = db.query(Review).filter(Review.id == review_data.get("id")).first()
        print("\n--- [DB] SUBMITTED REVIEW RECORD ---")
        if db_review:
            print(f"  review_id:   {db_review.id}")
            print(f"  listing_id:  {db_review.listing_id}")
            print(f"  author_name: {db_review.author_name}")
            print(f"  rating:      {db_review.rating}")
            print(f"  text:        {db_review.text}")
            print(f"  created_at:  {db_review.created_at}")

        print_banner("ALL SMOKE AUTOMATION CHECKS PASSED SUCCESSFULLY")
    finally:
        db.close()


if __name__ == "__main__":
    run_smoke_test()

