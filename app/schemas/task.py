"""schemas/task.py – Pydantic schemas for Task."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.task import TaskCategory, TaskType, EnergyLevel, Priority


class TaskBase(BaseModel):
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    category: TaskCategory = TaskCategory.work
    task_type: TaskType = TaskType.admin
    priority: Priority = Priority.medium
    estimated_energy: EnergyLevel = EnergyLevel.medium
    scheduled_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_minutes: int = Field(default=30, ge=5)
    tags: Optional[str] = None
    notes: Optional[str] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    task_type: Optional[TaskType] = None
    priority: Optional[Priority] = None
    estimated_energy: Optional[EnergyLevel] = None
    scheduled_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    completed: Optional[bool] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class TaskOut(TaskBase):
    id: int
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
