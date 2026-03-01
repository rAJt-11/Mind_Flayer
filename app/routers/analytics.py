"""
routers/analytics.py – Analytics and weekly review API endpoints (auth-protected).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import UserProfile
from app.schemas.analytics import ProgressAnalyticsOut
from app.services import analytics_service
from app.services.auth_service import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/latest", response_model=Optional[ProgressAnalyticsOut])
async def get_latest(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await analytics_service.get_latest_analytics(db, current_user.id)


@router.get("/history", response_model=List[ProgressAnalyticsOut])
async def get_history(
    weeks: int = 8,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await analytics_service.get_analytics_history(db, current_user.id, weeks=weeks)


@router.post("/compute", response_model=ProgressAnalyticsOut)
async def trigger_weekly_review(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Manually trigger a weekly review computation for the current user."""
    record = await analytics_service.compute_and_store_weekly_analytics(db, current_user.id)
    return record
