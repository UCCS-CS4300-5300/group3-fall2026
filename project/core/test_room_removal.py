from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction

from .models import Mission, RoomDefinition, RoomState
from .room_removal import remove_content

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def room_content(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    mission = Mission.objects.create(title="Building")
    rooms = []
    for index in range(3):
        room = RoomDefinition.objects.create(
            mission=mission, background_asset_path=f"backgrounds/room-{index}.jpg",
            tutorial_document_path=f"tutorials/room-{index}.md",
        )
        RoomState.objects.create(room=room)
        for path in (room.background_asset_path, room.tutorial_document_path):
            generated_file = tmp_path / "gen" / path
            generated_file.parent.mkdir(parents=True, exist_ok=True)
            generated_file.write_text("test content")
        if rooms:
            rooms[-1].next_room = room
            rooms[-1].save()
        rooms.append(room)
    mission.first_room = rooms[0]
    mission.current_room = rooms[1]
    mission.save()
    return mission, rooms, tmp_path


@pytest.mark.parametrize('index', [0, 1, 2])
def test_remove_room_repairs_chain_and_removes_state_and_files(room_content, index):
    mission, rooms, root = room_content
    removed = rooms[index]
    removed_id = removed.pk
    expected_ids = [room.pk for room in rooms if room.pk != removed_id]
    assert remove_content(room_id=removed_id) == (0, 1)
    mission.refresh_from_db()
    assert mission.first_room_id == expected_ids[0]
    assert mission.current_room_id in expected_ids
    current = mission.first_room
    visited = []
    while current:
        visited.append(current.pk)
        current = current.next_room
    assert visited == expected_ids
    assert not RoomState.objects.filter(room_id=removed_id).exists()
    assert not (root / 'gen' / removed.background_asset_path).exists()
    assert not (root / 'gen' / removed.tutorial_document_path).exists()


def test_remove_only_room_keeps_empty_mission(room_content):
    mission, rooms, _ = room_content
    for room in rooms:
        remove_content(room_id=room.pk)
    mission.refresh_from_db()
    assert mission.first_room_id is None
    assert mission.current_room_id is None
    assert not mission.rooms.exists()


def test_remove_mission_preserves_other_missions_and_shared_documents(room_content):
    mission, rooms, root = room_content
    other_mission = Mission.objects.create(title="Other")
    shared_document = rooms[0].tutorial_document_path
    RoomDefinition.objects.create(
        mission=other_mission, background_asset_path="backgrounds/other.jpg",
        tutorial_document_path=shared_document,
    )
    assert remove_content(mission_title=mission.title) == (1, 3)
    assert Mission.objects.filter(pk=other_mission.pk).exists()
    assert (root / 'gen' / shared_document).exists()
    assert not RoomState.objects.exists()


def test_remove_all_cleans_referenced_files_but_keeps_unrelated_data(room_content):
    _, _, root = room_content
    unrelated = root / 'gen/backgrounds/not-imported.jpg'
    unrelated.write_text('unreferenced file')
    assert remove_content(remove_all=True) == (1, 3)
    assert not Mission.objects.exists()
    assert not RoomDefinition.objects.exists()
    assert not RoomState.objects.exists()
    assert list((root / 'gen/backgrounds').iterdir()) == [unrelated]


def test_removal_never_deletes_files_outside_generated_folder(room_content):
    mission, rooms, root = room_content
    original = root / 'original.jpg'
    original.write_text('source image')
    rooms[0].background_asset_path = 'backgrounds/../../original.jpg'
    rooms[0].save()
    remove_content(mission_title=mission.title)
    assert original.read_text() == 'source image'


def test_rollback_keeps_database_and_generated_files(room_content):
    mission, rooms, root = room_content
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            remove_content(mission_title=mission.title)
            raise RuntimeError('rollback')
    assert mission.rooms.count() == 3
    assert (root / 'gen' / rooms[0].background_asset_path).exists()


def test_command_targets_and_missing_content(room_content):
    mission, rooms, _ = room_content
    output = StringIO()
    call_command('remove_content', room_id=rooms[1].pk, stdout=output)
    assert '1 room(s)' in output.getvalue()
    with pytest.raises(CommandError, match='not found'):
        call_command('remove_content', room_id=rooms[1].pk)
    call_command('remove_content', mission_title=mission.title, stdout=output)
    call_command('remove_content', remove_all=True, stdout=output)
    assert not Mission.objects.exists()
