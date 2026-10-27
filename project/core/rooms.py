"""Room creation, saved progress, encounter initialization, and navigation."""

import shutil
from pathlib import Path
from typing import Literal

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from PIL import Image

from .lessons import create_lesson_from_id
from .models import Mission, Puzzle, RoomDefinition, RoomState


def create_mission(*, title: str = "Untitled mission", boss_lesson_id: str = "") -> Mission:
    create_lesson_from_id(boss_lesson_id)
    mission = Mission(title=title, boss_lesson_id=boss_lesson_id)
    mission.full_clean()
    mission.save()
    return mission


def load_room(*, mission: Mission, room_id: int) -> tuple[RoomDefinition, RoomState]:
    try:
        room_definition = mission.rooms.get(room_id=room_id)
    except RoomDefinition.DoesNotExist as error:
        raise ValueError("Room does not belong to this mission") from error

    room_state, _ = RoomState.objects.get_or_create(room=room_definition)
    _save_initial_room_encounter_requirements(room_definition, room_state)
    return room_definition, room_state


def _save_initial_room_encounter_requirements(room_definition: RoomDefinition, room_state: RoomState):
    """Save requirements for a lesson room once; callers hold the mission lock while loading rooms."""


    # Skip encounter setup for rooms without a lesson.
    if not room_definition.lesson_id:
        return


    # Keep the saved requirements when this room still uses the same lesson.
    if room_state.encounter_state.get("lesson_id") == room_definition.lesson_id:
        return
    lesson = create_lesson_from_id(room_definition.lesson_id)
    room_state.encounter_state = {
        "lesson_id": room_definition.lesson_id,
        "requirements": lesson.default_requirements.copy(),
    }
    room_state.save(update_fields=["encounter_state"])


def _save_current_room(mission: Mission, current_room_state: RoomState):

    if current_room_state.room_id != mission.current_room_id or mission.current_room_id is None:
        raise ValueError("Room state is not for the current room")

    if mission.current_room.mission_id != mission.pk:
        raise ValueError("Room does not belong to this mission")

    for value in (current_room_state.tutorial_read, current_room_state.completed):
        if not isinstance(value, bool):
            raise ValueError("Room progress values must be booleans")
            
    RoomState.objects.update_or_create(room_id=current_room_state.room_id,
        defaults={
            "tutorial_read": current_room_state.tutorial_read,
            "completed": current_room_state.completed,
        },
    )


def save_current_room(*, mission: Mission, current_room_state: RoomState):
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        _save_current_room(saved_mission, current_room_state)


def reset_mission(*, mission: Mission):
    """Reset progress in every room while retaining definitions and room order."""
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        saved_mission.room_states.update(tutorial_read=False, completed=False, encounter_state={})
        Puzzle.objects.filter(mission=saved_mission).update(workspace_state={})
        saved_mission.current_room = None
        saved_mission.save(update_fields=["current_room"])
    mission.current_room = None


def open_mission(*, mission_id: int) -> tuple[RoomDefinition, RoomState]:
    with transaction.atomic():
        mission = Mission.objects.select_for_update().get(pk=mission_id)
        room_id = mission.current_room_id or mission.first_room_id

        if room_id is None:
            raise ValueError("Mission has no rooms yet")

        assign_boss_lesson_to_final_room(mission)
        room_definition, room_state = load_room(mission=mission, room_id=room_id)
        mission.current_room = room_definition
        mission.save(update_fields=["current_room"])
    return room_definition, room_state


def switch_room(*, mission: Mission, current_room_state: RoomState, destination_room_id: int, ) -> tuple[RoomDefinition, RoomState]:

    with transaction.atomic():

        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        _save_current_room(saved_mission, current_room_state)

        destination_room, destination_room_state = load_room( mission=saved_mission, room_id=destination_room_id, )
        
        saved_mission.current_room = destination_room
        saved_mission.save(update_fields=["current_room"])

    mission.current_room = destination_room
    return destination_room, destination_room_state


def advance_from_current_room(*, mission: Mission, current_room_state: RoomState,) -> tuple[RoomDefinition, RoomState] | Literal["main-menu"]:
    
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)


        if (
            saved_mission.current_room_id is not None
            and saved_mission.current_room.lesson_id
            and not saved_mission.room_states.filter(room_id=saved_mission.current_room_id, completed=True).exists()
        ):
            raise ValueError("Finish this room's challenge before leaving.")
        current_room_state.tutorial_read = True
        _save_current_room(saved_mission, current_room_state)
        next_room_id = saved_mission.current_room.next_room_id
        if next_room_id is None:
            saved_mission.tutorials_unlocked = True
            saved_mission.save(update_fields=["tutorials_unlocked"])
            reset_mission(mission=mission)
            return "main-menu"

        destination_room, destination_room_state = load_room( mission=saved_mission, room_id=next_room_id,)
        saved_mission.current_room = destination_room
        saved_mission.save(update_fields=["current_room"])
    mission.current_room = destination_room
    return destination_room, destination_room_state


def _copy_image_without_overwriting(source: Path, destination: Path):
    # Exclusive creation ensures an existing asset is never replaced or removed.
    with source.open("rb") as source_file:
        destination_file = destination.open("xb")
        try:
            with destination_file:
                shutil.copyfileobj(source_file, destination_file)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise


def find_last_room_id(mission: Mission) -> int | None:
    """Return the last room ID, or None for an empty mission; reject invalid chains."""
    previous_room_id = mission.first_room_id

    if previous_room_id is not None:
        room_links = dict(mission.rooms.values_list("room_id", "next_room_id"))
        visited_room_ids = set()

        while True:
            if previous_room_id in visited_room_ids or previous_room_id not in room_links:
                raise ValueError("Mission room chain is invalid; cannot append a room")

            visited_room_ids.add(previous_room_id)
            next_room_id = room_links[previous_room_id]

            if next_room_id is None:
                break
            previous_room_id = next_room_id

    return previous_room_id


def assign_boss_lesson_to_final_room(mission: Mission):
    """Move the configured boss lesson to the final linked room while the caller holds the mission lock."""


    # Skip automatic placement for missions without a configured boss lesson.
    if not mission.boss_lesson_id:
        return
    create_lesson_from_id(mission.boss_lesson_id)
    last_room_id = find_last_room_id(mission)


    # Wait until the mission has a room in which to place the boss.
    if last_room_id is None:
        return
    last_room = mission.rooms.get(pk=last_room_id)


    if last_room.lesson_id not in ("", mission.boss_lesson_id):
        raise ValueError("The final room already has a different lesson.")
    previous_boss_rooms = mission.rooms.filter(lesson_id=mission.boss_lesson_id).exclude(pk=last_room_id)
    changed_room_ids = list(previous_boss_rooms.values_list("pk", flat=True))
    previous_boss_rooms.update(lesson_id="")


    # Assign the boss lesson when the final room does not already have it.
    if last_room.lesson_id != mission.boss_lesson_id:
        last_room.lesson_id = mission.boss_lesson_id
        last_room.save(update_fields=["lesson_id"])
        changed_room_ids.append(last_room_id)


    # Clear saved attempts only for rooms whose lesson changed.
    if changed_room_ids:
        _clear_saved_progress_for_changed_lessons(mission, changed_room_ids)


def _clear_saved_progress_for_changed_lessons(mission: Mission, room_ids: list[int]):
    """Clear completion, encounter requirements, and saved code for rooms whose lessons changed."""
    mission.room_states.filter(room_id__in=room_ids).update(completed=False, encounter_state={})
    puzzle = Puzzle.objects.filter(mission=mission).first()


    # Remove the changed rooms' saved blocks when the mission has a puzzle.
    if puzzle is not None:
        for room_id in room_ids:
            puzzle.workspace_state.pop(str(room_id), None)
        puzzle.save(update_fields=["workspace_state"])


def create_room_from_image(
    *,
    mission: Mission,
    source_image_path: Path,
    category: str,
    background_name: str,
    tutorial_document_path: str, 

    ) -> tuple[RoomDefinition, RoomState]:

    source_image_path = Path(source_image_path)

    with Image.open(source_image_path) as image:
        image.verify()
    with Image.open(source_image_path) as image:
        image.load()
        if Image.registered_extensions().get(source_image_path.suffix.lower()) != image.format:
            raise ValueError("Image filename extension does not match its format")

    category_part = slugify(category)
    background_part = slugify(background_name)

    if not category_part or not background_part:
        raise ValueError("Category and background name must contain letters or numbers")

    if not tutorial_document_path.strip():
        raise ValueError("A tutorial document path is required")

    background_folder = Path(settings.BASE_DIR) / "gen/backgrounds"
    copied_image_path = None
    try:
        # Commit here: a later outer rollback could otherwise leave an orphan image.
        with transaction.atomic(durable=True):
            saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
            previous_room_id = find_last_room_id(saved_mission)

            room_definition = RoomDefinition.objects.create(
                mission=saved_mission,
                background_asset_path="",
                tutorial_document_path=tutorial_document_path,
                lesson_id=saved_mission.boss_lesson_id,
            )

            image_filename = (
                f"{category_part}-{background_part}-{room_definition.room_id}"
                f"{source_image_path.suffix.lower()}"
            )

            room_definition.background_asset_path = f"backgrounds/{image_filename}"
            room_definition.full_clean()
            background_folder.mkdir(parents=True, exist_ok=True)

            destination = background_folder / image_filename
            _copy_image_without_overwriting(source_image_path, destination)
            copied_image_path = destination

            room_definition.save(update_fields=["background_asset_path"])
            room_state = RoomState.objects.create(room=room_definition)
            
            if saved_mission.first_room_id is None:
                saved_mission.first_room = room_definition
                saved_mission.save(update_fields=["first_room"])
            else:
                RoomDefinition.objects.filter(pk=previous_room_id).update(next_room=room_definition)
            assign_boss_lesson_to_final_room(saved_mission)
    except BaseException:
        if copied_image_path is not None:
            copied_image_path.unlink(missing_ok=True)
        raise

    mission.first_room_id = saved_mission.first_room_id
    return room_definition, room_state
