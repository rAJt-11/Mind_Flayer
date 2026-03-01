"""schemas/analytics.py – Pydantic schemas for ProgressAnalytics."""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class ProgressAnalyticsOut(BaseModel):
    id: int
    week_start_date: date
    week_end_date: date
    weekly_productivity_score: float
    mood_average: float
    sleep_average: float
    focus_average: float
    stress_average: float
    energy_average: float
    tasks_total: int
    tasks_completed: int
    task_completion_rate: float
    best_productivity_day: Optional[str] = None
    worst_productivity_day: Optional[str] = None
    peak_performance_hour: Optional[str] = None
    wins: Optional[str] = None
    missed_targets: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    recommended_focus: Optional[str] = None
    habit_consistency_score: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
