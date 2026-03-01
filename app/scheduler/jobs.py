"""
scheduler/jobs.py – APScheduler job definitions.

All scheduled jobs that run in the background.
The scheduler is started when the FastAPI app starts up.

Schedule (IST / configurable):
  07:00  – Wake-up reminder
  09:15  – Morning work sync
  Every 2h – Hydration reminder
  18:30  – Evening reflection
  22:30  – Sleep reminder
  Sunday  – Weekly review generation
"""

import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings

logger = logging.getLogger(__name__)

# ─── In-memory notification store (replace with WebSocket / push in production) ─
_notifications: list[dict] = []


def get_notifications() -> list[dict]:
    """Return and clear pending notifications."""
    global _notifications
    copy = _notifications[:]
    _notifications.clear()
    return copy


def _push(title: str, message: str, level: str = "info") -> None:
    entry = {
        "title": title,
        "message": message,
        "level": level,
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    _notifications.append(entry)
    logger.info(f"[NOTIFICATION] {title}: {message}")


# ─── Job functions ────────────────────────────────────────────────────────────

def job_wake_up_reminder():
    _push(
        "☀️ Rise & Align",
        "Good morning, Champion. Your body is your command centre — hydrate before you caffeinate.",
        level="info",
    )


def job_morning_sync():
    _push(
        "🧠 Morning Sync",
        "Time for your 9:15 check-in. Log your mood, sleep, and today's intention. "
        "Your AI plan is waiting.",
        level="primary",
    )


def job_hydration_reminder():
    _push(
        "💧 Hydration Check",
        "Water. Right now. No negotiation. Dehydration drops cognitive output by 10–15%.",
        level="warning",
    )


def job_afternoon_reset():
    _push(
        "🎯 Afternoon Triage",
        "Mid-day check: Are you still working on your top priority? "
        "If not — drop everything else and return to it.",
        level="info",
    )


def job_evening_reflection():
    _push(
        "📔 Evening Reflection",
        "Time to close the loop. Log your evening reflection: "
        "What moved the needle today? What will you do differently tomorrow?",
        level="success",
    )


def job_sleep_reminder():
    _push(
        "😴 Sleep Protocol",
        "10:30 PM. Wind down begins now. Screens off in 30 minutes. "
        "Your tomorrow is built tonight.",
        level="warning",
    )


async def job_weekly_review():
    """Run the full weekly review for all active users — every Sunday at 20:00."""
    logger.info("Running Sunday weekly review job for all users...")
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.user import UserProfile
        from app.services.analytics_service import compute_and_store_weekly_analytics

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserProfile).where(UserProfile.is_active == True)
            )
            users = result.scalars().all()

            best_score = 0.0
            for user in users:
                try:
                    record = await compute_and_store_weekly_analytics(db, user.id)
                    if record.weekly_productivity_score > best_score:
                        best_score = record.weekly_productivity_score
                except Exception as ue:
                    logger.error(f"Weekly review failed for user {user.id}: {ue}")
            await db.commit()

        _push(
            "📊 Weekly Review Ready",
            "Your week has been analysed. Check your analytics dashboard.",
            level="success",
        )
    except Exception as e:
        logger.error(f"Weekly review job failed: {e}", exc_info=True)


# ─── Scheduler factory ────────────────────────────────────────────────────────

def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance."""
    tz = settings.SCHEDULER_TIMEZONE
    scheduler = AsyncIOScheduler(timezone=tz)

    # Wake-up reminder – 7:00 AM daily
    scheduler.add_job(
        job_wake_up_reminder,
        CronTrigger(hour=7, minute=0, timezone=tz),
        id="wake_up",
        replace_existing=True,
    )

    # Morning sync – 9:15 AM daily
    scheduler.add_job(
        job_morning_sync,
        CronTrigger(hour=9, minute=15, timezone=tz),
        id="morning_sync",
        replace_existing=True,
    )

    # Hydration reminders – every 2 hours (8 AM to 8 PM)
    for hour in range(8, 21, 2):
        scheduler.add_job(
            job_hydration_reminder,
            CronTrigger(hour=hour, minute=0, timezone=tz),
            id=f"hydration_{hour}",
            replace_existing=True,
        )

    # Afternoon triage – 2:30 PM
    scheduler.add_job(
        job_afternoon_reset,
        CronTrigger(hour=14, minute=30, timezone=tz),
        id="afternoon_triage",
        replace_existing=True,
    )

    # Evening reflection – 6:30 PM
    scheduler.add_job(
        job_evening_reflection,
        CronTrigger(hour=18, minute=30, timezone=tz),
        id="evening_reflection",
        replace_existing=True,
    )

    # Sleep reminder – 10:30 PM
    scheduler.add_job(
        job_sleep_reminder,
        CronTrigger(hour=22, minute=30, timezone=tz),
        id="sleep_reminder",
        replace_existing=True,
    )

    # Weekly review – Every Sunday at 8 PM
    scheduler.add_job(
        job_weekly_review,
        CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=tz),
        id="weekly_review",
        replace_existing=True,
    )

    logger.info(f"Scheduler configured with {len(scheduler.get_jobs())} jobs (tz={tz})")
    return scheduler
