import json

import pytest
from django.urls import reverse

from .lessons import load_quiz_set
from .models import Mission, RoomDefinition


@pytest.fixture
def quiz_room():
    mission = Mission.objects.create(title="The Corner Store")
    return RoomDefinition.objects.create(
        mission=mission, background_asset_path="x.jpeg", tutorial_document_path="x.md",
        exercise_set_id="building1_room1",
    )


def _submit_quiz(client, room, answers):
    return client.post(
        reverse("core:submit_quiz"),
        data=json.dumps({
            "mission_id": room.mission_id,
            "room_id": room.pk,
            "answers": answers,
        }),
        content_type="application/json",
    )


@pytest.mark.parametrize("quiz_set_id", [
    "building1_room1", "building1_room2", "building1_room3",
])
def test_quizzes_have_multiple_questions_with_four_choices_each(quiz_set_id):
    questions = load_quiz_set(quiz_set_id)["questions"]

    assert len(questions) == 5
    assert all(len(question["choices"]) == 4 for question in questions)
    assert all(0 <= question["correct_choice"] < 4 for question in questions)


def test_quiz_catalog_has_no_entries_outside_building_one():
    assert load_quiz_set("building3_room1") == {}


@pytest.mark.django_db
def test_quiz_submission_returns_completion_and_score(client, quiz_room):
    response = _submit_quiz(client, quiz_room, [0, 2, 1, 1, 3])

    assert response.status_code == 200
    assert response.json() == {"score": 5, "total": 5, "completed": True}


@pytest.mark.django_db
def test_quiz_submission_rejects_missing_answers(client, quiz_room):
    response = _submit_quiz(client, quiz_room, [0])

    assert response.status_code == 400


@pytest.mark.django_db
def test_room_without_quiz_rejects_submission(client, quiz_room):
    quiz_room.exercise_set_id = "building3_room1"
    quiz_room.save(update_fields=["exercise_set_id"])

    response = _submit_quiz(client, quiz_room, [0, 0, 0, 0, 0])

    assert response.status_code == 404