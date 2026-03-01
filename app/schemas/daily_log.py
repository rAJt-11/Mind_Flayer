"""schemas/daily_log.py – Pydantic schemas for DailyLog."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class DailyLogBase(BaseModel):
    date: date
    mood_score: int = Field(default=7, ge=1, le=10)
    focus_score: int = Field(default=7, ge=1, le=10)
    stress_score: int = Field(default=5, ge=1, le=10)
    energy_score: int = Field(default=7, ge=1, le=10)
    sleep_hours: float = Field(default=7.0, ge=0.0, le=24.0)
    morning_intention: Optional[str] = None
    evening_reflection: Optional[str] = None
    blockers: Optional[str] = None
    gratitude: Optional[str] = None


class DailyLogCreate(DailyLogBase):
    pass


class DailyLogUpdate(BaseModel):
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    focus_score: Optional[int] = Field(None, ge=1, le=10)
    stress_score: Optional[int] = Field(None, ge=1, le=10)
    energy_score: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0.0, le=24.0)
    morning_intention: Optional[str] = None
    evening_reflection: Optional[str] = None
    blockers: Optional[str] = None
    gratitude: Optional[str] = None
    ai_daily_plan: Optional[str] = None


class DailyLogOut(DailyLogBase):
    id: int
    ai_daily_plan: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
