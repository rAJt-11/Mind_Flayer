"""
services/log_service.py – CRUD operations for DailyLog (user-scoped).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from app.models.daily_log import DailyLog
from app.schemas.daily_log import DailyLogCreate, DailyLogUpdate
from typing import Optional, List
from datetime import date
import logging

logger = logging.getLogger(__name__)


async def get_log_by_date(db: AsyncSession, log_date: date, user_id: int) -> Optional[DailyLog]:
    result = await db.execute(
        select(DailyLog).where(
            and_(DailyLog.date == log_date, DailyLog.user_id == user_id)
        )
    )
    return result.scalar_one_or_none()


async def get_today_log(db: AsyncSession, user_id: int) -> Optional[DailyLog]:
    return await get_log_by_date(db, date.today(), user_id)


async def get_recent_logs(db: AsyncSession, user_id: int, days: int = 7) -> List[DailyLog]:
    """Fetch the N most recent daily logs for a user, sorted oldest-first."""
    result = await db.execute(
        select(DailyLog)
        .where(DailyLog.user_id == user_id)
        .order_by(desc(DailyLog.date))
        .limit(days)
    )
    logs = result.scalars().all()
    return list(reversed(logs))  # oldest first for the AI engine


async def create_or_update_log(
    db: AsyncSession, data: DailyLogCreate, user_id: int
) -> DailyLog:
    """Upsert a daily log (one per user per day)."""
    existing = await get_log_by_date(db, data.date, user_id)
    if existing:
        update_data = data.model_dump(exclude={"date"})
        for field, value in update_data.items():
            setattr(existing, field, value)
        await db.flush()
        logger.info(f"DailyLog updated for user {user_id} on {data.date}")
        return existing

    log_data = data.model_dump()
    log_data["user_id"] = user_id
    log = DailyLog(**log_data)
    db.add(log)
    await db.flush()
    logger.info(f"DailyLog created for user {user_id} on {data.date}")
    return log


async def update_log(
    db: AsyncSession, log_id: int, data: DailyLogUpdate, user_id: int
) -> Optional[DailyLog]:
    result = await db.execute(
        select(DailyLog).where(DailyLog.id == log_id, DailyLog.user_id == user_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    await db.flush()
    return log


async def logs_to_dicts(logs: List[DailyLog]) -> List[dict]:
    """Convert ORM objects to plain dicts for the AI engine."""
    return [
        {
            "date": log.date,
            "sleep_hours": log.sleep_hours,
            "mood_score": log.mood_score,
            "focus_score": log.focus_score,
            "stress_score": log.stress_score,
            "energy_score": log.energy_score,
        }
        for log in logs
    ]
