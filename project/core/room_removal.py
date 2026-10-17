"""Remove room content while preserving the remaining room chain and shared files."""

from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from .models import Mission, RoomDefinition


def _remove_unused_generated_files(paths: set[str]) -> None:
    generated_root = (Path(settings.BASE_DIR) / "gen").resolve()
    for stored_path in paths:
        if not stored_path.startswith(("backgrounds/", "tutorials/")):
            continue
        file_path = (generated_root / stored_path).resolve()
        if not file_path.is_relative_to(generated_root):
            continue
        if RoomDefinition.objects.filter(
            Q(background_asset_path=stored_path) | Q(tutorial_document_path=stored_path)
        ).exists():
            continue
        file_path.unlink(missing_ok=True)


def remove_content(
    *, room_id: int | None = None, mission_title: str | None = None,
    remove_all: bool = False,
) -> tuple[int, int]:
    """Return (missions removed, rooms removed). Generated files are cleaned after commit."""
    if sum((room_id is not None, mission_title is not None, remove_all)) != 1:
        raise ValueError("Choose exactly one room, mission, or all content")

    with transaction.atomic():
        if room_id is not None:
            room = RoomDefinition.objects.get(pk=room_id)
            mission = Mission.objects.select_for_update().get(pk=room.mission_id)
            successor_id = room.next_room_id if room.next_room_id != room.pk else None
            if successor_id is not None and not mission.rooms.filter(pk=successor_id).exists():
                raise ValueError("Next room does not belong to this mission")
            paths = {room.background_asset_path, room.tutorial_document_path}
            mission.rooms.filter(next_room_id=room.pk).exclude(pk=room.pk).update(next_room_id=successor_id)
            if mission.first_room_id == room.pk:
                mission.first_room_id = successor_id
            if mission.current_room_id == room.pk:
                mission.current_room_id = successor_id or mission.first_room_id
            mission.save(update_fields=["first_room", "current_room"])
            room.delete()
            removed_missions, removed_rooms = 0, 1
        else:
            if remove_all:
                missions = Mission.objects.select_for_update().all()
            else:
                mission = Mission.objects.select_for_update().get(title=mission_title)
                missions = Mission.objects.filter(pk=mission.pk)
            mission_ids = list(missions.values_list("pk", flat=True))
            rooms = RoomDefinition.objects.filter(mission_id__in=mission_ids)
            paths = {path for pair in rooms.values_list(
                "background_asset_path", "tutorial_document_path"
            ) for path in pair}
            removed_missions, removed_rooms = len(mission_ids), rooms.count()
            Mission.objects.filter(pk__in=mission_ids).delete()

        transaction.on_commit(lambda: _remove_unused_generated_files(paths))
    return removed_missions, removed_rooms
