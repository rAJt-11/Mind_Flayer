"""schemas/user.py – Pydantic schemas for UserProfile."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserProfileBase(BaseModel):
    name: str = Field(default="User", max_length=100)
    email: Optional[str] = None
    avatar_initials: Optional[str] = Field(default="MF", max_length=5)
    wake_up_time: str = Field(default="07:00", pattern=r"^\d{2}:\d{2}$")
    office_start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    office_end_time: str = Field(default="18:00", pattern=r"^\d{2}:\d{2}$")
    sleep_target_hours: float = Field(default=7.5, ge=4.0, le=12.0)
    goals: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    dreams: Optional[str] = None
    role: Optional[str] = "Professional"
    timezone: str = "Asia/Kolkata"


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    name: Optional[str] = None
    wake_up_time: Optional[str] = None
    office_start_time: Optional[str] = None
    office_end_time: Optional[str] = None


class UserProfileOut(UserProfileBase):
    id: int
    username: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
