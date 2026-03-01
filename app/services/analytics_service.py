"""
services/analytics_service.py – Weekly analytics computation and retrieval (user-scoped).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from app.models.analytics import ProgressAnalytics
from app.ai_engine.weekly_review import WeeklyReviewEngine
from app.services.log_service import get_recent_logs, logs_to_dicts
from app.services.task_service import get_tasks
from app.services.habit_service import get_habits, habits_to_dicts
from typing import Optional, List
from datetime import date, timedelta
import json
import logging

logger = logging.getLogger(__name__)

_review_engine = WeeklyReviewEngine()


async def get_latest_analytics(db: AsyncSession, user_id: int) -> Optional[ProgressAnalytics]:
    result = await db.execute(
        select(ProgressAnalytics)
        .where(ProgressAnalytics.user_id == user_id)
        .order_by(desc(ProgressAnalytics.week_start_date))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_analytics_history(db: AsyncSession, user_id: int, weeks: int = 8) -> List[ProgressAnalytics]:
    result = await db.execute(
        select(ProgressAnalytics)
        .where(ProgressAnalytics.user_id == user_id)
        .order_by(desc(ProgressAnalytics.week_start_date))
        .limit(weeks)
    )
    records = result.scalars().all()
    return list(reversed(records))


async def compute_and_store_weekly_analytics(db: AsyncSession, user_id: int) -> ProgressAnalytics:
    """Run the full weekly review engine and persist results for this user."""
    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)

    logs = await get_recent_logs(db, user_id=user_id, days=7)
    tasks_orm = await get_tasks(db, user_id=user_id, limit=100)
    habits_orm = await get_habits(db, user_id=user_id, active_only=True)

    log_dicts = await logs_to_dicts(logs)
    habit_dicts = await habits_to_dicts(habits_orm)
    task_dicts = [
        {
            "id": t.id,
            "task_type": t.task_type.value if t.task_type else "admin",
            "completed": t.completed,
        }
        for t in tasks_orm
    ]

    review = _review_engine.generate_review(
        week_start=week_start,
        daily_logs=log_dicts,
        tasks=task_dicts,
        habits=habit_dicts,
    )

    existing_result = await db.execute(
        select(ProgressAnalytics).where(
            and_(
                ProgressAnalytics.user_id == user_id,
                ProgressAnalytics.week_start_date == week_start,
            )
        )
    )
    record = existing_result.scalar_one_or_none()

    data = {
        "user_id": user_id,
        "week_start_date": week_start,
        "week_end_date": week_end,
        "weekly_productivity_score": review["weekly_productivity_score"],
        "mood_average": review["mood_average"],
        "sleep_average": review["sleep_average"],
        "focus_average": review["focus_average"],
        "stress_average": review["stress_average"],
        "energy_average": review["energy_average"],
        "tasks_total": review["tasks_total"],
        "tasks_completed": review["tasks_completed"],
        "task_completion_rate": review["task_completion_rate"],
        "best_productivity_day": review.get("best_productivity_day"),
        "worst_productivity_day": review.get("worst_productivity_day"),
        "wins": review["wins"],
        "missed_targets": review["missed_targets"],
        "improvement_suggestions": review["improvement_suggestions"],
        "recommended_focus": review["recommended_focus"],
        "habit_consistency_score": review["habit_consistency_score"],
        "raw_data_json": json.dumps(review.get("completion_rates_by_type", {})),
    }

    if record:
        for k, v in data.items():
            setattr(record, k, v)
    else:
        record = ProgressAnalytics(**data)
        db.add(record)

    await db.flush()
    logger.info(f"Analytics stored for user {user_id}, week {week_start}")
    return record
