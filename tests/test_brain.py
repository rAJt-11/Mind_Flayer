"""
tests/test_brain.py – Unit tests for the MindFlayerBrain engine.

Run with: pytest tests/test_brain.py -v
"""

import pytest
from app.ai_engine.brain import MindFlayerBrain, MentalState, DailyPlan


@pytest.fixture
def brain():
    return MindFlayerBrain()


class TestMentalState:
    def test_low_sleep_detection(self):
        s = MentalState(sleep_hours=5.0)
        assert s.is_low_sleep is True

    def test_great_sleep_detection(self):
        s = MentalState(sleep_hours=8.0)
        assert s.is_great_sleep is True
        assert s.is_low_sleep is False

    def test_low_mood_detection(self):
        s = MentalState(mood_score=3)
        assert s.is_low_mood is True

    def test_high_stress_detection(self):
        s = MentalState(stress_score=8)
        assert s.is_high_stress is True

    def test_peak_readiness(self):
        s = MentalState(sleep_hours=8, mood_score=9, focus_score=9, stress_score=2, energy_score=9)
        assert s.overall_readiness == "peak"

    def test_low_readiness(self):
        s = MentalState(sleep_hours=4, mood_score=2, focus_score=2, stress_score=9, energy_score=2)
        assert s.overall_readiness == "low"

    def test_readiness_score_peak(self):
        s = MentalState(sleep_hours=8, mood_score=10, focus_score=10, stress_score=1, energy_score=10)
        brain = MindFlayerBrain()
        score = brain._compute_readiness_score(s)
        assert score >= 80

    def test_readiness_score_low(self):
        s = MentalState(sleep_hours=4, mood_score=2, focus_score=2, stress_score=10, energy_score=2)
        brain = MindFlayerBrain()
        score = brain._compute_readiness_score(s)
        assert score <= 40


class TestBrainPlanGeneration:
    def test_plan_has_required_fields(self, brain):
        state = MentalState()
        plan = brain.generate_daily_plan(state, user_name="Test")
        assert isinstance(plan, DailyPlan)
        assert plan.greeting
        assert plan.state_assessment
        assert len(plan.major_tasks) == 2
        assert len(plan.minor_tasks) == 3
        assert plan.health_reminders
        assert plan.break_schedule

    def test_low_sleep_recommends_low_energy_tasks(self, brain):
        state = MentalState(sleep_hours=5.0, mood_score=5)
        plan = brain.generate_daily_plan(state)
        # Major tasks should be documentation or admin (low energy)
        for task in plan.major_tasks:
            assert task.task_type in ("documentation", "admin", "review", "planning")

    def test_peak_state_recommends_deep_work(self, brain):
        state = MentalState(sleep_hours=8.5, mood_score=9, focus_score=9, stress_score=2, energy_score=9)
        plan = brain.generate_daily_plan(state)
        types = [t.task_type for t in plan.major_tasks]
        assert any(t in ("implementation", "creative", "planning") for t in types)

    def test_high_stress_produces_warning(self, brain):
        state = MentalState(stress_score=9, mood_score=3)
        plan = brain.generate_daily_plan(state)
        assert len(plan.warnings) >= 1

    def test_low_sleep_produces_warning(self, brain):
        state = MentalState(sleep_hours=4.5)
        plan = brain.generate_daily_plan(state)
        assert len(plan.warnings) >= 1
        assert any("sleep" in w.lower() for w in plan.warnings)

    def test_plan_to_dict_is_serializable(self, brain):
        import json
        state = MentalState()
        plan = brain.generate_daily_plan(state)
        d = plan.to_dict()
        # Should be JSON-serializable
        json.dumps(d)

    def test_pending_tasks_used_in_plan(self, brain):
        state = MentalState(sleep_hours=8, mood_score=8, focus_score=8, stress_score=3)
        pending = [
            {"id": 1, "title": "Build auth system", "task_type": "implementation",
             "estimated_minutes": 90},
        ]
        plan = brain.generate_daily_plan(state, pending_tasks=pending)
        titles = [t.title for t in plan.major_tasks]
        # The pending implementation task should appear
        assert "Build auth system" in titles

    def test_break_schedule_contains_lunch(self, brain):
        state = MentalState()
        plan = brain.generate_daily_plan(state)
        times = [b["time"] for b in plan.break_schedule]
        assert any("01:00" in t or "1:00" in t for t in times)

    def test_high_stress_adds_extra_break(self, brain):
        normal_state = MentalState(stress_score=4)
        stressed_state = MentalState(stress_score=9)
        normal_plan = brain.generate_daily_plan(normal_state)
        stressed_plan = brain.generate_daily_plan(stressed_state)
        assert len(stressed_plan.break_schedule) > len(normal_plan.break_schedule)
