"""
seed_data.py – Populates the DB with realistic sample data.

Run standalone:
    python seed_data.py

Or it is called automatically by main.py on first startup.
"""

import asyncio
from datetime import date, timedelta, datetime, timezone
from app.database import init_db, AsyncSessionLocal
from app.models.user import UserProfile
from app.models.daily_log import DailyLog
from app.models.task import Task, TaskCategory, TaskType, EnergyLevel, Priority
from app.models.habit import Habit, HabitFrequency
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # ── User Profile ──────────────────────────────────────────────────────
        user = UserProfile(
            id=1,
            name="Alex Champion",
            email="alex@mindflayer.ai",
            avatar_initials="AC",
            wake_up_time="06:30",
            office_start_time="09:00",
            office_end_time="18:00",
            sleep_target_hours=7.5,
            role="Senior Software Engineer",
            timezone="Asia/Kolkata",
            goals=(
                "Ship my SaaS product by Q3. "
                "Learn system design at a deeper level. "
                "Run a 10K by December."
            ),
            strengths="Deep work, debugging, problem decomposition",
            weaknesses="Perfectionism, context-switching, saying yes to everything",
            dreams=(
                "Build a company that generates passive income. "
                "Travel for 3 months. Become physically elite."
            ),
        )
        db.add(user)

        # ── Daily Logs (last 7 days) ──────────────────────────────────────────
        today = date.today()
        logs_data = [
            {"days_ago": 6, "sleep": 7.5, "mood": 8, "focus": 8, "stress": 4, "energy": 8},
            {"days_ago": 5, "sleep": 6.0, "mood": 6, "focus": 6, "stress": 6, "energy": 5},
            {"days_ago": 4, "sleep": 8.0, "mood": 9, "focus": 9, "stress": 3, "energy": 9},
            {"days_ago": 3, "sleep": 5.5, "mood": 5, "focus": 5, "stress": 8, "energy": 4},
            {"days_ago": 2, "sleep": 7.0, "mood": 7, "focus": 7, "stress": 5, "energy": 7},
            {"days_ago": 1, "sleep": 6.5, "mood": 6, "focus": 7, "stress": 6, "energy": 6},
            {"days_ago": 0, "sleep": 7.5, "mood": 8, "focus": 8, "stress": 4, "energy": 8},
        ]
        for l in logs_data:
            log = DailyLog(
                date=today - timedelta(days=l["days_ago"]),
                sleep_hours=l["sleep"],
                mood_score=l["mood"],
                focus_score=l["focus"],
                stress_score=l["stress"],
                energy_score=l["energy"],
                morning_intention="Ship something meaningful today." if l["days_ago"] == 0 else None,
            )
            db.add(log)

        # ── Tasks ─────────────────────────────────────────────────────────────
        tasks = [
            Task(title="Implement user authentication flow", category=TaskCategory.work,
                 task_type=TaskType.implementation, priority=Priority.high,
                 estimated_energy=EnergyLevel.high, estimated_minutes=120, completed=True,
                 completed_at=datetime.now(timezone.utc) - timedelta(days=2)),
            Task(title="Write API documentation", category=TaskCategory.work,
                 task_type=TaskType.documentation, priority=Priority.medium,
                 estimated_energy=EnergyLevel.low, estimated_minutes=60, completed=True,
                 completed_at=datetime.now(timezone.utc) - timedelta(days=1)),
            Task(title="Design database schema for v2", category=TaskCategory.work,
                 task_type=TaskType.planning, priority=Priority.high,
                 estimated_energy=EnergyLevel.medium, estimated_minutes=90, completed=False),
            Task(title="30-minute morning run", category=TaskCategory.health,
                 task_type=TaskType.admin, priority=Priority.high,
                 estimated_energy=EnergyLevel.medium, estimated_minutes=30, completed=False),
            Task(title="Review system design book – Chapter 5", category=TaskCategory.personal,
                 task_type=TaskType.review, priority=Priority.low,
                 estimated_energy=EnergyLevel.low, estimated_minutes=45, completed=False),
            Task(title="Set up CI/CD pipeline", category=TaskCategory.work,
                 task_type=TaskType.implementation, priority=Priority.critical,
                 estimated_energy=EnergyLevel.high, estimated_minutes=180, completed=False),
            Task(title="Reply to investor emails", category=TaskCategory.money,
                 task_type=TaskType.admin, priority=Priority.high,
                 estimated_energy=EnergyLevel.low, estimated_minutes=30, completed=False),
            Task(title="Brainstorm marketing angles", category=TaskCategory.work,
                 task_type=TaskType.creative, priority=Priority.medium,
                 estimated_energy=EnergyLevel.medium, estimated_minutes=60, completed=False),
        ]
        for t in tasks:
            db.add(t)

        # ── Habits ────────────────────────────────────────────────────────────
        habits = [
            Habit(name="Morning Hydration", description="Drink 500ml water before coffee",
                  category="health", frequency=HabitFrequency.daily, icon="💧",
                  streak_count=12, longest_streak=21, total_completions=45, reminder_time="07:00"),
            Habit(name="Deep Work Block", description="90-min no-distraction work session",
                  category="work", frequency=HabitFrequency.weekdays, icon="🎯",
                  streak_count=5, longest_streak=15, total_completions=28, reminder_time="09:30"),
            Habit(name="Evening Walk", description="20-30 minute walk after dinner",
                  category="fitness", frequency=HabitFrequency.daily, icon="🚶",
                  streak_count=3, longest_streak=9, total_completions=18, reminder_time="19:30"),
            Habit(name="Reading Session", description="30 min non-fiction reading before bed",
                  category="learning", frequency=HabitFrequency.daily, icon="📚",
                  streak_count=7, longest_streak=30, total_completions=62, reminder_time="21:30"),
            Habit(name="Weekly Review", description="Sunday life and work reflection",
                  category="mind", frequency=HabitFrequency.weekly, icon="🔍",
                  streak_count=4, longest_streak=8, total_completions=16),
        ]
        for h in habits:
            db.add(h)

        await db.commit()
        logger.info("✅ Seed data loaded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
