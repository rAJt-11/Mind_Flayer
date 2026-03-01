"""
routers/users.py – User profile API endpoints (auth-protected).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import UserProfile
from app.schemas.user import UserProfileUpdate, UserProfileOut
from app.services.auth_service import get_current_user
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["User Profile"])


@router.get("/me", response_model=UserProfileOut)
async def get_profile(
    current_user: UserProfile = Depends(get_current_user),
):
    return current_user


@router.patch("/me", response_model=UserProfileOut)
async def update_profile(
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    user = await user_service.update_user(db, user_id=current_user.id, data=data)
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user
