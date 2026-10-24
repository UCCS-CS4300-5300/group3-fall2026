import pytest

from .lesson_runner import apply_assignments_to_variables
from .lessons import BossLessonVar


@pytest.fixture
def slow_then_kill_assignments():
    """Return speed=3, speed=1, alive=False instructions in that order."""
    return [
        {"variable": "zombie_speed", "value": 3},
        {"variable": "zombie_speed", "value": 1},
        {"variable": "zombie_alive", "value": False},
    ]


def test_encounter_instructions_give_the_goal_without_the_assignment():
    assert BossLessonVar().instructions == "A zombie is approaching! Use the available blocks to defeat it."


def test_last_speed_assignment_sets_final_speed(slow_then_kill_assignments):
    result = BossLessonVar().apply_assignments_to_zombie_variables(slow_then_kill_assignments)
    assert result["variables"] == {"zombie_alive": False, "zombie_speed": 1}


def test_actions_preserve_assignment_order(slow_then_kill_assignments):
    result = BossLessonVar().apply_assignments_to_zombie_variables(slow_then_kill_assignments)
    assert result["actions"] == slow_then_kill_assignments


def test_empty_program_retains_initial_variables_without_actions():
    result = BossLessonVar().apply_assignments_to_zombie_variables([])
    assert result["variables"] == {"zombie_alive": True, "zombie_speed": 10}
    assert result["actions"] == []


def test_empty_program_does_not_pass_the_lesson():
    result = BossLessonVar().apply_assignments_to_zombie_variables([])
    assert result["passed"] is False


def test_setting_zombie_alive_false_passes_the_lesson():
    result = BossLessonVar().apply_assignments_to_zombie_variables([
        {"variable": "zombie_alive", "value": False},
    ])
    assert result["passed"] is True
    assert result["feedback"] == "The zombie is dead. You win!"


def test_setting_zombie_alive_true_after_false_fails_the_lesson():
    result = BossLessonVar().apply_assignments_to_zombie_variables([
        {"variable": "zombie_alive", "value": False},
        {"variable": "zombie_alive", "value": True},
    ])
    assert result["passed"] is False
    assert result["feedback"] == "The zombie is still alive. Try again."


def test_lowering_speed_leaves_the_zombie_alive():
    result = BossLessonVar().apply_assignments_to_zombie_variables([{"variable": "zombie_speed", "value": 1}])
    assert result["variables"] == {"zombie_alive": True, "zombie_speed": 1}
    assert result["passed"] is False


def test_slow_living_zombie_eats_the_player_slower():
    result = BossLessonVar().apply_assignments_to_zombie_variables([
        {"variable": "zombie_speed", "value": 3},
    ])
    assert result["passed"] is False
    assert result["feedback"] == "The zombie eats you slower."


def test_slow_dead_zombie_still_reports_victory(slow_then_kill_assignments):
    result = BossLessonVar().apply_assignments_to_zombie_variables(slow_then_kill_assignments)
    assert result["passed"] is True
    assert result["feedback"] == "The zombie is dead. You win!"


def test_restoring_starting_speed_does_not_report_slower_death():
    result = BossLessonVar().apply_assignments_to_zombie_variables([
        {"variable": "zombie_speed", "value": 3},
        {"variable": "zombie_speed", "value": 10},
    ])
    assert result["feedback"] == "The zombie is still alive. Try again."


def test_each_run_starts_with_speed_ten():
    lesson = BossLessonVar()
    lesson.apply_assignments_to_zombie_variables([{"variable": "zombie_speed", "value": 3}])
    assert lesson.apply_assignments_to_zombie_variables([])["variables"]["zombie_speed"] == 10


def test_boss_rejects_zero_speed():
    with pytest.raises(ValueError, match="speed must be at least 1"):
        BossLessonVar().apply_assignments_to_zombie_variables([{"variable": "zombie_speed", "value": 0}])


def test_boss_rejects_negative_speed():
    with pytest.raises(ValueError, match="speed must be at least 1"):
        BossLessonVar().apply_assignments_to_zombie_variables([{"variable": "zombie_speed", "value": -1}])


def test_zombie_alive_rejects_an_integer():
    with pytest.raises(ValueError, match="requires a value of type bool"):
        BossLessonVar().apply_assignments_to_zombie_variables([{"variable": "zombie_alive", "value": 0}])


def test_zombie_speed_rejects_a_boolean():
    with pytest.raises(ValueError, match="requires a value of type int"):
        BossLessonVar().apply_assignments_to_zombie_variables([{"variable": "zombie_speed", "value": True}])


def test_runner_updates_names_from_initial_variables():
    """The shared runner must update caller-defined variables without zombie fields."""
    result = apply_assignments_to_variables([
        {"variable": "door_open", "value": True},
        {"variable": "steps", "value": -2},
    ], {"door_open": False, "steps": 0})
    assert result["variables"] == {"door_open": True, "steps": -2}
