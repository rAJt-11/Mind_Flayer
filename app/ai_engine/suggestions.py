"""
ai_engine/suggestions.py – Intelligent suggestion engine.

Converts the mental state + historical context into actionable
one-liner suggestions displayed on the dashboard.
"""

from typing import List, Optional, Dict, Any
from app.ai_engine.brain import MentalState
import logging

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """
    Generates contextual, human-sounding suggestions based on:
    - Current daily log (sleep, mood, stress)
    - Habit streak data
    - Task completion patterns
    - Historical weekly patterns
    """

    # ── Tone constants ────────────────────────────────────────────────────────
    _SLEEP_MESSAGES = {
        "critical": [  # < 5h
            "You slept less than 5 hours. Today is a recovery day — not a war day.",
            "Critical sleep deficit. Protect your remaining energy ruthlessly.",
        ],
        "low": [  # 5–6h
            "You slept {:.1f} hours. Stick to structured, low-cognitive tasks today.",
            "Light sleep night. Documentation and admin are your friends today.",
        ],
        "adequate": [  # 6–7.5h
            "Decent {:.1f}h of sleep. You have enough in the tank for solid work.",
        ],
        "great": [  # 7.5+
            "{:.1f} hours of quality sleep. Your brain is primed — don't waste the edge.",
            "You're well-rested. This is the time for deep work and creative thinking.",
        ],
    }

    _STRESS_MESSAGES = [
        "Your stress spikes after 3 PM. Insert a 10-min reset then.",
        "High stress compresses your thinking. Fewer tasks, better execution.",
        "Stress at {}/10. Time to triage — what actually needs done today?",
    ]

    _MOOD_MESSAGES = [
        "Mood is low. Start with a small win — build momentum before tackling the hard thing.",
        "When mood dips, discipline carries you. Show up anyway.",
        "Low energy today? That's data, not weakness. Plan accordingly.",
    ]

    _POSITIVE_MESSAGES = [
        "You're consistent. Consistency beats motivation every single time.",
        "Strong state today. Use it — it won't last forever.",
        "Your metrics are solid. Keep the standard high.",
    ]

    def generate_suggestions(
        self,
        state: MentalState,
        habits: Optional[List[Dict]] = None,
        weekly_patterns: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Generate a prioritised list of contextual suggestions.
        Each suggestion is a single actionable sentence.
        """
        suggestions: List[str] = []
        habits = habits or []
        weekly_patterns = weekly_patterns or {}

        # ── Sleep-based suggestions ────────────────────────────────────────────
        suggestions.extend(self._sleep_suggestions(state))

        # ── Mood-based suggestions ─────────────────────────────────────────────
        if state.is_low_mood:
            suggestions.append(self._mood_suggestions(state))

        # ── Stress-based suggestions ───────────────────────────────────────────
        if state.is_high_stress:
            suggestions.append(f"Stress at {state.stress_score}/10. Triage ruthlessly — what actually matters today?")

        # ── Habit streak suggestions ───────────────────────────────────────────
        suggestions.extend(self._habit_suggestions(habits))

        # ── Pattern-based insights ─────────────────────────────────────────────
        if weekly_patterns:
            suggestions.extend(self._pattern_suggestions(weekly_patterns))

        # ── Positive reinforcement (if state is good) ──────────────────────────
        if state.overall_readiness in ("peak", "good") and not suggestions:
            suggestions.append(
                "Your energy is aligned. Protect deep work blocks and "
                "avoid reactive email-first mornings."
            )

        # ── Default fallback ──────────────────────────────────────────────────
        if not suggestions:
            suggestions.append(
                "Start with a 2-minute intention: what is the ONE thing that, "
                "if done today, makes everything else easier?"
            )

        return suggestions[:6]  # Cap at 6 to avoid overwhelm

    def _sleep_suggestions(self, state: MentalState) -> List[str]:
        h = state.sleep_hours
        if h < 5:
            return [
                "You slept less than 5 hours. Today is about damage control — not ambition.",
                "Avoid high-stakes decisions when sleep-deprived. Your judgement is compromised.",
            ]
        elif h < settings_low_threshold():
            return [
                f"You slept {h:.1f} hours. Focus on structured tasks — avoid creative deep work.",
            ]
        elif h >= 7.5:
            return [
                f"{h:.1f}h sleep — well rested. Your prefrontal cortex is primed for hard problems.",
            ]
        return []

    def _mood_suggestions(self, state: MentalState) -> str:
        return (
            f"Mood at {state.mood_score}/10. Don't fight it — flow with it. "
            "Small wins first. Administrative tasks build momentum without friction."
        )

    def _habit_suggestions(self, habits: List[Dict]) -> List[str]:
        suggestions = []
        for habit in habits:
            streak = habit.get("streak_count", 0)
            name = habit.get("name", "your habit")
            if streak >= 7:
                suggestions.append(
                    f"🔥 Your '{name}' habit streak is {streak} days. "
                    "That's compound interest on your identity. Don't break the chain."
                )
            elif streak == 0:
                suggestions.append(
                    f"'{name}' streak is at zero. Today is the best day to restart. "
                    "Start tiny — 5 minutes counts."
                )
            elif streak in (1, 2, 3):
                suggestions.append(
                    f"Fresh start on '{name}' — {streak} day streak. "
                    "The first 7 days are the hardest. Win today."
                )
        return suggestions[:2]  # max 2 habit suggestions

    def _pattern_suggestions(self, patterns: Dict[str, Any]) -> List[str]:
        suggestions = []
        if patterns.get("low_sleep_high_stress_correlation"):
            suggestions.append(
                "Pattern detected: poor sleep consistently raises your next-day stress. "
                "Tonight's sleep is tomorrow's performance."
            )
        if patterns.get("best_task_type"):
            best = patterns["best_task_type"]
            suggestions.append(
                f"Pattern: You complete '{best}' tasks at 80%+ rate. "
                "Schedule more of those on lower-energy days."
            )
        if patterns.get("midweek_mood_dip"):
            suggestions.append(
                "Pattern: Your mood tends to dip mid-week. "
                "Wednesdays: book a social interaction or brief change of environment."
            )
        return suggestions


def settings_low_threshold():
    """Avoids circular import for threshold access."""
    from app.config import settings
    return settings.LOW_SLEEP_THRESHOLD
