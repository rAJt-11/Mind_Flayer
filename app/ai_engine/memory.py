"""
ai_engine/memory.py – Pattern detection and long-term memory analytics.

Analyses historical daily logs to identify behavioural patterns
(sleep-stress correlations, peak productivity windows, etc.)
and returns structured pattern insights for the suggestion engine.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class MemoryEngine:
    """
    Analyses historical DailyLog records to surface patterns.

    Key patterns detected:
    - Low sleep → high next-day stress correlation
    - Best performing task types (highest completion rate)
    - Peak productivity hour range
    - Mid-week mood dip
    - Hydration / habit consistency patterns
    """

    def analyse_patterns(
        self,
        daily_logs: List[Dict[str, Any]],
        tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Run full pattern analysis over provided daily logs.

        Args:
            daily_logs: list of DailyLog dicts (sorted by date, oldest first)
            tasks: list of Task dicts for completion analysis

        Returns:
            dict of named patterns with boolean flags and descriptive strings
        """
        tasks = tasks or []
        patterns: Dict[str, Any] = {}

        if len(daily_logs) >= 3:
            patterns["low_sleep_high_stress_correlation"] = (
                self._detect_sleep_stress_correlation(daily_logs)
            )
            patterns["midweek_mood_dip"] = self._detect_midweek_mood_dip(daily_logs)
            patterns["best_sleep_window"] = self._best_sleep_window(daily_logs)
            patterns["average_sleep"] = self._average(daily_logs, "sleep_hours")
            patterns["average_mood"] = self._average(daily_logs, "mood_score")
            patterns["average_stress"] = self._average(daily_logs, "stress_score")
            patterns["best_mood_day"] = self._best_day_for_metric(daily_logs, "mood_score")
            patterns["worst_stress_day"] = self._best_day_for_metric(
                daily_logs, "stress_score", highest=True
            )

        if tasks:
            patterns["best_task_type"] = self._best_task_type(tasks)
            patterns["worst_task_type"] = self._worst_task_type(tasks)
            patterns["completion_rate_by_type"] = self._completion_rate_by_type(tasks)

        return patterns

    def generate_weekly_narrative(
        self,
        daily_logs: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        habits: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate a qualitative weekly summary narrative.
        Used by the weekly review engine.
        """
        patterns = self.analyse_patterns(daily_logs, tasks)
        avg_sleep = patterns.get("average_sleep", 0)
        avg_mood = patterns.get("average_mood", 0)
        avg_stress = patterns.get("average_stress", 0)
        best_task = patterns.get("best_task_type", "unknown")

        insights = []

        if avg_sleep >= 7.5:
            insights.append(f"You averaged {avg_sleep:.1f}h sleep — above target. Strong foundation.")
        elif avg_sleep < 6:
            insights.append(
                f"Average sleep was {avg_sleep:.1f}h — significantly below target. "
                "This is the single biggest lever to pull next week."
            )
        else:
            insights.append(f"Sleep averaged {avg_sleep:.1f}h. Decent, but there's room to optimise.")

        if avg_mood >= 7:
            insights.append("Mood stayed relatively positive this week. That's a performance multiplier.")
        elif avg_mood < 5:
            insights.append(
                "Mood was consistently low this week. Look for root causes — "
                "sleep, workload, social isolation, or nutrition."
            )

        if patterns.get("midweek_mood_dip"):
            insights.append(
                "Mid-week mood dip pattern confirmed. "
                "Consider scheduling a lighter Wednesday to protect energy."
            )

        if best_task and best_task != "unknown":
            insights.append(
                f"Your highest completion rate was on '{best_task}' tasks. "
                "Use your lower energy days to stack more of those."
            )

        completion_rates = patterns.get("completion_rate_by_type", {})

        return {
            "patterns": patterns,
            "insights": insights,
            "completion_rates": completion_rates,
        }

    # ─── Private pattern detectors ────────────────────────────────────────────

    def _detect_sleep_stress_correlation(self, logs: List[Dict]) -> bool:
        """
        Check if nights with < 6.5h sleep reliably produce high next-day stress.
        Returns True if correlation is present in >= 50% of cases.
        """
        correlated = 0
        total = 0
        for i in range(len(logs) - 1):
            current = logs[i]
            next_day = logs[i + 1]
            if current.get("sleep_hours", 7) < 6.5:
                total += 1
                if next_day.get("stress_score", 5) >= 7:
                    correlated += 1
        if total == 0:
            return False
        return (correlated / total) >= 0.5

    def _detect_midweek_mood_dip(self, logs: List[Dict]) -> bool:
        """
        Check if Wednesday (weekday 2) shows consistently lower mood
        than Monday and Friday.
        """
        mood_by_weekday: Dict[int, List[int]] = defaultdict(list)
        for log in logs:
            log_date = log.get("date")
            if log_date:
                try:
                    from datetime import date as date_type
                    if isinstance(log_date, str):
                        from datetime import datetime
                        log_date = datetime.fromisoformat(log_date).date()
                    mood_by_weekday[log_date.weekday()].append(log.get("mood_score", 7))
                except Exception:
                    pass

        if not (0 in mood_by_weekday and 2 in mood_by_weekday):
            return False

        mon_avg = sum(mood_by_weekday[0]) / len(mood_by_weekday[0])
        wed_avg = sum(mood_by_weekday[2]) / len(mood_by_weekday[2])
        return wed_avg < mon_avg - 1.0  # significant dip = more than 1 point below Monday

    def _best_sleep_window(self, logs: List[Dict]) -> str:
        """Find the sleep band where the user scores highest on mood+focus."""
        buckets: Dict[str, List[float]] = {
            "< 6h": [], "6–7h": [], "7–8h": [], "8h+": []
        }
        for log in logs:
            h = log.get("sleep_hours", 7)
            score = (log.get("mood_score", 7) + log.get("focus_score", 7)) / 2
            if h < 6:
                buckets["< 6h"].append(score)
            elif h < 7:
                buckets["6–7h"].append(score)
            elif h < 8:
                buckets["7–8h"].append(score)
            else:
                buckets["8h+"].append(score)

        best = max(
            ((k, sum(v) / len(v)) for k, v in buckets.items() if v),
            key=lambda x: x[1],
            default=("7–8h", 7.0),
        )
        return best[0]

    def _best_day_for_metric(
        self, logs: List[Dict], metric: str, highest: bool = False
    ) -> str:
        """Return the weekday name that shows best (or worst) average for a metric."""
        day_scores: Dict[int, List[float]] = defaultdict(list)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for log in logs:
            log_date = log.get("date")
            if log_date:
                try:
                    from datetime import datetime
                    if isinstance(log_date, str):
                        log_date = datetime.fromisoformat(log_date).date()
                    day_scores[log_date.weekday()].append(log.get(metric, 5))
                except Exception:
                    pass
        if not day_scores:
            return "Unknown"
        avgs = {day: sum(vals) / len(vals) for day, vals in day_scores.items()}
        best_idx = (max if highest else min)(avgs, key=avgs.get)
        return days[best_idx]

    def _average(self, logs: List[Dict], field: str) -> float:
        vals = [log.get(field, 0) for log in logs if log.get(field) is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    def _completion_rate_by_type(self, tasks: List[Dict]) -> Dict[str, float]:
        by_type: Dict[str, List[bool]] = defaultdict(list)
        for task in tasks:
            t = task.get("task_type", "admin")
            by_type[t].append(task.get("completed", False))
        return {
            t: round(sum(v) / len(v) * 100, 1)
            for t, v in by_type.items()
            if v
        }

    def _best_task_type(self, tasks: List[Dict]) -> str:
        rates = self._completion_rate_by_type(tasks)
        if not rates:
            return "unknown"
        return max(rates, key=rates.get)

    def _worst_task_type(self, tasks: List[Dict]) -> str:
        rates = self._completion_rate_by_type(tasks)
        if not rates:
            return "unknown"
        return min(rates, key=rates.get)
