"""
services/habit_service.py – CRUD and streak management for Habits (user-scoped).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.habit import Habit
from app.schemas.habit import HabitCreate, HabitUpdate
from typing import Optional, List
from datetime import datetime, timezone, date
import logging

logger = logging.getLogger(__name__)


async def get_habits(db: AsyncSession, user_id: int, active_only: bool = True) -> List[Habit]:
    conditions = [Habit.user_id == user_id]
    if active_only:
        conditions.append(Habit.is_active == True)
    q = select(Habit).where(and_(*conditions)).order_by(Habit.streak_count.desc())
    result = await db.execute(q)
    return result.scalars().all()


async def get_habit(db: AsyncSession, habit_id: int, user_id: int) -> Optional[Habit]:
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_habit(db: AsyncSession, data: HabitCreate, user_id: int) -> Habit:
    habit_data = data.model_dump()
    habit_data["user_id"] = user_id
    habit = Habit(**habit_data)
    db.add(habit)
    await db.flush()
    logger.info(f"Habit created for user {user_id}: '{habit.name}'")
    return habit


async def update_habit(
    db: AsyncSession, habit_id: int, data: HabitUpdate, user_id: int
) -> Optional[Habit]:
    habit = await get_habit(db, habit_id, user_id)
    if not habit:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    await db.flush()
    return habit


async def delete_habit(db: AsyncSession, habit_id: int, user_id: int) -> bool:
    habit = await get_habit(db, habit_id, user_id)
    if not habit:
        return False
    await db.delete(habit)
    await db.flush()
    return True


async def mark_habit_complete(db: AsyncSession, habit_id: int, user_id: int) -> Optional[Habit]:
    """Mark a habit as completed for today, updating streak."""
    habit = await get_habit(db, habit_id, user_id)
    if not habit:
        return None

    now = datetime.now(timezone.utc)
    today = date.today()

    if habit.last_completed_date:
        last = habit.last_completed_date
        last_date = last.date() if hasattr(last, 'date') else last

        if last_date == today:
            logger.info(f"Habit '{habit.name}' already completed today.")
            return habit

        days_since = (today - last_date).days
        if days_since > 1:
            habit.streak_count = 1
        else:
            habit.streak_count += 1
    else:
        habit.streak_count = 1

    habit.total_completions += 1
    habit.last_completed_date = now
    if habit.streak_count > habit.longest_streak:
        habit.longest_streak = habit.streak_count

    await db.flush()
    logger.info(f"Habit '{habit.name}' completed — streak: {habit.streak_count}")
    return habit


async def habits_to_dicts(habits: List[Habit]) -> List[dict]:
    return [
        {
            "id": h.id,
            "name": h.name,
            "streak_count": h.streak_count,
            "total_completions": h.total_completions,
            "frequency": h.frequency.value if h.frequency else "daily",
        }
        for h in habits
    ]
