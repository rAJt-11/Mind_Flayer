"""
models/user.py – UserProfile ORM model.

Stores user identity (login credentials) and personal configuration.
This is the foundational profile that the AI engine uses to personalise suggestions.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # ─── Auth credentials ──────────────────────────────────────────────────────
    username = Column(String(50), nullable=False, unique=True, index=True)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # ─── Identity ──────────────────────────────────────────────────────────────
    name = Column(String(100), nullable=False, default="User")
    email = Column(String(200), nullable=True, unique=True)
    avatar_initials = Column(String(5), nullable=True, default="MF")

    # ─── Daily schedule ────────────────────────────────────────────────────────
    wake_up_time = Column(String(5), default="07:00")          # HH:MM
    office_start_time = Column(String(5), default="09:00")
    office_end_time = Column(String(5), default="18:00")
    sleep_target_hours = Column(Float, default=7.5)

    # ─── Personal context (long-form text) ─────────────────────────────────────
    goals = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    dreams = Column(Text, nullable=True)
    role = Column(String(200), nullable=True, default="Professional")
    timezone = Column(String(50), default="Asia/Kolkata")

    # ─── Metadata ──────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} username={self.username!r} name={self.name!r}>"
