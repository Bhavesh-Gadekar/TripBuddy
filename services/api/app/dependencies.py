from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from tripbuddy_core.db import get_db
from tripbuddy_core.models import User
from tripbuddy_core.auth import decode_access_token
from tripbuddy_core.errors import UnauthorizedError

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Resolve acting user from either httpOnly cookie 'access_token' or Bearer header."""
    token = None
    # 1. Check httpOnly cookie
    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    # 2. Check Bearer Authorization header
    elif auth and auth.credentials:
        token = auth.credentials

    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None


def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Enforce authenticated user, raising 401 if missing."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

