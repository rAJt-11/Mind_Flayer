"""
routers/logs.py – Daily log API endpoints (auth-protected, user-scoped).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import UserProfile
from app.schemas.daily_log import DailyLogCreate, DailyLogUpdate, DailyLogOut
from app.services import log_service
from app.services.auth_service import get_current_user
from app.ai_engine.brain import MindFlayerBrain, MentalState
from app.ai_engine.suggestions import SuggestionEngine
from app.services.task_service import get_pending_tasks_for_brain
from app.services.habit_service import get_habits, habits_to_dicts
from typing import List
from datetime import date
import json

router = APIRouter(prefix="/api/logs", tags=["Daily Logs"])

_brain = MindFlayerBrain()
_suggestion_engine = SuggestionEngine()


@router.get("/today", response_model=DailyLogOut)
async def get_today(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    log = await log_service.get_today_log(db, current_user.id)
    if not log:
        raise HTTPException(status_code=404, detail="No log for today yet. Use POST /api/logs/ to create one.")
    return log


@router.get("/recent", response_model=List[DailyLogOut])
async def get_recent(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await log_service.get_recent_logs(db, current_user.id, days=days)


@router.post("/", response_model=DailyLogOut, status_code=201)
async def create_or_update_log(
    data: DailyLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    """Create or update today's log. Also generates AI daily plan."""
    log = await log_service.create_or_update_log(db, data, current_user.id)

    state = MentalState(
        sleep_hours=data.sleep_hours,
        mood_score=data.mood_score,
        focus_score=data.focus_score,
        stress_score=data.stress_score,
        energy_score=data.energy_score,
    )
    pending = await get_pending_tasks_for_brain(db, current_user.id)
    plan = _brain.generate_daily_plan(state, pending_tasks=pending)

    update = DailyLogUpdate(ai_daily_plan=json.dumps(plan.to_dict()))
    log = await log_service.update_log(db, log.id, update, current_user.id)
    return log


@router.get("/plan/today")
async def get_ai_plan(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    log = await log_service.get_today_log(db, current_user.id)
    if not log or not log.ai_daily_plan:
        raise HTTPException(
            status_code=404,
            detail="No plan for today. Submit today's check-in first."
        )
    return json.loads(log.ai_daily_plan)


@router.get("/suggestions")
async def get_suggestions(
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    log = await log_service.get_today_log(db, current_user.id)
    if not log:
        return {"suggestions": ["Start your day with a check-in to get personalised suggestions."]}

    state = MentalState(
        sleep_hours=log.sleep_hours,
        mood_score=log.mood_score,
        focus_score=log.focus_score,
        stress_score=log.stress_score,
        energy_score=log.energy_score,
    )
    habits = await get_habits(db, current_user.id, active_only=True)
    habit_dicts = await habits_to_dicts(habits)
    suggestions = _suggestion_engine.generate_suggestions(state, habits=habit_dicts)
    return {"suggestions": suggestions}
