"""The header Exit preserves a run until a victory switches it to completion."""

from html.parser import HTMLParser
import json

import pytest
from django.urls import reverse

from .models import Mission, Puzzle, RoomDefinition, RoomState


class ExitFormParser(HTMLParser):
    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "form":
            self.form_action = attributes.get("action")
        elif tag == "button" and "exit-button" in attributes.get("class", "").split():
            self.destination = attributes.get("formaction", self.form_action)
        elif tag == "input" and attributes.get("name") == "room_id":
            self.room_id = attributes["value"]


@pytest.fixture
def boss_exit_room():
    mission = Mission.objects.create(title="Exit test", boss_lesson_id="boss_variables")
    room = RoomDefinition.objects.create(mission=mission, lesson_id="boss_variables")
    mission.first_room = mission.current_room = room
    mission.save(update_fields=["first_room", "current_room"])
    RoomState.objects.create(room=room)
    Puzzle.objects.create(mission=mission, workspace_state={})
    return room


@pytest.mark.django_db
@pytest.mark.parametrize("completed", [False, True])
def test_rendered_exit_destination_matches_saved_victory(client, boss_exit_room, completed):
    room = boss_exit_room
    RoomState.objects.filter(room=room).update(completed=completed)
    response = client.get(reverse("core:screen"), {"mission": room.mission_id})
    form = ExitFormParser()
    form.feed(response.content.decode())
    endpoint = "core:next-room" if completed else "core:exit-mission"
    assert form.destination == reverse(endpoint, args=[room.mission_id])


@pytest.mark.django_db
@pytest.mark.parametrize("completed", [False, True])
def test_rendered_exit_resets_only_after_victory(client, boss_exit_room, completed):
    room = boss_exit_room
    RoomState.objects.filter(room=room).update(completed=completed)
    response = client.get(reverse("core:screen"), {"mission": room.mission_id})
    form = ExitFormParser()
    form.feed(response.content.decode())
    workspace = {"blocks": {"languageVersion": 0, "blocks": []}}
    client.post(form.destination, {"room_id": form.room_id, "workspace_json": json.dumps(workspace)})
    mission = Mission.objects.get(pk=room.mission_id)
    saved_workspace = Puzzle.objects.get(mission=mission).workspace_state
    expected = (None, True, {}) if completed else (room.pk, False, {str(room.pk): workspace})
    assert (mission.current_room_id, mission.tutorials_unlocked, saved_workspace) == expected
