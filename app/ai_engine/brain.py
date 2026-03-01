"""
ai_engine/brain.py – The Mind Flayer core intelligence.

This is the primary decision-making engine. It analyses the user's
current state (sleep, mood, stress) and produces an adaptive daily plan
with task recommendations and wellness actions.

The tone is calm, strategic, and slightly intense – like a personal coach
who knows you deeply and doesn't sugarcoat the truth.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class MentalState:
    """Snapshot of the user's current mental and physical state."""
    sleep_hours: float = 7.0
    mood_score: int = 7       # 1–10
    focus_score: int = 7      # 1–10
    stress_score: int = 5     # 1–10
    energy_score: int = 7     # 1–10

    @property
    def is_low_sleep(self) -> bool:
        return self.sleep_hours < settings.LOW_SLEEP_THRESHOLD

    @property
    def is_low_mood(self) -> bool:
        return self.mood_score < settings.LOW_MOOD_THRESHOLD

    @property
    def is_high_stress(self) -> bool:
        return self.stress_score > settings.HIGH_STRESS_THRESHOLD

    @property
    def is_great_sleep(self) -> bool:
        return self.sleep_hours >= settings.GREAT_SLEEP_THRESHOLD

    @property
    def overall_readiness(self) -> str:
        """Compute overall readiness band: 'peak', 'good', 'moderate', 'low'."""
        composite = (
            self.mood_score * 0.25
            + self.focus_score * 0.25
            + (10 - self.stress_score) * 0.20
            + self.energy_score * 0.20
            + min(self.sleep_hours / 8.0, 1.0) * 10 * 0.10
        )
        if composite >= 8.0:
            return "peak"
        elif composite >= 6.5:
            return "good"
        elif composite >= 5.0:
            return "moderate"
        else:
            return "low"


@dataclass
class TaskRecommendation:
    """A single recommended task block in the daily plan."""
    time_slot: str            # e.g. "9:30 AM"
    title: str
    task_type: str
    energy_required: str      # low / medium / high
    duration_minutes: int
    rationale: str            # WHY the brain chose this
    is_major: bool = True     # major vs minor task


@dataclass
class DailyPlan:
    """The full AI-generated daily plan."""
    greeting: str
    state_assessment: str
    major_tasks: List[TaskRecommendation] = field(default_factory=list)
    minor_tasks: List[TaskRecommendation] = field(default_factory=list)
    health_reminders: List[str] = field(default_factory=list)
    break_schedule: List[Dict[str, str]] = field(default_factory=list)
    evening_prompt: str = ""
    warnings: List[str] = field(default_factory=list)
    readiness_level: str = "good"
    readiness_score: int = 70

    def to_dict(self) -> Dict[str, Any]:
        return {
            "greeting": self.greeting,
            "state_assessment": self.state_assessment,
            "readiness_level": self.readiness_level,
            "readiness_score": self.readiness_score,
            "major_tasks": [vars(t) for t in self.major_tasks],
            "minor_tasks": [vars(t) for t in self.minor_tasks],
            "health_reminders": self.health_reminders,
            "break_schedule": self.break_schedule,
            "evening_prompt": self.evening_prompt,
            "warnings": self.warnings,
        }


# ─── Brain ────────────────────────────────────────────────────────────────────

class MindFlayerBrain:
    """
    Core AI reasoning engine.

    Implements an adaptive rule-based decision tree that maps the user's
    current state to an optimal set of tasks and wellness actions. The logic
    is intentionally transparent so it can be augmented with an LLM later.
    """

    # Task type → energy mapping
    ENERGY_MAP = {
        "implementation": "high",
        "creative": "high",
        "review": "medium",
        "documentation": "low",
        "admin": "low",
        "planning": "medium",
    }

    def generate_daily_plan(
        self,
        state: MentalState,
        user_name: str = "Champion",
        pending_tasks: Optional[List[Dict]] = None,
    ) -> DailyPlan:
        """
        Main entry point: given a MentalState, produce a full DailyPlan.
        This embodies the 'Executive Coach' persona — direct, strategic, caring.
        """
        pending_tasks = pending_tasks or []
        readiness = state.overall_readiness

        # ── Build greeting based on readiness ──────────────────────────────────
        greeting = self._build_greeting(user_name, state, readiness)
        assessment = self._assess_state(state)
        warnings = self._compute_warnings(state)

        # ── Select tasks based on current state ────────────────────────────────
        recommended_types = self._recommend_task_types(state)
        major_tasks = self._select_major_tasks(state, recommended_types, pending_tasks)
        minor_tasks = self._select_minor_tasks(state, recommended_types, pending_tasks)

        # ── Build wellness plan ────────────────────────────────────────────────
        health_reminders = self._build_health_reminders(state)
        break_schedule = self._build_break_schedule(state)
        evening_prompt = self._build_evening_prompt(state)

        # ── Compute a readiness score (0–100) ─────────────────────────────────
        readiness_score = self._compute_readiness_score(state)

        plan = DailyPlan(
            greeting=greeting,
            state_assessment=assessment,
            major_tasks=major_tasks,
            minor_tasks=minor_tasks,
            health_reminders=health_reminders,
            break_schedule=break_schedule,
            evening_prompt=evening_prompt,
            warnings=warnings,
            readiness_level=readiness,
            readiness_score=readiness_score,
        )

        logger.info(
            f"Daily plan generated | readiness={readiness} "
            f"({readiness_score}) | sleep={state.sleep_hours}h "
            f"| mood={state.mood_score} | stress={state.stress_score}"
        )
        return plan

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _build_greeting(self, name: str, state: MentalState, readiness: str) -> str:
        greetings = {
            "peak": (
                f"Good morning, {name}. You're running at full power today. "
                "Slept well, mood is solid, energy is there. "
                "This is the day you do the hard thing you've been avoiding."
            ),
            "good": (
                f"Morning, {name}. You're in good shape — not perfect, but good. "
                "Good is enough to make serious progress. Focus on what matters and let the noise go."
            ),
            "moderate": (
                f"Hey {name}. Today isn't your strongest day, and that's okay. "
                "Your energy is limited — protect it. Don't fight on too many fronts. "
                "Pick your battles wisely."
            ),
            "low": (
                f"Listen, {name}. Your energy is low today. "
                "Don't pretend otherwise. Win small battles instead of fighting wars. "
                "Structured, low-cognitive tasks will keep momentum without burning you out."
            ),
        }
        return greetings.get(readiness, f"Good morning, {name}.")

    def _assess_state(self, state: MentalState) -> str:
        parts = []

        if state.is_low_sleep:
            parts.append(
                f"⚠️ You slept {state.sleep_hours:.1f}h — below your target. "
                "Cognitive tasks will feel harder. Lean on structured, low-thinking work."
            )
        elif state.is_great_sleep:
            parts.append(
                f"✅ Solid {state.sleep_hours:.1f}h of sleep. "
                "Your prefrontal cortex is firing. Use that cognitive edge."
            )

        if state.is_low_mood:
            parts.append(
                f"🫁 Mood at {state.mood_score}/10. Something's off. "
                "Don't push through — acknowledge it. A 15-min walk or reset session first."
            )

        if state.is_high_stress:
            parts.append(
                f"🔴 Stress at {state.stress_score}/10. That's high. "
                "Reduce scope. Protect your bandwidth. "
                "Insert intentional breaks — not optional."
            )

        if state.energy_score <= 4:
            parts.append(
                "⚡ Energy is depleted. Prioritise recovery actions. "
                "No heroics today — consistency beats intensity."
            )

        if not parts:
            parts.append(
                "💚 You're in a balanced state. Steady, focused work will compound nicely today."
            )

        return " ".join(parts)

    def _recommend_task_types(self, state: MentalState) -> List[str]:
        """
        Map current state → appropriate task types.
        Lower energy/sleep = lower cognitive load tasks.
        """
        if state.is_low_sleep or state.overall_readiness == "low":
            # Low energy: structured, low-cognitive work
            return ["documentation", "admin", "review"]

        if state.is_low_mood:
            # Low mood: do NOT put high-friction creative/implementation tasks
            # Small wins first to build momentum
            return ["admin", "documentation", "review", "planning"]

        if state.is_high_stress:
            # High stress: structured things that feel accomplishable
            return ["admin", "documentation", "planning"]

        if state.overall_readiness == "peak":
            # Peak state: deep work first
            return ["implementation", "creative", "planning", "review"]

        # Default: balanced
        return ["implementation", "planning", "documentation", "review"]

    def _select_major_tasks(
        self,
        state: MentalState,
        recommended_types: List[str],
        pending: List[Dict],
    ) -> List[TaskRecommendation]:
        """
        Pick 2 major tasks. If user has pending tasks, score and select the best fit.
        Otherwise generate contextual placeholders.
        """
        results: List[TaskRecommendation] = []
        used_ids = set()

        # Try to match pending tasks
        for task in pending:
            if len(results) >= 2:
                break
            if task.get("id") in used_ids:
                continue
            task_type = task.get("task_type", "admin")
            if task_type in recommended_types:
                slot = "09:30 AM" if len(results) == 0 else "11:00 AM"
                results.append(TaskRecommendation(
                    time_slot=slot,
                    title=task.get("title", "Pending Task"),
                    task_type=task_type,
                    energy_required=self.ENERGY_MAP.get(task_type, "medium"),
                    duration_minutes=task.get("estimated_minutes", 60),
                    rationale=f"Matches your current readiness ({state.overall_readiness}). "
                              f"Task type '{task_type}' is optimal for your state today.",
                    is_major=True,
                ))
                used_ids.add(task.get("id"))

        # Fill with contextual suggestions if no matching tasks
        fallbacks = self._get_major_task_fallbacks(state, recommended_types)
        while len(results) < 2 and fallbacks:
            results.append(fallbacks.pop(0))

        return results

    def _select_minor_tasks(
        self,
        state: MentalState,
        recommended_types: List[str],
        pending: List[Dict],
    ) -> List[TaskRecommendation]:
        """Pick 2–3 minor supporting tasks."""
        results: List[TaskRecommendation] = []
        fallbacks = self._get_minor_task_fallbacks(state)
        while len(results) < 3 and fallbacks:
            results.append(fallbacks.pop(0))
        return results

    def _get_major_task_fallbacks(
        self, state: MentalState, types: List[str]
    ) -> List[TaskRecommendation]:
        """Context-aware major task suggestions when no pending tasks exist."""
        primary = types[0] if types else "documentation"
        secondary = types[1] if len(types) > 1 else "review"

        suggestions = {
            "implementation": [
                TaskRecommendation(
                    "09:30 AM", "Deep Work Block – Core Feature Development",
                    "implementation", "high", 90,
                    "You're at peak cognitively. Hard problems deserve your best hours.", True
                ),
                TaskRecommendation(
                    "11:00 AM", "System Architecture Review & Refactor",
                    "implementation", "high", 60,
                    "Use remaining peak-state energy for a second deep-thinking session.", True
                ),
            ],
            "documentation": [
                TaskRecommendation(
                    "09:30 AM", "Write Technical Documentation / Specs",
                    "documentation", "low", 60,
                    "Documentation is high-value, low-energy. Perfect for your state today.", True
                ),
                TaskRecommendation(
                    "11:00 AM", "Update Project README & Changelogs",
                    "documentation", "low", 45,
                    "Keeps the project clean without demanding high cognitive load.", True
                ),
            ],
            "planning": [
                TaskRecommendation(
                    "09:30 AM", "Strategic Planning Session – Next Sprint",
                    "planning", "medium", 60,
                    "Planning doesn't drain you — it organises chaos. Good for today's state.", True
                ),
                TaskRecommendation(
                    "11:00 AM", "Priority Mapping & Task Triage",
                    "planning", "medium", 30,
                    "Clarity is a form of energy conservation. Know what matters.", True
                ),
            ],
            "admin": [
                TaskRecommendation(
                    "09:30 AM", "Inbox Zero Session – Clear Email & Messages",
                    "admin", "low", 45,
                    "Low energy? Clear the backlog. Small wins build momentum.", True
                ),
                TaskRecommendation(
                    "11:00 AM", "Update Project Tracker & Standup Notes",
                    "admin", "low", 30,
                    "Keeps you visible and organised with minimal cognitive cost.", True
                ),
            ],
        }
        return suggestions.get(primary, suggestions["documentation"])

    def _get_minor_task_fallbacks(self, state: MentalState) -> List[TaskRecommendation]:
        tasks = [
            TaskRecommendation(
                "02:00 PM", "Reply to non-urgent messages",
                "admin", "low", 20,
                "Post-lunch admin is ideal — cognitive load is naturally lower.", False
            ),
            TaskRecommendation(
                "03:00 PM", "15-min learning / reading session",
                "review", "low", 15,
                "Compound growth. 15 min per day = 90 hours per year.", False
            ),
            TaskRecommendation(
                "04:30 PM", "Day wrap-up: update task list & notes",
                "admin", "low", 15,
                "Close the loop. A clean end-of-day = a clean start tomorrow.", False
            ),
        ]
        if state.is_high_stress:
            # Replace with lighter tasks
            tasks[1] = TaskRecommendation(
                "03:00 PM", "5-min breathing / mindfulness reset",
                "admin", "low", 5,
                "Your stress is elevated. A micro-reset now prevents a crash later.", False
            )
        return tasks

    def _build_health_reminders(self, state: MentalState) -> List[str]:
        reminders = [
            "💧 Drink a glass of water right now. Dehydration kills focus.",
            "🎯 Phone on DND for the next 90 minutes.",
        ]
        if state.is_low_sleep:
            reminders.insert(0, "😴 You're sleep-deprived. No heroics — protect your energy.")
        if state.is_high_stress:
            reminders.append("🧘 4-7-8 breathing at lunch: inhale 4s, hold 7s, exhale 8s.")
        if state.mood_score <= 5:
            reminders.append("🚶 10-minute walk after lunch. Non-negotiable for mood recovery.")
        reminders.append("🥗 Eat a real meal. Your brain runs on glucose, not willpower.")
        return reminders

    def _build_break_schedule(self, state: MentalState) -> List[Dict[str, str]]:
        breaks = [
            {"time": "10:45 AM", "duration": "10 min", "activity": "Stand, stretch, water"},
            {"time": "01:00 PM", "duration": "45 min", "activity": "Lunch + short walk"},
            {"time": "03:30 PM", "duration": "10 min", "activity": "Eyes off screen, breathe"},
            {"time": "05:30 PM", "duration": "15 min", "activity": "End-of-day reset & plan tomorrow"},
        ]
        if state.is_high_stress:
            breaks.insert(1, {
                "time": "11:30 AM",
                "duration": "5 min",
                "activity": "Breathing or quick reset — stress is high today",
            })
        return breaks

    def _build_evening_prompt(self, state: MentalState) -> str:
        return (
            "📔 Evening Reflection Prompt:\n"
            "1. What was the one thing that actually moved the needle today?\n"
            "2. What felt harder than expected — and why?\n"
            "3. What will you do differently tomorrow?\n"
            "4. Name one thing you are grateful for right now.\n"
            "\nWrite honestly. The patterns in your answers will shape your AI plan tomorrow."
        )

    def _compute_warnings(self, state: MentalState) -> List[str]:
        warnings = []
        if state.is_low_sleep:
            warnings.append(
                f"Sleep deficit detected ({state.sleep_hours:.1f}h). "
                "Avoid critical decisions and complex coding today."
            )
        if state.is_high_stress and state.is_low_mood:
            warnings.append(
                "High stress + low mood combination detected. "
                "Consider rescheduling non-essential meetings."
            )
        if state.energy_score <= 3:
            warnings.append(
                "Very low energy. If possible, block the first 30 minutes for "
                "a gentle warm-up routine before starting work."
            )
        return warnings

    def _compute_readiness_score(self, state: MentalState) -> int:
        """Convert mental state to a 0–100 readiness score."""
        score = (
            state.mood_score * 10 * 0.20
            + state.focus_score * 10 * 0.25
            + (10 - state.stress_score) * 10 * 0.20
            + state.energy_score * 10 * 0.15
            + min(state.sleep_hours / 8.0, 1.0) * 100 * 0.20
        )
        return min(100, max(0, int(score)))
