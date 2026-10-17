# Room system

The room backend stores definitions and progress in the existing database. Its functions return data or the string `"main-menu"`; they do not render or navigate pages.

Install `requirements.txt` and run `python manage.py migrate` before using it.

## Commands

Create an empty mission, then add one room at a time:

```text
python manage.py create_mission --title "School"
python manage.py add_room --mission-title "School" --source-image "C:/room-photos/IMG_1042.jpg" --category school --background-name chemistry-lab --tutorial-document "tutorials/chemistry-lab.md"
```

The database generates mission and room IDs. `--mission-title` selects the existing parent mission; it must match exactly one mission. The image is copied to `core/static/core/assets/backgrounds/` with a name such as `school-chemistry-lab-12.jpg`. The source file is preserved. The tutorial argument stores a document location; it does not import document content.

The first added room becomes the mission's first room. Each new room has `next_room_id=None`, `tutorial_read=False`, and `completed=False`. Creating rooms does not change the mission's current room.

## Python functions

Functions are in `core.rooms`:

```python
from pathlib import Path
from core.rooms import (
    create_mission, create_room_from_image, open_mission,
    save_current_room, switch_room, advance_from_current_room,
)

mission = create_mission(title="School")
first_room, first_room_state = create_room_from_image(
    mission=mission,
    source_image_path=Path("C:/room-photos/entrance.jpg"),
    category="school",
    background_name="entrance",
    tutorial_document_path="tutorials/entrance.md",
)
second_room, second_room_state = create_room_from_image(
    mission=mission,
    source_image_path=Path("C:/room-photos/hallway.jpg"),
    category="school",
    background_name="hallway",
    tutorial_document_path="tutorials/hallway.md",
)

# Link rooms once their generated IDs are available.
first_room.next_room = second_room
first_room.full_clean()
first_room.save(update_fields=["next_room"])

current_room, current_room_state = open_mission(mission_id=mission.pk)
current_room_state.tutorial_read = True
save_current_room(mission=mission, current_room_state=current_room_state)

current_room, current_room_state = switch_room(
    mission=mission,
    current_room_state=current_room_state,
    destination_room_id=second_room.room_id,
)
destination = advance_from_current_room(
    mission=mission, current_room_state=current_room_state,
)  # "main-menu" because the second room has no next room.
```

`load_room(mission=mission, room_id=...)` returns `(RoomDefinition, RoomState)` and initializes missing room state. `open_mission` resumes the current room during a mission. Exit and advancing from the last room call `reset_mission`: all room completion/tutorial flags are cleared and `current_room_id` becomes `None`, so the next entry starts at the first room. Saving and switching use the database's current room, so callers can retain the mission object returned during creation.

Mission owns its rooms through the Django `mission.rooms` related manager, and its saved states through the `mission.room_states` queryset. These are the database-backed equivalents of the collections in the planning document. Progress has no player/account dimension.

Image import commits each room independently and cannot run inside an outer database transaction. This lets it remove its copied image if the database operation fails. A future batch command can call it once per image.

Batch import, entity behavior, lessons, and lesson-owned Blockly snapshots are deferred. Existing Puzzle and mission-generation behavior is retained.

Run `pytest core/test_rooms.py` for backend tests. The full existing suite also expects the project's generated Blockly bundles (`npm run build`).

