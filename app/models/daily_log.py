"""
models/daily_log.py – DailyLog ORM model (now with user_id FK for multi-user support).
"""

from sqlalchemy import Column, Integer, Float, Text, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (
        # Each user can have at most one log per date
        UniqueConstraint("user_id", "date", name="uq_daily_log_user_date"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # ─── Multi-user FK ─────────────────────────────────────────────────────────
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    # ─── Date ──────────────────────────────────────────────────────────────────
    date = Column(Date, nullable=False, index=True)

    # ─── Wellbeing scores (1–10 scale) ────────────────────────────────────────
    mood_score = Column(Integer, nullable=False, default=7)
    focus_score = Column(Integer, nullable=False, default=7)
    stress_score = Column(Integer, nullable=False, default=5)
    energy_score = Column(Integer, nullable=False, default=7)

    # ─── Sleep ─────────────────────────────────────────────────────────────────
    sleep_hours = Column(Float, nullable=False, default=7.0)

    # ─── Free-text context ─────────────────────────────────────────────────────
    morning_intention = Column(Text, nullable=True)
    evening_reflection = Column(Text, nullable=True)
    blockers = Column(Text, nullable=True)
    gratitude = Column(Text, nullable=True)

    # ─── AI-generated plan stored here ─────────────────────────────────────────
    ai_daily_plan = Column(Text, nullable=True)

    # ─── Metadata ──────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<DailyLog user={self.user_id} date={self.date} mood={self.mood_score}>"
