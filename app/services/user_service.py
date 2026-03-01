"""
services/user_service.py – CRUD operations for UserProfile.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserProfile
from app.schemas.user import UserProfileCreate, UserProfileUpdate
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def get_user(db: AsyncSession, user_id: int = 1) -> Optional[UserProfile]:
    """Fetch user by ID. Defaults to user 1 (single-user mode)."""
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    return result.scalar_one_or_none()


async def get_or_create_default_user(db: AsyncSession) -> UserProfile:
    """Ensure at least one user exists; create a default if not."""
    user = await get_user(db, user_id=1)
    if not user:
        user = UserProfile(
            username="champion",
            hashed_password="hashed_password_placeholder",  # Needs actual hash if used for login
            name="Champion",
            avatar_initials="CH",
            goals="Become the best version of myself — mentally, physically, and professionally.",
            strengths="Problem-solving, consistency, deep focus",
            weaknesses="Perfectionism, late start to mornings",
            dreams="Build something meaningful that outlasts me.",
        )
        db.add(user)
        await db.flush()
        logger.info("Default user profile created.")
    return user


async def update_user(
    db: AsyncSession, user_id: int, data: UserProfileUpdate
) -> Optional[UserProfile]:
    """Update user profile fields."""
    user = await get_user(db, user_id)
    if not user:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    return user


async def create_user(db: AsyncSession, data: UserProfileCreate) -> UserProfile:
    """Create a new user profile."""
    user = UserProfile(**data.model_dump())
    db.add(user)
    await db.flush()
    return user
