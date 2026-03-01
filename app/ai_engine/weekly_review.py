"""
ai_engine/weekly_review.py – Sunday weekly review engine.

Aggregates the past 7 days of logs, tasks, and habits into
a structured weekly report with wins, misses, and next-week focus areas.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from app.ai_engine.memory import MemoryEngine
import logging

logger = logging.getLogger(__name__)

memory_engine = MemoryEngine()


class WeeklyReviewEngine:
    """
    Generates Sunday weekly reviews.

    Output structure:
    - Aggregated metrics (sleep, mood, stress averages)
    - Wins of the week
    - Missed targets
    - Habit consistency score
    - Recommended focus area for next week
    - Improvement suggestions
    """

    def generate_review(
        self,
        week_start: date,
        daily_logs: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        habits: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate a complete weekly review.

        Args:
            week_start: Monday date of the reviewed week
            daily_logs: 7 daily log records for the week
            tasks: all tasks created/due in the week
            habits: all user habits (with streak data)

        Returns:
            Structured review dict
        """
        week_end = week_start + timedelta(days=6)

        # ── Aggregate metrics ──────────────────────────────────────────────────
        metrics = self._compute_metrics(daily_logs, tasks)

        # ── Narrative analysis via memory engine ──────────────────────────────
        narrative = memory_engine.generate_weekly_narrative(daily_logs, tasks, habits)

        # ── Habit consistency ─────────────────────────────────────────────────
        habit_score = self._compute_habit_consistency(habits)

        # ── Wins ──────────────────────────────────────────────────────────────
        wins = self._identify_wins(metrics, habits, narrative)

        # ── Misses ────────────────────────────────────────────────────────────
        misses = self._identify_misses(metrics, habits)

        # ── Suggestions for next week ─────────────────────────────────────────
        suggestions = self._generate_suggestions(metrics, narrative, habits)

        # ── Recommended focus area ────────────────────────────────────────────
        recommended_focus = self._recommend_focus(metrics, narrative)

        # ── Productivity score (0–100) ────────────────────────────────────────
        productivity_score = self._compute_productivity_score(metrics, habit_score)

        review = {
            "week_start_date": week_start.isoformat(),
            "week_end_date": week_end.isoformat(),
            # Metrics
            "sleep_average": metrics["sleep_average"],
            "mood_average": metrics["mood_average"],
            "stress_average": metrics["stress_average"],
            "focus_average": metrics["focus_average"],
            "energy_average": metrics["energy_average"],
            "tasks_total": metrics["tasks_total"],
            "tasks_completed": metrics["tasks_completed"],
            "task_completion_rate": metrics["task_completion_rate"],
            "habit_consistency_score": habit_score,
            "weekly_productivity_score": productivity_score,
            # Narrative
            "wins": wins,
            "missed_targets": misses,
            "improvement_suggestions": suggestions,
            "recommended_focus": recommended_focus,
            "insights": narrative.get("insights", []),
            "best_productivity_day": narrative["patterns"].get("best_mood_day", "Unknown"),
            "worst_productivity_day": narrative["patterns"].get("worst_stress_day", "Unknown"),
            "completion_rates_by_type": narrative.get("completion_rates", {}),
        }

        logger.info(
            f"Weekly review generated for {week_start} → {week_end} | "
            f"productivity={productivity_score:.1f}%"
        )
        return review

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _compute_metrics(
        self,
        logs: List[Dict],
        tasks: List[Dict],
    ) -> Dict[str, Any]:
        """Aggregate raw numbers from the week's logs and tasks."""
        def avg(field: str) -> float:
            vals = [l.get(field, 0) for l in logs if l.get(field) is not None]
            return round(sum(vals) / len(vals), 2) if vals else 0.0

        completed = sum(1 for t in tasks if t.get("completed"))
        total = len(tasks)
        completion_rate = round(completed / total * 100, 1) if total else 0.0

        return {
            "sleep_average": avg("sleep_hours"),
            "mood_average": avg("mood_score"),
            "stress_average": avg("stress_score"),
            "focus_average": avg("focus_score"),
            "energy_average": avg("energy_score"),
            "tasks_total": total,
            "tasks_completed": completed,
            "task_completion_rate": completion_rate,
            "days_logged": len(logs),
        }

    def _compute_habit_consistency(self, habits: List[Dict]) -> float:
        """
        Calculate average habit consistency score (0–100).
        Based on streak_count vs expected frequency for the week.
        """
        if not habits:
            return 0.0
        # Simple heuristic: a daily habit with streak >= 7 = 100%
        scores = []
        for habit in habits:
            streak = habit.get("streak_count", 0)
            freq = habit.get("frequency", "daily")
            expected = {"daily": 7, "weekdays": 5, "weekends": 2, "weekly": 1}.get(freq, 7)
            score = min(streak / expected, 1.0) * 100 if expected else 0
            scores.append(score)
        return round(sum(scores) / len(scores), 1)

    def _identify_wins(
        self,
        metrics: Dict,
        habits: List[Dict],
        narrative: Dict,
    ) -> str:
        wins = []

        if metrics["task_completion_rate"] >= 80:
            wins.append(
                f"✅ Exceptional task completion rate: {metrics['task_completion_rate']:.0f}%. "
                "Your execution was disciplined."
            )
        elif metrics["task_completion_rate"] >= 60:
            wins.append(
                f"✅ Solid task completion: {metrics['task_completion_rate']:.0f}%. "
                "Maintained good momentum."
            )

        if metrics["sleep_average"] >= 7.5:
            wins.append(
                f"✅ Averaged {metrics['sleep_average']:.1f}h sleep — above target. "
                "Your foundation was strong."
            )

        if metrics["mood_average"] >= 7:
            wins.append(f"✅ Mood averaged {metrics['mood_average']:.1f}/10 — positive week.")

        # Highlight habit wins
        for habit in habits:
            if habit.get("streak_count", 0) >= 7:
                wins.append(
                    f"✅ '{habit.get('name')}' habit: "
                    f"{habit.get('streak_count')} day streak maintained."
                )

        if not wins:
            wins.append("✅ You showed up every day. That counts. Build from here.")

        return "\n".join(wins)

    def _identify_misses(self, metrics: Dict, habits: List[Dict]) -> str:
        misses = []

        if metrics["task_completion_rate"] < 50:
            misses.append(
                f"⚠️ Only {metrics['task_completion_rate']:.0f}% of tasks completed. "
                "Either overcommitted or focus was scattered. Plan fewer, finish more."
            )
        if metrics["sleep_average"] < 6.5:
            misses.append(
                f"⚠️ Average sleep of {metrics['sleep_average']:.1f}h is a red flag. "
                "Sleep is non-negotiable performance infrastructure."
            )
        if metrics["stress_average"] >= 7:
            misses.append(
                f"⚠️ Stress averaged {metrics['stress_average']:.1f}/10. "
                "Too high to maintain peak performance sustainably."
            )
        if metrics["days_logged"] < 5:
            misses.append(
                "⚠️ Less than 5 daily logs recorded. "
                "The AI can't help you if you don't give it data. Commit to daily check-ins."
            )

        for habit in habits:
            if habit.get("streak_count", 0) == 0:
                misses.append(f"⚠️ '{habit.get('name')}' habit was missed this week.")

        if not misses:
            misses.append("No critical misses this week. Solid discipline.")

        return "\n".join(misses)

    def _generate_suggestions(
        self,
        metrics: Dict,
        narrative: Dict,
        habits: List[Dict],
    ) -> str:
        suggestions = []

        if metrics["sleep_average"] < 7.0:
            suggestions.append(
                "🎯 Sleep first. Set a hard cut-off at 10:30 PM — everything else can wait. "
                "Your cognitive output is directly proportional to your sleep quality."
            )
        if metrics["task_completion_rate"] < 70:
            suggestions.append(
                "🎯 Apply the 3 MIT rule: identify your 3 Most Important Tasks each morning. "
                "Don't start anything else until those are done."
            )
        if metrics["stress_average"] >= 7:
            suggestions.append(
                "🎯 Insert 10-minute recovery sessions between deep work blocks. "
                "Stress above 7 compresses creative thinking."
            )

        insights = narrative.get("insights", [])
        for insight in insights[:2]:
            suggestions.append(f"🎯 {insight}")

        if not suggestions:
            suggestions.append(
                "🎯 You performed well. Next level: identify the one process "
                "that would 10x your output and invest in it this week."
            )

        return "\n".join(suggestions)

    def _recommend_focus(self, metrics: Dict, narrative: Dict) -> str:
        if metrics["sleep_average"] < 6.5:
            return (
                "🔑 NEXT WEEK FOCUS: Sleep optimisation. "
                "Everything else improves when this improves. "
                "Hard bedroom cut-off at 10:30 PM. No screens 1 hour before bed."
            )
        if metrics["task_completion_rate"] < 60:
            return (
                "🔑 NEXT WEEK FOCUS: Execution discipline. "
                "Less planning, more doing. Time-block your top 3 priorities."
            )
        if metrics["stress_average"] >= 7:
            return (
                "🔑 NEXT WEEK FOCUS: Recovery and scope reduction. "
                "Say no to one commitment. Protect at least 2 PM blocks for deep work."
            )
        if metrics["mood_average"] < 5:
            return (
                "🔑 NEXT WEEK FOCUS: Energy management and environment. "
                "Schedule at least one enjoyable activity per day. "
                "Mood is a leading indicator of performance."
            )
        return (
            "🔑 NEXT WEEK FOCUS: Compound the wins. "
            "Identify what worked this week and systematise it. "
            "Consistency at a high level is the real goal."
        )

    def _compute_productivity_score(self, metrics: Dict, habit_score: float) -> float:
        """Compute overall weekly productivity score (0–100)."""
        task_factor = metrics["task_completion_rate"] * 0.35
        sleep_factor = min(metrics["sleep_average"] / 8.0, 1.0) * 100 * 0.20
        mood_factor = metrics["mood_average"] * 10 * 0.15
        stress_factor = (10 - metrics["stress_average"]) * 10 * 0.15
        habit_factor = habit_score * 0.15
        return round(
            task_factor + sleep_factor + mood_factor + stress_factor + habit_factor, 1
        )
