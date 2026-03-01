"""
services/auth_service.py – Password hashing, JWT creation, and session-based auth.

Auth flow:
  1. /signup  → hash password → create UserProfile → store user_id in session
  2. /login   → verify password → store user_id in session
  3. get_current_user dependency → read user_id from session → fetch from DB
  4. /logout  → clear session
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

# ─── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT helpers ──────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT with an expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ─── Session-based current user dependency ────────────────────────────────────
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """
    FastAPI dependency: reads user_id from the session cookie,
    fetches the UserProfile from DB, and returns it.
    Raises HTTP 401 and redirects to /login if not authenticated.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Not authenticated",
        )

    result = await db.execute(
        select(UserProfile).where(UserProfile.id == int(user_id), UserProfile.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="User not found",
        )
    return user


# ─── Auth helpers ─────────────────────────────────────────────────────────────
async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[UserProfile]:
    """Verify credentials and return the user, or None on failure."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[UserProfile]:
    """Fetch a user by username."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.username == username)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    password: str,
    name: str,
    email: Optional[str] = None,
) -> UserProfile:
    """Create a new user with a hashed password."""
    # Compute avatar initials from name
    words = name.strip().split()
    initials = "".join(w[0].upper() for w in words[:2]) if words else "MF"

    user = UserProfile(
        username=username,
        hashed_password=hash_password(password),
        name=name,
        email=email,
        avatar_initials=initials,
    )
    db.add(user)
    await db.flush()
    logger.info(f"New user created: {username!r}")
    return user
