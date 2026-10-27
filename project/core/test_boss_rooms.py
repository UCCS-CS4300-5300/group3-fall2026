from importlib import import_module

import pytest
from django.apps import apps
from django.urls import reverse

from .exercises import load_exercise_lessons
from .lessons import create_lesson_from_id
from .models import Mission, Puzzle, RoomDefinition, RoomState
from .room_removal import remove_content
from .rooms import advance_from_current_room, open_mission, reset_mission

pytestmark = pytest.mark.django_db

BOSS_LESSON_ID = "building1_boss"
BOSS_SOLUTION = load_exercise_lessons()[BOSS_LESSON_ID]["exercises"][0]["solution"]


@pytest.fixture
def boss_room():
    mission = Mission.objects.create(
        title="The Corner Store", description="Variables & Data Types",
        instructions="Old punch instructions", boss_lesson_id=BOSS_LESSON_ID,
    )
    room = RoomDefinition.objects.create(mission=mission, lesson_id=BOSS_LESSON_ID)
    mission.first_room = room
    mission.current_room = room
    mission.save(update_fields=["first_room", "current_room"])
    RoomState.objects.create(room=room)
    return room


@pytest.fixture
def two_room_mission():
    mission = Mission.objects.create(
        title="The Corner Store", description="Variables & Data Types", boss_lesson_id=BOSS_LESSON_ID,
    )
    # Create the final room first so placement must follow links rather than IDs.
    last = RoomDefinition.objects.create(mission=mission)
    first = RoomDefinition.objects.create(mission=mission, next_room=last)
    mission.first_room = first
    mission.current_room = first
    mission.save(update_fields=["first_room", "current_room"])
    return mission, first, last


def test_opening_a_mission_puts_the_boss_in_the_final_linked_room(two_room_mission):
    mission, first, last = two_room_mission
    open_mission(mission_id=mission.pk)
    first.refresh_from_db()
    last.refresh_from_db()
    assert first.lesson_id == ""
    assert last.lesson_id == BOSS_LESSON_ID


def test_migration_configures_the_seeded_corner_store(two_room_mission):
    mission, _, last = two_room_mission
    mission.boss_lesson_id = ""
    mission.save(update_fields=["boss_lesson_id"])
    # Migration 0015 later gives the seeded Corner Store exercise lessons, which 0010 would reject.
    Mission.objects.filter(title=mission.title).exclude(pk=mission.pk).delete()
    migration = import_module("core.migrations.0010_mission_boss_lesson_id")
    migration.configure_seeded_variables_boss(apps, None)
    last.refresh_from_db()
    assert Mission.objects.get(pk=mission.pk).boss_lesson_id == "boss_variables"
    assert last.lesson_id == "boss_variables"


def test_extending_the_route_moves_the_boss_to_the_new_final_room(boss_room):
    new_last = RoomDefinition.objects.create(mission=boss_room.mission)
    boss_room.next_room = new_last
    boss_room.save(update_fields=["next_room"])
    open_mission(mission_id=boss_room.mission_id)
    boss_room.refresh_from_db()
    new_last.refresh_from_db()
    assert boss_room.lesson_id == ""
    assert new_last.lesson_id == BOSS_LESSON_ID


def test_moving_the_boss_clears_its_old_completion_and_requirements(boss_room):
    new_last = RoomDefinition.objects.create(mission=boss_room.mission)
    boss_room.next_room = new_last
    boss_room.save(update_fields=["next_room"])
    RoomState.objects.filter(room=boss_room).update(completed=True, encounter_state={"old": True})
    open_mission(mission_id=boss_room.mission_id)
    state = RoomState.objects.get(room=boss_room)
    assert state.completed is False
    assert state.encounter_state == {}


def test_removing_the_final_room_moves_the_boss_to_the_previous_room(two_room_mission):
    mission, first, last = two_room_mission
    open_mission(mission_id=mission.pk)
    remove_content(room_id=last.pk)
    first.refresh_from_db()
    assert first.lesson_id == BOSS_LESSON_ID


def test_boss_placement_does_not_overwrite_a_different_lesson(two_room_mission):
    mission, _, last = two_room_mission
    last.lesson_id = "another_lesson"
    last.save(update_fields=["lesson_id"])
    with pytest.raises(ValueError, match="already has a different lesson"):
        open_mission(mission_id=mission.pk)
    assert RoomDefinition.objects.get(pk=last.pk).lesson_id == "another_lesson"


def test_opening_the_boss_saves_its_requirements(boss_room):
    _, state = open_mission(mission_id=boss_room.mission_id)
    assert state.encounter_state == {
        "lesson_id": BOSS_LESSON_ID, "requirements": {"exercises": ["1-boss"]},
    }


def test_refresh_preserves_the_boss_requirements(client, boss_room):
    open_mission(mission_id=boss_room.mission_id)
    saved = {"lesson_id": BOSS_LESSON_ID, "requirements": {"exercises": []}}
    RoomState.objects.filter(room=boss_room).update(encounter_state=saved)
    response = client.get(reverse("core:screen"), {"mission": boss_room.mission_id})
    assert response.status_code == 200
    assert RoomState.objects.get(room=boss_room).encounter_state == saved


def test_submission_uses_saved_requirements(client, boss_room):
    open_mission(mission_id=boss_room.mission_id)
    saved = {"lesson_id": BOSS_LESSON_ID, "requirements": {"exercises": []}}
    RoomState.objects.filter(room=boss_room).update(encounter_state=saved)
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "exercise_id": "1-boss", "code": "print(1)",
    }, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["room_completed"] is True


def test_reset_clears_boss_requirements_and_completion(boss_room):
    open_mission(mission_id=boss_room.mission_id)
    RoomState.objects.filter(room=boss_room).update(completed=True)
    reset_mission(mission=boss_room.mission)
    state = RoomState.objects.get(room=boss_room)
    assert state.encounter_state == {}
    assert state.completed is False


def test_killing_the_boss_saves_completion(client, boss_room):
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "exercise_id": "1-boss", "code": BOSS_SOLUTION,
    }, content_type="application/json")
    assert response.status_code == 200
    assert RoomState.objects.get(room=boss_room).completed is True


def test_wrong_output_does_not_save_boss_completion(client, boss_room):
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "exercise_id": "1-boss", "code": "print(1)",
    }, content_type="application/json")
    assert response.status_code == 200
    assert RoomState.objects.get(room=boss_room).completed is False


def test_a_failed_retry_keeps_previous_success(client, boss_room):
    RoomState.objects.filter(room=boss_room).update(completed=True)
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "exercise_id": "1-boss", "code": "",
    }, content_type="application/json")
    assert response.json()["passed"] is False
    assert RoomState.objects.get(room=boss_room).completed is True


def test_unsolved_boss_blocks_leaving_with_an_explanation(client, boss_room):
    response = client.post(reverse("core:next-room", args=[boss_room.mission_id]), {
        "room_id": boss_room.pk, "completed": True,
    }, follow=True)
    assert "Finish this room&#x27;s challenge before leaving.".encode() in response.content
    assert Mission.objects.get(pk=boss_room.mission_id).current_room_id == boss_room.pk


def test_an_unsaved_completion_flag_cannot_bypass_the_boss(boss_room):
    state = RoomState.objects.get(room=boss_room)
    state.completed = True
    with pytest.raises(ValueError, match="Finish this room"):
        advance_from_current_room(mission=boss_room.mission, current_room_state=state)
    assert RoomState.objects.get(room=boss_room).completed is False


def test_solved_boss_allows_finishing_the_mission(client, boss_room):
    RoomState.objects.filter(room=boss_room).update(completed=True)
    response = client.post(reverse("core:next-room", args=[boss_room.mission_id]), {"room_id": boss_room.pk})
    assert response.url == reverse("core:main-menu")
    assert Mission.objects.get(pk=boss_room.mission_id).current_room_id is None


def test_exit_and_reopen_preserve_boss_success(client, boss_room):
    RoomState.objects.filter(room=boss_room).update(completed=True)
    client.post(reverse("core:exit-mission", args=[boss_room.mission_id]))
    response = client.get(reverse("core:screen"), {"mission": boss_room.mission_id})
    assert response.context["room"] == boss_room
    assert RoomState.objects.get(room=boss_room).completed is True


def test_stale_room_submission_cannot_complete_the_boss(client, boss_room):
    Mission.objects.filter(pk=boss_room.mission_id).update(current_room=None)
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "exercise_id": "1-boss", "code": BOSS_SOLUTION,
    }, content_type="application/json")
    assert response.status_code == 400
    assert RoomState.objects.get(room=boss_room).completed is False


def test_boss_screen_shows_boss_instructions_instead_of_old_instructions(client, boss_room):
    response = client.get(reverse("core:screen"), {"mission": boss_room.mission_id})
    assert create_lesson_from_id(BOSS_LESSON_ID).instructions.encode() in response.content
    assert b"Old punch instructions" not in response.content


def test_boss_screen_hides_the_old_heading_and_solution(client, boss_room):
    Puzzle.objects.create(mission=boss_room.mission, solution="Old punch solution")
    response = client.get(reverse("core:screen"), {"mission": boss_room.mission_id})
    assert b"Variables &amp; Data Types" not in response.content
    assert b"Old punch solution" not in response.content
