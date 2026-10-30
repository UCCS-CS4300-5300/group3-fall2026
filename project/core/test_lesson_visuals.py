"""Small checks that lesson image changes apply independently of room planes."""

import json

import pytest

from . import lessons
from .static.core.png_movement.png_move import load_room_floor, load_room_plane


@pytest.fixture
def lesson_catalogue(tmp_path, monkeypatch):
    catalogue = {entry["lesson_id"]: entry for entry in json.loads(lessons.EXERCISES_PATH.read_text(encoding="utf-8"))}
    path = tmp_path / "exercises.json"
    path.write_text(json.dumps(list(catalogue.values())), encoding="utf-8")
    monkeypatch.setattr(lessons, "EXERCISES_PATH", path)
    return catalogue, path


def change_first_picture(catalogue, path):
    """Change one lesson's asset reference without writing room geometry."""
    catalogue["building1_room1"]["visuals"]["sprite_asset"] = "core/png_movement/other-cat.jpg"
    path.write_text(json.dumps(list(catalogue.values())), encoding="utf-8")


def test_changing_lesson_picture_applies_to_its_room(lesson_catalogue):
    catalogue, path = lesson_catalogue
    change_first_picture(catalogue, path)
    preview = load_room_floor(987, 654, "The Corner Store/corner_store_room1_variables.jpeg", "building1_room1")

    assert preview["motion"]["sprite_asset"] == "core/png_movement/other-cat.jpg"


def test_reusing_a_lesson_picture_keeps_the_destination_plane(lesson_catalogue):
    catalogue, path = lesson_catalogue
    background = "The Police station/police_station_room1_if_else_alt.jpeg"
    destination = load_room_plane(2, 6, background, "building2_room1")
    change_first_picture(catalogue, path)
    catalogue["building2_room1"]["visuals"] = catalogue["building1_room1"]["visuals"].copy()
    path.write_text(json.dumps(list(catalogue.values())), encoding="utf-8")
    preview = load_room_floor(2, 6, background, "building2_room1")

    assert (preview["motion"]["sprite_asset"], preview["matrix"]) == (
        "core/png_movement/other-cat.jpg", destination["matrix"],
    )


def test_all_non_boss_records_have_valid_geometry_and_visuals(lesson_catalogue):
    catalogue, _ = lesson_catalogue
    placed = {reference: entry for reference, entry in catalogue.items() if "room_profile" in entry}
    assert len(placed) == 40
    for reference, entry in placed.items():
        preview = load_room_floor(987, 654, entry["room_profile"]["background_asset"], reference)
        assert preview["motion"]["duration_ms"] == entry["visuals"]["duration_ms"]
        assert preview["corners"] == tuple(tuple(point) for point in entry["room_profile"]["corners"])


def test_changed_background_keeps_lesson_picture_and_uses_default_plane(lesson_catalogue):
    catalogue, path = lesson_catalogue
    change_first_picture(catalogue, path)
    preview = load_room_floor(987, 654, "replacement.jpg", "building1_room1")
    default = load_room_plane(987, 654, "replacement.jpg")
    assert preview["matrix"] == default["matrix"]
    assert preview["motion"]["sprite_asset"] == "core/png_movement/other-cat.jpg"


def test_boss_keeps_legacy_data_without_reading_exercises(monkeypatch):
    monkeypatch.setattr(lessons, "EXERCISES_PATH", None)
    preview = load_room_floor(1, 5, "The Corner Store/corner_store_boss_zombie.jpeg")
    assert preview["motion"]["sprite_asset"] == lessons.load_lesson_visuals("corner_store_boss_zombie")["sprite_asset"]
    assert lessons.create_lesson_from_id("boss_variables").default_requirements == {"zombie_alive": False}


def test_popup_excludes_solutions_and_geometry(lesson_catalogue):
    from .views import _exercises_for

    catalogue, _ = lesson_catalogue
    exercises = _exercises_for("building1_room1")
    assert exercises[0]["task"] == catalogue["building1_room1"]["exercises"][0]["task"]
    assert "solution" not in exercises[0]
    assert "room_profile" not in exercises[0]


@pytest.mark.parametrize("reference", ["unknown", "building2_room4"])
def test_missing_or_unplaced_content_uses_defaults(reference):
    expected = load_room_floor(987, 654, "unmapped.jpg")
    assert load_room_floor(987, 654, "unmapped.jpg", reference) == expected
