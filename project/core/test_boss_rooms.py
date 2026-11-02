from importlib import import_module

import pytest
from django.apps import apps
from django.urls import reverse

from .lessons import BossLessonVar
from .models import Mission, RoomDefinition, RoomState
from .room_removal import remove_content
from .rooms import open_mission, reset_mission

pytestmark = pytest.mark.django_db


@pytest.fixture
def boss_room():
    mission = Mission.objects.create(
        title="The Corner Store", description="Variables & Data Types",
        instructions="Old punch instructions", boss_lesson_id="boss_variables",
    )
    room = RoomDefinition.objects.create(mission=mission, lesson_id="boss_variables")
    mission.first_room = room
    mission.current_room = room
    mission.save(update_fields=["first_room", "current_room"])
    RoomState.objects.create(room=room)
    return room


@pytest.fixture
def two_room_mission():
    mission = Mission.objects.create(
        title="The Corner Store", description="Variables & Data Types", boss_lesson_id="boss_variables",
    )
    # Create the final room first so placement must follow links rather than IDs.
    last = RoomDefinition.objects.create(mission=mission)
    first = RoomDefinition.objects.create(mission=mission, next_room=last)
    mission.first_room = first
    mission.current_room = first
    mission.save(update_fields=["first_room", "current_room"])
    return mission, first, last


def test_original_punch_program_still_works(client):
    response = client.post(reverse("core:check_program"), {
        "program": "if zombie\n  punch zombie",
    }, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["punched"] is True


def test_opening_a_mission_puts_the_boss_in_the_final_linked_room(two_room_mission):
    mission, first, last = two_room_mission
    open_mission(mission_id=mission.pk)
    first.refresh_from_db()
    last.refresh_from_db()
    assert first.lesson_id == ""
    assert last.lesson_id == "boss_variables"


def test_migration_configures_the_seeded_corner_store(two_room_mission):
    mission, _, last = two_room_mission
    mission.boss_lesson_id = ""
    mission.save(update_fields=["boss_lesson_id"])
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
    assert new_last.lesson_id == "boss_variables"


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
    assert first.lesson_id == "boss_variables"


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
        "lesson_id": "boss_variables", "requirements": {"zombie_alive": False},
    }


def test_refresh_preserves_the_boss_requirements(client, boss_room, monkeypatch):
    _, state = open_mission(mission_id=boss_room.mission_id)
    monkeypatch.setattr(BossLessonVar, "default_requirements", {"zombie_alive": True})
    response = client.get(reverse("core:screen"), {"mission": boss_room.mission_id})
    assert response.status_code == 200
    assert RoomState.objects.get(room=boss_room).encounter_state == state.encounter_state


def test_submission_uses_saved_requirements(client, boss_room, monkeypatch):
    open_mission(mission_id=boss_room.mission_id)
    monkeypatch.setattr(BossLessonVar, "default_requirements", {"zombie_alive": True})
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk,
        "assignments": [{"variable": "zombie_alive", "value": False}],
    }, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_reset_clears_boss_requirements_and_completion(boss_room):
    open_mission(mission_id=boss_room.mission_id)
    RoomState.objects.filter(room=boss_room).update(completed=True)
    reset_mission(mission=boss_room.mission)
    state = RoomState.objects.get(room=boss_room)
    assert state.encounter_state == {}
    assert state.completed is False


def test_killing_the_boss_saves_completion(client, boss_room):
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk,
        "assignments": [{"variable": "zombie_alive", "value": False}],
    }, content_type="application/json")
    assert response.status_code == 200
    assert RoomState.objects.get(room=boss_room).completed is True


def test_slowing_the_boss_does_not_save_completion(client, boss_room):
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk,
        "assignments": [{"variable": "zombie_speed", "value": 3}],
    }, content_type="application/json")
    assert response.status_code == 200
    assert RoomState.objects.get(room=boss_room).completed is False


def test_a_failed_retry_keeps_previous_success(client, boss_room):
    RoomState.objects.filter(room=boss_room).update(completed=True)
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "assignments": [],
    }, content_type="application/json")
    assert response.json()["passed"] is False
    assert RoomState.objects.get(room=boss_room).completed is True


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


def test_zero_speed_submission_returns_a_clear_error(client, boss_room):
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk,
        "assignments": [{"variable": "zombie_speed", "value": 0}],
    }, content_type="application/json")
    assert response.status_code == 400
    assert response.json()["error"] == "Zombie speed must be at least 1."


def test_stale_room_submission_cannot_complete_the_boss(client, boss_room):
    Mission.objects.filter(pk=boss_room.mission_id).update(current_room=None)
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk,
        "assignments": [{"variable": "zombie_alive", "value": False}],
    }, content_type="application/json")
    assert response.status_code == 400
    assert RoomState.objects.get(room=boss_room).completed is False


def test_invalid_program_cannot_save_partial_success(client, boss_room):
    assignments = [{"variable": "zombie_alive", "value": False}, {"variable": "missing", "value": 1}]
    response = client.post(reverse("core:check_program"), {
        "mission_id": boss_room.mission_id, "room_id": boss_room.pk, "assignments": assignments,
    }, content_type="application/json")
    assert response.status_code == 400
    assert RoomState.objects.get(room=boss_room).completed is False
