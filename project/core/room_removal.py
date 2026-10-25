"""Remove room content while preserving the remaining room chain and shared files."""

from pathlib import Path

from django.conf import settings
from django.core.management.color import no_style
from django.db import connection, transaction
from django.db.models import Q, QuerySet

from .models import Mission, RoomDefinition
from .rooms import assign_boss_lesson_to_final_room


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


def room_remove_single(room_id: int) -> set[str]:
    """Remove one room within the caller's transaction and return its file paths."""
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
    assign_boss_lesson_to_final_room(mission)
    return paths


def _remove_missions_with_rooms(missions: QuerySet[Mission]) -> tuple[int, int, set[str]]:
    """Delete selected missions and return counts and file paths for cleanup."""
    mission_ids = list(missions.values_list("pk", flat=True))
    rooms = RoomDefinition.objects.filter(mission_id__in=mission_ids)
    paths = {path for pair in rooms.values_list(
        "background_asset_path", "tutorial_document_path"
    ) for path in pair}
    removed_missions, removed_rooms = len(mission_ids), rooms.count()
    Mission.objects.filter(pk__in=mission_ids).delete()
    return removed_missions, removed_rooms, paths


def single_mission_with_rooms_removal(mission_title: str) -> tuple[int, int, set[str]]:
    """Remove one mission and its rooms within the caller's transaction."""
    mission = Mission.objects.select_for_update().get(title=mission_title)
    missions = Mission.objects.filter(pk=mission.pk)
    return _remove_missions_with_rooms(missions)


def remove_content(
    *, room_id: int | None = None, mission_title: str | None = None,
    remove_all: bool = False,
) -> tuple[int, int]:
    """Return (missions removed, rooms removed). Generated files are cleaned after commit."""
    if sum((room_id is not None, mission_title is not None, remove_all)) != 1:
        raise ValueError("Choose exactly one room, mission, or all content")

    with transaction.atomic():

        #Checks if a single room is provided for removal
        if room_id is not None:
            paths = room_remove_single(room_id)
            removed_missions, removed_rooms = 0, 1

        #Checks if a single mission is provided for removal
        elif mission_title is not None:
            removed_missions, removed_rooms, paths = single_mission_with_rooms_removal(mission_title)

        #The remaining valid choice is to remove all missions and their rooms
        else:
            missions = Mission.objects.select_for_update().all()
            removed_missions, removed_rooms, paths = _remove_missions_with_rooms(missions)
            statements = connection.ops.sequence_reset_by_name_sql(
                no_style(),
                [
                    {"table": model._meta.db_table, "column": model._meta.pk.column}
                    for model in (Mission, RoomDefinition)
                ],
            )
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

        transaction.on_commit(lambda: _remove_unused_generated_files(paths))
    return removed_missions, removed_rooms
