from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from PIL import Image

from .models import Mission, RoomDefinition, RoomState
from .rooms import (
    _copy_image_without_overwriting, advance_from_current_room, create_mission,
    create_room_from_image, load_room, open_mission, save_current_room, switch_room,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def image_source(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    source = tmp_path / "original.PNG"
    Image.new("RGB", (8, 8), "blue").save(source)
    return source


def add_room(mission, source):
    return create_room_from_image(
        mission=mission, source_image_path=source, category="School",
        background_name="Chemistry Lab", tutorial_document_path="tutorials/lab.md",
    )


def test_create_room_generates_ids_copies_image_and_initializes_fields(image_source):
    mission = create_mission()
    source_bytes = image_source.read_bytes()
    room, room_state = add_room(mission, image_source)
    second_room, _ = add_room(mission, image_source)
    mission.refresh_from_db()
    assert mission.pk and room.room_id != second_room.room_id
    assert mission.first_room_id == room.room_id
    assert mission.current_room_id is None
    assert list(mission.rooms.order_by("room_id")) == [room, second_room]
    assert mission.room_states.count() == 2
    assert room.mission_id == mission.pk
    assert room.next_room_id is None
    assert room.tutorial_document_path == "tutorials/lab.md"
    assert not room_state.completed and not room_state.tutorial_read
    assert room.background_asset_path == f"core/assets/backgrounds/school-chemistry-lab-{room.room_id}.png"
    assert (image_source.parent / "core/static" / room.background_asset_path).read_bytes() == source_bytes
    assert image_source.read_bytes() == source_bytes


def test_progress_persists_across_switches_and_reopening(image_source):
    mission = create_mission()
    first_room, _ = add_room(mission, image_source)
    second_room, _ = add_room(mission, image_source)
    _, room_state = open_mission(mission_id=mission.pk)
    room_state.tutorial_read = True
    room_state.completed = True
    save_current_room(mission=mission, current_room_state=room_state)
    _, second_state = switch_room(
        mission=mission, current_room_state=room_state, destination_room_id=second_room.pk,
    )
    assert open_mission(mission_id=mission.pk)[0] == second_room
    _, restored_state = switch_room(
        mission=mission, current_room_state=second_state, destination_room_id=first_room.pk,
    )
    assert restored_state.completed and restored_state.tutorial_read
    assert RoomState.objects.count() == 2


def test_advance_follows_links_and_final_room_returns_destination_only(image_source):
    mission = create_mission()
    first_room, _ = add_room(mission, image_source)
    second_room, _ = add_room(mission, image_source)
    first_room.next_room = second_room
    first_room.save(update_fields=["next_room"])
    _, room_state = open_mission(mission_id=mission.pk)
    destination, last_state = advance_from_current_room(mission=mission, current_room_state=room_state)
    assert destination == second_room
    last_state.completed = True
    assert advance_from_current_room(mission=mission, current_room_state=last_state) == "main-menu"
    mission.refresh_from_db()
    assert mission.current_room_id is None
    reopened_room, reopened_state = open_mission(mission_id=mission.pk)
    assert reopened_room == first_room
    assert not reopened_state.completed
    assert not mission.room_states.filter(completed=True).exists()


def test_invalid_destination_rolls_back_outgoing_progress(image_source):
    mission = create_mission()
    first_room, _ = add_room(mission, image_source)
    foreign_room, _ = add_room(create_mission(), image_source)
    _, room_state = open_mission(mission_id=mission.pk)
    room_state.completed = True
    with pytest.raises(ValueError, match="belong"):
        switch_room(mission=mission, current_room_state=room_state, destination_room_id=foreign_room.pk)
    assert not RoomState.objects.get(room=first_room).completed
    mission.refresh_from_db()
    assert mission.current_room_id == first_room.pk


def test_save_rejects_state_from_another_current_room(image_source):
    mission = create_mission()
    add_room(mission, image_source)
    _, wrong_room_state = add_room(mission, image_source)
    open_mission(mission_id=mission.pk)
    with pytest.raises(ValueError, match="current room"):
        save_current_room(mission=mission, current_room_state=wrong_room_state)


def test_empty_mission_and_missing_room_state(image_source):
    mission = create_mission()
    with pytest.raises(ValueError, match="no rooms"):
        open_mission(mission_id=mission.pk)
    room, room_state = add_room(mission, image_source)
    room_state.delete()
    assert load_room(mission=mission, room_id=room.pk)[1].completed is False


def test_failed_import_rolls_back_database_and_removes_copy(image_source):
    mission = create_mission()
    with patch("core.rooms.RoomState.objects.create", side_effect=RuntimeError("failed save")):
        with pytest.raises(RuntimeError, match="failed save"):
            add_room(mission, image_source)
    assert not RoomDefinition.objects.exists()
    assert not RoomState.objects.exists()
    assert list((image_source.parent / "core/static/core/assets/backgrounds").iterdir()) == []
    mission.refresh_from_db()
    assert mission.first_room_id is None
    assert image_source.exists()


def test_existing_asset_is_never_overwritten(image_source, tmp_path):
    destination = tmp_path / "existing.png"
    destination.write_bytes(b"existing data")
    with pytest.raises(FileExistsError):
        _copy_image_without_overwriting(image_source, destination)
    assert destination.read_bytes() == b"existing data"


def test_partial_copy_is_removed(image_source, tmp_path):
    destination = tmp_path / "partial.png"
    with patch("core.rooms.shutil.copyfileobj", side_effect=OSError("copy failed")):
        with pytest.raises(OSError):
            _copy_image_without_overwriting(image_source, destination)
    assert not destination.exists()


def test_invalid_image_creates_no_room(image_source):
    image_source.write_text("not an image")
    with pytest.raises(OSError):
        add_room(create_mission(), image_source)
    assert not RoomDefinition.objects.exists()


def test_import_cannot_leave_file_in_an_outer_rolled_back_transaction(image_source):
    mission = create_mission()
    with transaction.atomic():
        with pytest.raises(RuntimeError, match="durable"):
            add_room(mission, image_source)
    assert not RoomDefinition.objects.exists()


def test_commands_create_mission_and_room_without_id_arguments(image_source):
    output = StringIO()
    call_command("create_mission", title="School", stdout=output)
    call_command(
        "add_room", mission_title="School", source_image=image_source,
        category="school", background_name="lab", tutorial_document="tutorials/lab.md", stdout=output,
    )
    mission = Mission.objects.get(title="School")
    assert mission.rooms.count() == 1
    assert "Created room" in output.getvalue()


def test_command_rejects_ambiguous_mission_title(image_source):
    create_mission(title="School")
    create_mission(title="School")
    with pytest.raises(CommandError, match="ambiguous"):
        call_command(
            "add_room", mission_title="School", source_image=image_source,
            category="school", background_name="lab", tutorial_document="tutorials/lab.md",
        )
    assert not RoomDefinition.objects.exists()


def test_model_validation_rejects_cross_mission_room_links(image_source):
    mission = create_mission()
    room, _ = add_room(mission, image_source)
    foreign_room, _ = add_room(create_mission(), image_source)
    room.next_room = foreign_room
    with pytest.raises(ValidationError):
        room.full_clean()
    mission.first_room = foreign_room
    with pytest.raises(ValidationError):
        mission.full_clean()
