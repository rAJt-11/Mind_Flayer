"""
models/task.py – Task ORM model (now with user_id FK for multi-user support).
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from app.database import Base


class TaskCategory(str, enum.Enum):
    work = "work"
    health = "health"
    personal = "personal"
    money = "money"
    learning = "learning"


class TaskType(str, enum.Enum):
    implementation = "implementation"   # deep coding / building
    documentation = "documentation"     # writing / docs
    creative = "creative"               # brainstorming / design
    admin = "admin"                     # emails / meetings / forms
    review = "review"                   # reading / code review
    planning = "planning"               # strategy / roadmapping


class EnergyLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    # ─── Multi-user FK ─────────────────────────────────────────────────────────
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    # ─── Core fields ───────────────────────────────────────────────────────────
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SAEnum(TaskCategory), default=TaskCategory.work)
    task_type = Column(SAEnum(TaskType), default=TaskType.admin)
    priority = Column(SAEnum(Priority), default=Priority.medium)
    estimated_energy = Column(SAEnum(EnergyLevel), default=EnergyLevel.medium)

    # ─── Scheduling ────────────────────────────────────────────────────────────
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_minutes = Column(Integer, default=30)

    # ─── Status ────────────────────────────────────────────────────────────────
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ─── Metadata ──────────────────────────────────────────────────────────────
    tags = Column(String(500), nullable=True)   # comma-separated
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} completed={self.completed}>"
