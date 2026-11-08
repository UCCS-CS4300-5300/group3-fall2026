import json

import pytest
from django.urls import reverse

from .code_runner import run_python
from .models import Mission, RoomDefinition


def test_run_python_returns_printed_output():
    assert run_python('print("hi")') == {"output": "hi\n", "error": ""}


def test_run_python_reports_error_with_line_number():
    assert "NameError on line 2" in run_python("x = 1\nprint(y)")["error"]


def test_run_python_reports_syntax_error():
    assert run_python('print("a"')["error"].startswith("SyntaxError on line 1")


def test_run_python_stops_endless_loop():
    assert run_python("while True: pass")["error"] != ""


def test_run_python_hides_server_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "do-not-leak")
    assert "do-not-leak" not in run_python("import os; print(os.environ)")["output"]


@pytest.fixture
def exercise_room():
    mission = Mission.objects.create(title="Corner Store")
    return RoomDefinition.objects.create(
        mission=mission, background_asset_path="x.jpeg", tutorial_document_path="x.md",
        exercise_set_id="building1_room1",
    )


def _post_exercise(client, room, code, exercise_id="1.1"):
    return client.post(
        reverse("core:run_exercise"),
        data=json.dumps({
            "mission_id": room.mission_id, "room_id": room.pk,
            "exercise_id": exercise_id, "code": code,
        }),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_room_with_exercises_renders_quiz_button(client, exercise_room):
    mission = exercise_room.mission
    next_room = RoomDefinition.objects.create(
        mission=mission, background_asset_path="next.jpeg", tutorial_document_path="next.md",
    )
    exercise_room.next_room = next_room
    exercise_room.save(update_fields=["next_room"])
    mission.first_room = exercise_room
    mission.save(update_fields=["first_room"])

    response = client.get(reverse("core:screen"), {"mission": mission.pk})

    assert response.status_code == 200
    assert b'id="quiz-button"' in response.content
    assert b'id="quiz-popup"' in response.content


@pytest.mark.django_db
def test_run_exercise_passes_matching_output(client, exercise_room):
    code = (
        'name = "Maya Reyes"\nage = 27\nhometown = "Riverside"\n'
        'print("Name:", name)\nprint("Age:", age)\nprint("Hometown:", hometown)'
    )
    result = _post_exercise(client, exercise_room, code).json()
    assert result["passed"] is True
    assert result["error"] == ""


@pytest.mark.django_db
def test_run_exercise_fails_wrong_output(client, exercise_room):
    result = _post_exercise(client, exercise_room, 'print("Name: Bob")').json()
    assert result["passed"] is False
    assert result["output"] == "Name: Bob\n"


@pytest.mark.django_db
def test_run_exercise_rejects_exercise_from_another_room(client, exercise_room):
    response = _post_exercise(client, exercise_room, 'print("hi")', exercise_id="9.9")
    assert response.status_code == 404
