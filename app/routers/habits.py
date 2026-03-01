"""
routers/habits.py – Habit API endpoints (auth-protected, user-scoped).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import UserProfile
from app.schemas.habit import HabitCreate, HabitUpdate, HabitOut
from app.services import habit_service
from app.services.auth_service import get_current_user
from typing import List

router = APIRouter(prefix="/api/habits", tags=["Habits"])


@router.get("/", response_model=List[HabitOut])
async def list_habits(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await habit_service.get_habits(db, current_user.id, active_only=active_only)


@router.post("/", response_model=HabitOut, status_code=201)
async def create_habit(
    data: HabitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await habit_service.create_habit(db, data, current_user.id)


@router.patch("/{habit_id}", response_model=HabitOut)
async def update_habit(
    habit_id: int,
    data: HabitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    habit = await habit_service.update_habit(db, habit_id, data, current_user.id)
    if not habit:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found")
    return habit


@router.post("/{habit_id}/complete", response_model=HabitOut)
async def complete_habit(
    habit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    habit = await habit_service.mark_habit_complete(db, habit_id, current_user.id)
    if not habit:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found")
    return habit


@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    ok = await habit_service.delete_habit(db, habit_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Habit {habit_id} not found")
