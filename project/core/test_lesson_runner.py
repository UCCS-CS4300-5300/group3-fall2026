import pytest

from .lesson_runner import apply_assignments_to_variables
from .lessons import BossLessonVar, JumpscareCashierLesson


def test_empty_program_keeps_the_zombie_alive_at_speed_ten():
    result = BossLessonVar().apply_assignments_to_zombie_variables([])
    assert result["variables"] == {"zombie_alive": True, "zombie_speed": 10}
    assert result["passed"] is False


def test_setting_zombie_alive_false_wins():
    assignments = [{"variable": "zombie_alive", "value": False}]
    result = BossLessonVar().apply_assignments_to_zombie_variables(assignments)
    assert result["passed"] is True
    assert result["feedback"] == "The zombie is dead. You win!"


def test_reviving_the_zombie_after_killing_it_loses():
    assignments = [
        {"variable": "zombie_alive", "value": False},
        {"variable": "zombie_alive", "value": True},
    ]
    result = BossLessonVar().apply_assignments_to_zombie_variables(assignments)
    assert result["passed"] is False
    assert result["feedback"] == "The zombie is still alive. Try again."


def test_minimum_speed_of_one_does_not_defeat_the_zombie():
    assignments = [{"variable": "zombie_speed", "value": 1}]
    result = BossLessonVar().apply_assignments_to_zombie_variables(assignments)
    assert result["variables"]["zombie_speed"] == 1
    assert result["passed"] is False


def test_speed_nine_reports_that_the_zombie_eats_you_slower():
    assignments = [{"variable": "zombie_speed", "value": 9}]
    result = BossLessonVar().apply_assignments_to_zombie_variables(assignments)
    assert result["feedback"] == "The zombie eats you slower."


def test_restoring_speed_ten_removes_the_slower_death_message():
    assignments = [
        {"variable": "zombie_speed", "value": 3},
        {"variable": "zombie_speed", "value": 10},
    ]
    result = BossLessonVar().apply_assignments_to_zombie_variables(assignments)
    assert result["feedback"] == "The zombie is still alive. Try again."


def test_zero_speed_is_rejected():
    assignments = [{"variable": "zombie_speed", "value": 0}]
    with pytest.raises(ValueError, match="speed must be at least 1"):
        BossLessonVar().apply_assignments_to_zombie_variables(assignments)


def test_negative_speed_is_rejected():
    assignments = [{"variable": "zombie_speed", "value": -1}]
    with pytest.raises(ValueError, match="speed must be at least 1"):
        BossLessonVar().apply_assignments_to_zombie_variables(assignments)


def test_zombie_alive_rejects_an_integer():
    assignments = [{"variable": "zombie_alive", "value": 0}]
    with pytest.raises(ValueError, match="requires a value of type bool"):
        BossLessonVar().apply_assignments_to_zombie_variables(assignments)


def test_zombie_speed_rejects_a_boolean():
    assignments = [{"variable": "zombie_speed", "value": True}]
    with pytest.raises(ValueError, match="requires a value of type int"):
        BossLessonVar().apply_assignments_to_zombie_variables(assignments)


def test_assignment_without_a_value_is_rejected():
    with pytest.raises(ValueError, match="variable name and a value"):
        apply_assignments_to_variables([{"variable": "steps"}], {"steps": 0})


def test_unknown_variable_is_rejected():
    assignments = [{"variable": "missing", "value": 1}]
    with pytest.raises(ValueError, match="Unknown variable"):
        apply_assignments_to_variables(assignments, {"steps": 0})


def test_program_must_be_a_list_of_assignments():
    with pytest.raises(ValueError, match="program must be a list"):
        apply_assignments_to_variables(None, {"steps": 0})


def test_running_assignments_does_not_change_the_starting_dictionary():
    starting_variables = {"steps": 0}
    apply_assignments_to_variables([{"variable": "steps", "value": 1}], starting_variables)
    assert starting_variables == {"steps": 0}


def test_assignments_keep_their_order_and_the_last_value_wins():
    assignments = [
        {"variable": "steps", "value": 3},
        {"variable": "steps", "value": 1},
    ]
    result = apply_assignments_to_variables(assignments, {"steps": 0})
    assert result["actions"] == assignments
    assert result["variables"]["steps"] == 1


def test_a_new_attempt_resets_both_zombie_variables():
    lesson = BossLessonVar()
    lesson.apply_assignments_to_zombie_variables([
        {"variable": "zombie_alive", "value": False},
        {"variable": "zombie_speed", "value": 3},
    ])
    result = lesson.apply_assignments_to_zombie_variables([])
    assert result["variables"] == {"zombie_alive": True, "zombie_speed": 10}



def cashier_program(cans, printed, price="2.50", total="cans * price"):
    return [
        {"variable": "cans", "value": cans},
        {"variable": "price", "value": price},
        {"variable": "total", "value": total},
        {"variable": "print", "value": printed},
    ]


def test_broken_cashier_program_shows_the_python_error():
    result = JumpscareCashierLesson().apply_assignments_to_zombie_variables(cashier_program('"6"', "total"))
    assert result["variables"]["output"] == "TypeError: can't multiply sequence by non-int of type 'float'"
    assert result["passed"] is False


def test_fixed_cashier_program_prints_the_total():
    result = JumpscareCashierLesson().apply_assignments_to_zombie_variables(cashier_program('int("6")', "str(total)"))
    assert result["variables"]["output"] == "Total: $15.0"
    assert result["passed"] is True


def test_wrong_cashier_operator_prints_the_wrong_total():
    program = cashier_program('int("6")', "str(total)", total="cans + price")
    result = JumpscareCashierLesson().apply_assignments_to_zombie_variables(program)
    assert result["variables"]["output"] == "Total: $8.5"
    assert result["passed"] is False


def test_unknown_cashier_option_is_rejected():
    with pytest.raises(ValueError, match="unsupported block"):
        JumpscareCashierLesson().apply_assignments_to_zombie_variables(cashier_program("7", "total"))
