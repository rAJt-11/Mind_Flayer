"""
models/habit.py – Habit ORM model (now with user_id FK for multi-user support).
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum as SAEnum, DateTime
from sqlalchemy.sql import func
from app.database import Base


class HabitFrequency(str, enum.Enum):
    daily = "daily"
    weekdays = "weekdays"
    weekends = "weekends"
    weekly = "weekly"
    custom = "custom"


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)

    # ─── Multi-user FK ─────────────────────────────────────────────────────────
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    # ─── Core fields ───────────────────────────────────────────────────────────
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="health")   # health, mind, work, etc.
    frequency = Column(SAEnum(HabitFrequency), default=HabitFrequency.daily)
    reminder_time = Column(String(5), nullable=True)  # HH:MM
    icon = Column(String(10), default="⭐")            # emoji icon

    # ─── Streak tracking ───────────────────────────────────────────────────────
    streak_count = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    last_completed_date = Column(DateTime(timezone=True), nullable=True)

    # ─── Status ────────────────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True)

    # ─── Metadata ──────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Habit id={self.id} name={self.name!r} streak={self.streak_count}>"
