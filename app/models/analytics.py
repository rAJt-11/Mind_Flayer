"""
models/analytics.py – ProgressAnalytics ORM model (now with user_id FK).
"""

from sqlalchemy import Column, Integer, Float, Text, Date, DateTime, String, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ProgressAnalytics(Base):
    __tablename__ = "progress_analytics"

    id = Column(Integer, primary_key=True, index=True)

    # ─── Multi-user FK ─────────────────────────────────────────────────────────
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    # ─── Week identification ────────────────────────────────────────────────────
    week_start_date = Column(Date, nullable=False, index=True)
    week_end_date = Column(Date, nullable=False)

    # ─── Aggregated scores ─────────────────────────────────────────────────────
    weekly_productivity_score = Column(Float, default=0.0)
    mood_average = Column(Float, default=0.0)
    sleep_average = Column(Float, default=0.0)
    focus_average = Column(Float, default=0.0)
    stress_average = Column(Float, default=0.0)
    energy_average = Column(Float, default=0.0)

    # ─── Task metrics ──────────────────────────────────────────────────────────
    tasks_total = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    task_completion_rate = Column(Float, default=0.0)

    # ─── Pattern insights (stored as JSON strings) ──────────────────────────────
    best_productivity_day = Column(String(20), nullable=True)
    worst_productivity_day = Column(String(20), nullable=True)
    peak_performance_hour = Column(String(5), nullable=True)

    # ─── AI-generated narrative ────────────────────────────────────────────────
    wins = Column(Text, nullable=True)
    missed_targets = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)
    recommended_focus = Column(Text, nullable=True)
    habit_consistency_score = Column(Float, default=0.0)

    # ─── Raw data snapshot (JSON) ──────────────────────────────────────────────
    raw_data_json = Column(Text, nullable=True)

    # ─── Metadata ──────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<ProgressAnalytics user={self.user_id} week={self.week_start_date} "
            f"productivity={self.weekly_productivity_score:.1f}>"
        )
