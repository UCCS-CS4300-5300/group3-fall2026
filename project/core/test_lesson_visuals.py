"""Small checks that lesson image changes apply independently of room planes."""

import json

import pytest

from . import lessons
from .static.core.png_movement.png_move import load_room_floor, load_room_plane


@pytest.fixture
def lesson_catalogue(tmp_path, monkeypatch):
    catalogue = json.loads(lessons.LESSON_PROFILES_PATH.read_text())
    path = tmp_path / "lesson_profiles.json"
    path.write_text(json.dumps(catalogue))
    monkeypatch.setattr(lessons, "LESSON_PROFILES_PATH", path)
    return catalogue, path


def change_first_picture(catalogue, path):
    """Change one lesson's asset reference without writing room geometry."""
    reference = catalogue["placements"]["1"]["1"]
    catalogue["lessons"][reference]["sprite_asset"] = "core/png_movement/other-cat.jpg"
    path.write_text(json.dumps(catalogue))


def test_changing_lesson_picture_applies_to_its_room(lesson_catalogue):
    catalogue, path = lesson_catalogue
    change_first_picture(catalogue, path)
    preview = load_room_floor(1, 1, "The Corner Store/corner_store_room1_variables.jpeg")

    assert preview["motion"]["sprite_asset"] == "core/png_movement/other-cat.jpg"


def test_reusing_a_lesson_picture_keeps_the_destination_plane(lesson_catalogue):
    catalogue, path = lesson_catalogue
    background = "The Police station/police_station_room1_if_else_alt.jpeg"
    destination = load_room_plane(2, 6, background)
    change_first_picture(catalogue, path)
    catalogue["placements"]["2"]["6"] = catalogue["placements"]["1"]["1"]
    path.write_text(json.dumps(catalogue))
    preview = load_room_floor(2, 6, background)

    assert (preview["motion"]["sprite_asset"], preview["matrix"]) == (
        "core/png_movement/other-cat.jpg", destination["matrix"],
    )
