# Mind Flayer 
## AI-Powered Personal Life & Work Optimization Assistant

> *"Your energy is limited — protect it. Win small battles instead of fighting wars."*

---

## ✨ Features

- **🧠 AI Brain Engine** — Adaptive task recommendation based on sleep, mood, stress & energy
- **📊 Analytics Dashboard** — Interactive charts for mood, sleep, productivity trends
- **✅ Task Management** — Smart task filtering by energy level & cognitive load
- **🔥 Habit Tracker** — Streak-based habit system with completion logic
- **📔 Daily Planner** — AI-generated morning plan with major/minor tasks and break schedule
- **🔔 Smart Scheduler** — APScheduler notifications (wake-up, hydration, reflection, sleep)
- **📈 Weekly Reviews** — Automated pattern analysis with wins, misses & next-week focus
- **🌑 Dark Glassmorphism UI** — Stunning premium UI with TailwindCSS & Chart.js

---

## 🏗️ Architecture

```
mind_flayer/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Pydantic settings
│   ├── database.py          # Async SQLAlchemy + SQLite
│   ├── models/              # 5 ORM models (User, Log, Task, Habit, Analytics)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic layer
│   ├── routers/             # FastAPI routers (API + UI)
│   ├── ai_engine/           # Brain, Suggestions, Memory, Weekly Review
│   ├── scheduler/           # APScheduler jobs
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
├── tests/                   # Pytest unit tests
├── seed_data.py             # Sample data seeder
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "d:\Python + AI\Mind Flayer"
pip install -r requirements.txt
```

### 2. Run the App

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app auto-creates the database and loads seed data on first run.

### 3. Open in Browser

```
http://localhost:8000        → Dashboard
http://localhost:8000/tasks  → Task Manager
http://localhost:8000/habits → Habit Tracker
http://localhost:8000/analytics → Analytics
http://localhost:8000/api/docs  → Swagger API Docs
```

---

## 🧠 How the AI Works

### Daily Plan Generation
Submit your morning check-in (sleep, mood, focus, stress, energy) via the dashboard.
The AI brain maps your state to optimal task types:

| State | Task Recommendation |
|-------|---------------------|
| Low sleep (< 6h) | Documentation, Admin, Review |
| Low mood (< 4/10) | Admin, small wins first |
| High stress (> 7/10) | Triage, structured tasks |
| Peak state | Implementation, Creative, Deep work |

### Weekly Review Engine
Automatically runs every Sunday at 8 PM (IST). Analyses:
- Sleep patterns → performance correlation
- Task completion rate by type
- Mood trends across the week
- Habit consistency score

Trigger manually:
```bash
POST http://localhost:8000/api/analytics/compute
```

### Scheduler Jobs

| Time | Notification |
|------|-------------|
| 7:00 AM | ☀️ Wake-up reminder |
| 9:15 AM | 🧠 Morning check-in sync |
| Every 2h | 💧 Hydration reminder |
| 2:30 PM | 🎯 Afternoon triage |
| 6:30 PM | 📔 Evening reflection |
| 10:30 PM | 😴 Sleep protocol |
| Sunday 8 PM | 📊 Weekly review |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🌱 Seed Sample Data

```bash
python seed_data.py
```

Creates: 1 user profile, 7 daily logs, 8 tasks, 5 habits.

---

## 🔐 Configuration

Create a `.env` file to override defaults:

```env
DEBUG=True
DATABASE_URL=sqlite+aiosqlite:///./mind_flayer.db
SCHEDULER_TIMEZONE=Asia/Kolkata
LOW_SLEEP_THRESHOLD=6.0
LOW_MOOD_THRESHOLD=4
HIGH_STRESS_THRESHOLD=7
```

---

## 🌟 Roadmap (Future)

- [ ] LLM integration (GPT-4 / Gemini) for natural language coaching
- [ ] Telegram / WhatsApp notifications
- [ ] Email weekly digest
- [ ] OAuth2 login
- [ ] Multi-user support
- [ ] Voice check-in
- [ ] Vector memory storage

---

## 🧬 AI Personality

Mind Flayer speaks like an executive coach:

- **Calm** — Never panics, always strategic
- **Observant** — Notices patterns before you do
- **Honest** — Won't sugarcoat your low-sleep days
- **Slightly intense** — "Win small battles instead of fighting wars"
- **Not robotic** — Every message feels personal

---

*Built with ❤️ using FastAPI · SQLAlchemy · APScheduler · TailwindCSS · Chart.js*
