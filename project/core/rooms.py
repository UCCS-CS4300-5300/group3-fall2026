"""Room creation, persistence, and navigation; no page or lesson behavior."""

import shutil
from pathlib import Path
from typing import Literal

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from PIL import Image

from .models import Mission, RoomDefinition, RoomState


def create_mission(*, title: str = "Untitled mission") -> Mission:
    mission = Mission(title=title)
    mission.full_clean()
    mission.save()
    return mission


def load_room(*, mission: Mission, room_id: int) -> tuple[RoomDefinition, RoomState]:
    try:
        room_definition = mission.rooms.get(room_id=room_id)
    except RoomDefinition.DoesNotExist as error:
        raise ValueError("Room does not belong to this mission") from error
    room_state, _ = RoomState.objects.get_or_create(room=room_definition)
    return room_definition, room_state


def _save_current_room(mission: Mission, current_room_state: RoomState) -> None:
    if current_room_state.room_id != mission.current_room_id or mission.current_room_id is None:
        raise ValueError("Room state is not for the current room")
    if mission.current_room.mission_id != mission.pk:
        raise ValueError("Room does not belong to this mission")
    for value in (current_room_state.tutorial_read, current_room_state.completed):
        if not isinstance(value, bool):
            raise ValueError("Room progress values must be booleans")
    RoomState.objects.update_or_create(
        room_id=current_room_state.room_id,
        defaults={
            "tutorial_read": current_room_state.tutorial_read,
            "completed": current_room_state.completed,
        },
    )


def save_current_room(*, mission: Mission, current_room_state: RoomState) -> None:
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        _save_current_room(saved_mission, current_room_state)


def reset_mission(*, mission: Mission) -> None:
    """Reset progress in every room while retaining definitions and room order."""
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        saved_mission.room_states.update(tutorial_read=False, completed=False)
        saved_mission.current_room = None
        saved_mission.save(update_fields=["current_room"])
    mission.current_room = None


def open_mission(*, mission_id: int) -> tuple[RoomDefinition, RoomState]:
    with transaction.atomic():
        mission = Mission.objects.select_for_update().get(pk=mission_id)
        room_id = mission.current_room_id or mission.first_room_id
        if room_id is None:
            raise ValueError("Mission has no rooms yet")
        room_definition, room_state = load_room(mission=mission, room_id=room_id)
        mission.current_room = room_definition
        mission.save(update_fields=["current_room"])
    return room_definition, room_state


def switch_room(
    *, mission: Mission, current_room_state: RoomState, destination_room_id: int,
) -> tuple[RoomDefinition, RoomState]:
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        _save_current_room(saved_mission, current_room_state)
        destination_room, destination_room_state = load_room(
            mission=saved_mission, room_id=destination_room_id,
        )
        saved_mission.current_room = destination_room
        saved_mission.save(update_fields=["current_room"])
    mission.current_room = destination_room
    return destination_room, destination_room_state


def advance_from_current_room(
    *, mission: Mission, current_room_state: RoomState,
) -> tuple[RoomDefinition, RoomState] | Literal["main-menu"]:
    with transaction.atomic():
        saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
        _save_current_room(saved_mission, current_room_state)
        next_room_id = saved_mission.current_room.next_room_id
        if next_room_id is None:
            reset_mission(mission=mission)
            return "main-menu"
        destination_room, destination_room_state = load_room(
            mission=saved_mission, room_id=next_room_id,
        )
        saved_mission.current_room = destination_room
        saved_mission.save(update_fields=["current_room"])
    mission.current_room = destination_room
    return destination_room, destination_room_state


def _copy_image_without_overwriting(source: Path, destination: Path) -> None:
    # Exclusive creation ensures an existing asset is never replaced or removed.
    with source.open("rb") as source_file:
        destination_file = destination.open("xb")
        try:
            with destination_file:
                shutil.copyfileobj(source_file, destination_file)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise


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

    background_folder = Path(settings.BASE_DIR) / "core/static/core/assets/backgrounds"
    copied_image_path = None
    try:
        # Commit here: a later outer rollback could otherwise leave an orphan image.
        with transaction.atomic(durable=True):
            saved_mission = Mission.objects.select_for_update().get(pk=mission.pk)
            room_definition = RoomDefinition.objects.create(
                mission=saved_mission,
                background_asset_path="",
                tutorial_document_path=tutorial_document_path,
            )
            image_filename = (
                f"{category_part}-{background_part}-{room_definition.room_id}"
                f"{source_image_path.suffix.lower()}"
            )
            room_definition.background_asset_path = f"core/assets/backgrounds/{image_filename}"
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
    except BaseException:
        if copied_image_path is not None:
            copied_image_path.unlink(missing_ok=True)
        raise

    mission.first_room_id = saved_mission.first_room_id
    return room_definition, room_state
