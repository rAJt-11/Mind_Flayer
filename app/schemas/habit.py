"""schemas/habit.py – Pydantic schemas for Habit."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.habit import HabitFrequency


class HabitBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: str = "health"
    frequency: HabitFrequency = HabitFrequency.daily
    reminder_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    icon: str = "⭐"


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[HabitFrequency] = None
    reminder_time: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class HabitOut(HabitBase):
    id: int
    streak_count: int
    longest_streak: int
    total_completions: int
    last_completed_date: Optional[datetime] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
