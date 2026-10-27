import json
from importlib import import_module

import pytest
from django.apps import apps
from django.urls import reverse

from . import code_runner
from .code_runner import outputs_match, run_python
from .exercises import ExerciseLesson, load_exercise_lessons
from .lessons import create_lesson_from_id
from .models import Mission, RoomDefinition, RoomState
from .rooms import advance_from_current_room

ALL_EXERCISES = [exercise for lesson in load_exercise_lessons().values() for exercise in lesson["exercises"]]


def test_document_has_every_exercise():
    lessons = load_exercise_lessons()
    assert len(ALL_EXERCISES) == 74
    assert sum(lesson["kind"] == "room" for lesson in lessons.values()) == 32
    assert sum(lesson["kind"] == "jumpscare" for lesson in lessons.values()) == 10
    # Boss rooms keep their own lessons, so the document has none.
    assert len(lessons) == 42


@pytest.mark.parametrize("exercise", ALL_EXERCISES, ids=lambda exercise: exercise["id"])
def test_reference_solution_prints_the_expected_output(exercise):
    result = run_python(exercise["solution"])
    assert result["error"] == ""
    assert outputs_match(result["output"], exercise["expected_output"])


@pytest.mark.parametrize(
    "exercise", [exercise for exercise in ALL_EXERCISES if exercise["kind"] == "jumpscare"],
    ids=lambda exercise: exercise["id"],
)
def test_jumpscare_broken_code_raises_the_documented_error(exercise):
    result = run_python(exercise["starting_code"])
    assert result["error"].strip().splitlines()[-1] == exercise["error_shown"]


def test_outputs_match_ignores_trailing_spaces_and_blank_lines():
    assert outputs_match("a  \nb\n\n", "a\nb")
    assert not outputs_match("a\nc", "a\nb")


def test_runner_stops_a_loop_that_never_ends(monkeypatch):
    monkeypatch.setattr(code_runner, "TIME_LIMIT_SECONDS", 1)
    result = run_python("print('start')\nwhile True:\n    pass")
    assert "more than 1 seconds" in result["error"]


def test_runner_reports_system_exit_without_stopping():
    result = run_python("print('before')\nraise SystemExit(3)")
    assert result["output"] == "before\n"
    assert "SystemExit: 3" in result["error"]


def test_runner_reports_final_values_of_starting_variables():
    result = run_python("print(speed)\nspeed = speed - 4", {"speed": 10, "alive": True})
    assert result == {"output": "10\n", "error": "", "variables": {"speed": 6, "alive": True}}


def test_the_document_has_no_boss_lessons():
    with pytest.raises(ValueError, match="Unknown LessonID"):
        create_lesson_from_id("building1_boss")


def test_public_exercises_have_no_timer():
    lesson = create_lesson_from_id("building1_jumpscare")
    assert "timer" not in lesson.instructions
    assert all("timer_seconds" not in exercise for exercise in lesson.public_exercises())


def test_exercise_lesson_ids_create_exercise_lessons():
    lesson = create_lesson_from_id("building1_room1")
    assert isinstance(lesson, ExerciseLesson)
    assert lesson.default_requirements == {"exercises": ["1.1", "1.2"]}
    assert all("solution" not in exercise for exercise in lesson.public_exercises())


@pytest.fixture
def variables_room():
    mission = Mission.objects.create(title="The Corner Store")
    room = RoomDefinition.objects.create(mission=mission, lesson_id="building1_room1")
    mission.first_room = mission.current_room = room
    mission.save(update_fields=["first_room", "current_room"])
    RoomState.objects.create(room=room)
    return room


def _check(client, room, exercise_id, code):
    return client.post(reverse("core:check_program"), {
        "code": code, "exercise_id": exercise_id, "mission_id": room.mission_id, "room_id": room.pk,
    }, content_type="application/json")


def _solution(exercise_id):
    return next(exercise["solution"] for exercise in ALL_EXERCISES if exercise["id"] == exercise_id)


@pytest.mark.django_db
class TestExerciseRequests:
    def test_free_code_runs_without_a_room(self, client):
        response = client.post(reverse("core:check_program"), {"code": "print(6 * 7)"}, content_type="application/json")
        assert response.json() == {"output": "42\n", "error": ""}

    def test_screen_lists_room_objects_without_solutions(self, client, variables_room):
        response = client.get(reverse("core:screen"), {"mission": variables_room.mission_id})
        assert b"Survivor ID Card" in response.content
        assert b"A bloodstained ID badge under the register." in response.content
        assert b'hometown = \\"Riverside\\"' not in response.content

    def test_solving_every_exercise_completes_the_room(self, client, variables_room):
        first = _check(client, variables_room, "1.1", _solution("1.1")).json()
        assert first["passed"] is True and first["room_completed"] is False
        assert RoomState.objects.get(room=variables_room).completed is False

        second = _check(client, variables_room, "1.2", _solution("1.2")).json()
        assert second["passed"] is True and second["room_completed"] is True
        state = RoomState.objects.get(room=variables_room)
        assert state.completed is True
        assert state.encounter_state["solved"] == ["1.1", "1.2"]
        assert advance_from_current_room(mission=variables_room.mission, current_room_state=state) == "main-menu"

    def test_wrong_output_does_not_solve_the_exercise(self, client, variables_room):
        result = _check(client, variables_room, "1.1", 'print("Name: Maya")').json()
        assert result["passed"] is False
        assert "doesn't match" in result["feedback"]
        assert "solved" not in RoomState.objects.get(room=variables_room).encounter_state or \
            RoomState.objects.get(room=variables_room).encounter_state["solved"] == []

    def test_crashing_code_reports_the_traceback(self, client, variables_room):
        result = _check(client, variables_room, "1.1", "print(name)").json()
        assert result["passed"] is False
        assert "NameError: name 'name' is not defined" in result["error"]

    def test_exercise_from_another_room_is_rejected(self, client, variables_room):
        response = _check(client, variables_room, "1.3", _solution("1.3"))
        assert response.status_code == 400

    def test_unfinished_room_blocks_the_next_room(self, variables_room):
        state = RoomState.objects.get(room=variables_room)
        with pytest.raises(ValueError, match="Finish this room"):
            advance_from_current_room(mission=variables_room.mission, current_room_state=state)


@pytest.mark.django_db
def test_migration_assigns_exercise_lessons_to_seeded_rooms():
    mission = Mission.objects.create(title="The Corner Store")
    images = ["corner_store_room1_variables", "corner_store_jumpscare_room", "corner_store_boss_zombie"]
    rooms = [
        RoomDefinition.objects.create(mission=mission, background_asset_path=f"The Corner Store/{image}.jpeg")
        for image in images
    ]
    rooms[1].lesson_id = "jumpscare_cashier"
    rooms[1].save(update_fields=["lesson_id"])
    RoomState.objects.create(room=rooms[1], completed=True, encounter_state={"lesson_id": "jumpscare_cashier"})

    migration = import_module("core.migrations.0015_python_exercise_lessons")
    migration.assign_exercise_lessons(apps, None)

    # The boss room keeps its own lesson instead of the exercises document's boss.
    assert [RoomDefinition.objects.get(pk=room.pk).lesson_id for room in rooms] == [
        "building1_room1", "building1_jumpscare", "",
    ]
    assert RoomState.objects.get(room=rooms[1]).completed is False
    # Every LessonID the migration assigns exists in the exercises file.
    for room_lessons in migration.SEEDED_ROOM_LESSONS.values():
        for _, lesson_id in room_lessons:
            assert lesson_id in load_exercise_lessons()
