import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User
from tripbuddy_core.auth import hash_password, verify_password, create_access_token
from tripbuddy_core.schemas import UserSignup, UserLogin, UserProfilePublic
from tripbuddy_core.services import get_user_profile_masked
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserProfilePublic)
def signup(data: UserSignup, response: Response, db: Session = Depends(get_db)):
    """Sign up a new user with bcrypt-hashed password and set httpOnly session cookie."""
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    verified_id = f"ID-{uuid.uuid4().hex[:6].upper()}-DEMO"

    user = User(
        id=user_id,
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        verified_id_number=verified_id,
        is_host=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7200,
        samesite="lax",
    )

    return get_user_profile_masked(db, user.id)


@router.post("/login", response_model=UserProfilePublic)
def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate user with email and password, setting httpOnly session cookie."""
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.email)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7200,
        samesite="lax",
    )

    return get_user_profile_masked(db, user.id)


@router.post("/logout")
def logout(response: Response):
    """Clear client session cookie."""
    response.delete_cookie(key="access_token")
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/me", response_model=UserProfilePublic)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the profile for the currently authenticated user (masked verified ID)."""
    return get_user_profile_masked(db, current_user.id)

