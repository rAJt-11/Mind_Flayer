"""
tests/test_suggestions.py – Unit tests for the SuggestionEngine.

Run with: pytest tests/test_suggestions.py -v
"""

import pytest
from app.ai_engine.brain import MentalState
from app.ai_engine.suggestions import SuggestionEngine


@pytest.fixture
def engine():
    return SuggestionEngine()


class TestSuggestionEngine:
    def test_returns_list(self, engine):
        state = MentalState()
        result = engine.generate_suggestions(state)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_max_6_suggestions(self, engine):
        state = MentalState(sleep_hours=4, mood_score=2, stress_score=9)
        result = engine.generate_suggestions(state)
        assert len(result) <= 6

    def test_low_sleep_mention(self, engine):
        state = MentalState(sleep_hours=4.5)
        result = engine.generate_suggestions(state)
        combined = " ".join(result).lower()
        # Should mention sleep
        assert "sleep" in combined or "hour" in combined

    def test_high_stress_mention(self, engine):
        state = MentalState(stress_score=8)
        result = engine.generate_suggestions(state)
        combined = " ".join(result).lower()
        assert "stress" in combined or "triage" in combined or "scope" in combined

    def test_great_sleep_positive(self, engine):
        state = MentalState(sleep_hours=8.0, mood_score=8, stress_score=3, focus_score=8, energy_score=8)
        result = engine.generate_suggestions(state)
        combined = " ".join(result).lower()
        # Should not focus on negative
        assert "critical" not in combined

    def test_habit_streak_suggestion(self, engine):
        state = MentalState()
        habits = [{"id": 1, "name": "Morning Run", "streak_count": 10, "frequency": "daily"}]
        result = engine.generate_suggestions(state, habits=habits)
        combined = " ".join(result)
        assert "Morning Run" in combined
        assert "10" in combined

    def test_habit_zero_streak_suggestion(self, engine):
        state = MentalState()
        habits = [{"id": 1, "name": "Journaling", "streak_count": 0, "frequency": "daily"}]
        result = engine.generate_suggestions(state, habits=habits)
        combined = " ".join(result)
        assert "Journaling" in combined

    def test_pattern_correlation_suggestion(self, engine):
        state = MentalState()
        patterns = {"low_sleep_high_stress_correlation": True}
        result = engine.generate_suggestions(state, weekly_patterns=patterns)
        combined = " ".join(result).lower()
        assert "sleep" in combined

    def test_midweek_pattern_suggestion(self, engine):
        state = MentalState()
        patterns = {"midweek_mood_dip": True}
        result = engine.generate_suggestions(state, weekly_patterns=patterns)
        combined = " ".join(result).lower()
        assert "mid-week" in combined or "wednesday" in combined

    def test_fallback_suggestion_always_present(self, engine):
        """Even with a perfectly normal state, at least one suggestion appears."""
        state = MentalState(sleep_hours=8, mood_score=7, stress_score=5, focus_score=7, energy_score=7)
        result = engine.generate_suggestions(state)
        assert len(result) >= 1
