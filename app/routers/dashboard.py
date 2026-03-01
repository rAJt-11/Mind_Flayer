"""
routers/dashboard.py – UI page routes (Jinja2 templates), all auth-protected.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import UserProfile
from app.services.auth_service import get_current_user
from app.services.log_service import get_today_log, get_recent_logs, logs_to_dicts
from app.services.task_service import get_tasks, get_pending_tasks_for_brain
from app.services.habit_service import get_habits, habits_to_dicts
from app.services.analytics_service import get_latest_analytics, get_analytics_history
from app.ai_engine.brain import MindFlayerBrain, MentalState
from app.ai_engine.suggestions import SuggestionEngine
from datetime import date
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")

_brain = MindFlayerBrain()
_suggestions = SuggestionEngine()


def _redirect_to_login():
    return RedirectResponse(url="/login", status_code=302)


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    try:
        uid = current_user.id
        today_log = await get_today_log(db, uid)
        recent_logs = await get_recent_logs(db, uid, days=7)
        tasks = await get_tasks(db, uid, completed=False, limit=10)
        completed_tasks = await get_tasks(db, uid, completed=True, limit=5)
        habits = await get_habits(db, uid, active_only=True)
        analytics = await get_latest_analytics(db, uid)

        plan_data = None
        suggestions = []
        readiness = "good"
        readiness_score = 70

        if today_log:
            state = MentalState(
                sleep_hours=today_log.sleep_hours,
                mood_score=today_log.mood_score,
                focus_score=today_log.focus_score,
                stress_score=today_log.stress_score,
                energy_score=today_log.energy_score,
            )
            readiness = state.overall_readiness
            readiness_score = _brain._compute_readiness_score(state)
            habit_dicts = await habits_to_dicts(habits)
            suggestions = _suggestions.generate_suggestions(state, habits=habit_dicts)

            if today_log.ai_daily_plan:
                try:
                    plan_data = json.loads(today_log.ai_daily_plan)
                except Exception:
                    pass

        log_dicts = await logs_to_dicts(recent_logs)
        chart_labels = [str(l["date"]) for l in log_dicts]
        mood_data = [l["mood_score"] for l in log_dicts]
        sleep_data = [l["sleep_hours"] for l in log_dicts]
        stress_data = [l["stress_score"] for l in log_dicts]
        energy_data = [l["energy_score"] for l in log_dicts]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": current_user,
            "today_log": today_log,
            "tasks": tasks,
            "completed_tasks": completed_tasks,
            "habits": habits,
            "analytics": analytics,
            "plan_data": plan_data,
            "suggestions": suggestions,
            "readiness": readiness,
            "readiness_score": readiness_score,
            "chart_labels": json.dumps(chart_labels),
            "mood_data": json.dumps(mood_data),
            "sleep_data": json.dumps(sleep_data),
            "stress_data": json.dumps(stress_data),
            "energy_data": json.dumps(energy_data),
            "today": date.today().isoformat(),
        })
    except Exception as e:
        if "303" in str(e) or "Location" in str(getattr(e, "headers", {})):
            raise
        logger.error(f"Dashboard error: {e}", exc_info=True)
        raise


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    tasks = await get_tasks(db, current_user.id, limit=100)
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "user": current_user,
        "tasks": tasks,
    })


@router.get("/habits", response_class=HTMLResponse)
async def habits_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    habits = await get_habits(db, current_user.id, active_only=False)
    return templates.TemplateResponse("habits.html", {
        "request": request,
        "user": current_user,
        "habits": habits,
    })


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    uid = current_user.id
    history = await get_analytics_history(db, uid, weeks=8)
    latest = await get_latest_analytics(db, uid)

    week_labels = [str(r.week_start_date) for r in history]
    productivity_data = [r.weekly_productivity_score for r in history]
    mood_data = [r.mood_average for r in history]
    sleep_data = [r.sleep_average for r in history]
    task_rate_data = [r.task_completion_rate for r in history]

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": current_user,
        "latest": latest,
        "history": history,
        "week_labels": json.dumps(week_labels),
        "productivity_data": json.dumps(productivity_data),
        "mood_data": json.dumps(mood_data),
        "sleep_data": json.dumps(sleep_data),
        "task_rate_data": json.dumps(task_rate_data),
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user,
    })


@router.get("/daily-plan", response_class=HTMLResponse)
async def daily_plan_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    today_log = await get_today_log(db, current_user.id)
    plan_data = None
    if today_log and today_log.ai_daily_plan:
        try:
            plan_data = json.loads(today_log.ai_daily_plan)
        except Exception:
            pass
    return templates.TemplateResponse("daily_plan.html", {
        "request": request,
        "user": current_user,
        "today_log": today_log,
        "plan_data": plan_data,
        "today": date.today().isoformat(),
    })
