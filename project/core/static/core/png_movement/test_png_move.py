"""Focused checks for room wiring, authored paths, and one projection reference."""

import json
from pathlib import Path

import pytest
from django.urls import reverse

from core.models import Mission, RoomDefinition
from core.lessons import load_exercise_set, load_lesson_visuals
from .png_move import load_floor, prepare_floor, prepare_motion, project_point

FIXTURE = json.loads(
    (Path(__file__).parent / "jstests" / "png_move_projection_fixture.json").read_text()
)


def configuration(corners):
    """Build a version-1 configuration from normalized image corners."""
    return {"version": 1, "coordinate_space": "normalized_image", "corners": corners}


@pytest.fixture
def known_floor():
    return prepare_floor(configuration(FIXTURE["corners"]))


@pytest.fixture
def motion_setup():
    config = load_exercise_set("settings")["default"]["room_profile"]
    config["motion"] = {**config["path"], **load_lesson_visuals()}
    floor = prepare_floor(config)
    motion = prepare_motion(config["motion"], floor)

    return config, floor, motion


def test_solves_known_matrix(known_floor):
    assert known_floor["matrix"] == pytest.approx(FIXTURE["matrix"])


@pytest.fixture
def room_response(db, client):
    mission = Mission.objects.create(title="Floor review")
    room = RoomDefinition.objects.create(mission=mission, background_asset_path="room.jpg")
    mission.first_room = room
    mission.save()

    return client.get(reverse("core:screen"), {"mission": mission.pk})


def test_room_receives_prepared_floor(room_response):
    assert room_response.context["floor_config"] == load_floor()


@pytest.mark.django_db
@pytest.mark.parametrize("final_room", [False, True], ids=["ordinary-room", "final-room"])
def test_movement_is_available_only_in_final_room(client, final_room):
    mission = Mission.objects.create(title="Movement placement")
    tail = RoomDefinition.objects.create(mission=mission, background_asset_path="tail.jpg")
    first = tail if final_room else RoomDefinition.objects.create(
        mission=mission, background_asset_path="first.jpg", next_room=tail,
    )
    mission.first_room = first
    mission.save()
    response = client.get(reverse("core:screen"), {"mission": mission.pk})

    assert response.context["movement_config"]["enabled"] is final_room


def test_room_renders_the_lesson_picture(room_response):
    assert "/static/core/png_movement/cat.jpg" in room_response.content.decode()


@pytest.fixture
def no_mission_response(db, client):
    Mission.objects.all().delete()

    return client.get(reverse("core:screen"))


def test_no_mission_page_omits_floor(no_mission_response):
    assert 'id="png-move-floor"' not in no_mission_response.content.decode()


@pytest.fixture
def roomless_response(db, client):
    mission = Mission.objects.create(title="No room")

    return client.get(reverse("core:screen"), {"mission": mission.pk})


def test_roomless_mission_has_no_configuration(roomless_response):
    assert roomless_response.context["floor_config"] is None


@pytest.mark.parametrize("endpoint", ["start", "end"])
def test_prepared_endpoint_matches_image_configuration(motion_setup, endpoint):
    config, floor, motion = motion_setup
    actual = project_point(floor["matrix"], motion[f"{endpoint}_floor"])

    assert actual == pytest.approx(config["motion"][f"{endpoint}_image"])


def test_rejects_shrinking_approach(motion_setup):
    config, floor, _ = motion_setup
    motion = {
        **config["motion"],
        "start_image": config["motion"]["end_image"],
        "end_image": config["motion"]["start_image"],
    }

    with pytest.raises(ValueError):
        prepare_motion(motion, floor)
