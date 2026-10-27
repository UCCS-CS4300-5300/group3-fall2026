# Room system

The room backend stores definitions and progress in the existing database. Its functions return data or the string `"main-menu"`; they do not render or navigate pages.

Generated files live in `project/gen/backgrounds/` and `project/gen/tutorials/`. Django serves this folder as static files: `gen/backgrounds/example.jpg` is stored as `backgrounds/example.jpg` and served at `/static/backgrounds/example.jpg`. The folder's generated contents are ignored by Git; mission and room records remain in the existing SQLite database.

Install `requirements.txt` and run `python manage.py migrate` before using it.

## Commands

Create an empty mission, then add one room at a time:

```text
python manage.py create_mission --title "School"
python manage.py add_room --mission-title "School" --source-image "C:/room-photos/IMG_1042.jpg" --category school --background-name chemistry-lab --tutorial-document "tutorials/chemistry-lab.md"
```

The database generates mission and room IDs. `--mission-title` selects the existing parent mission; it must match exactly one mission. The image is copied to `gen/backgrounds/` with a name such as `school-chemistry-lab-12.jpg`. The source file is preserved. The tutorial argument stores a document location; it does not import document content.

The first added room becomes the mission's first room. Each subsequent `add_room` appends to the end of its existing room chain automatically. The previous last room points to the new room, and the new last room has `next_room_id=None`. Initial progress is `tutorial_read=False` and `completed=False`. Creating rooms does not change the mission's current room.

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

# Room creation has already linked the entrance to the hallway.

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

`load_room(mission=mission, room_id=...)` returns `(RoomDefinition, RoomState)` and initializes missing room state. Exit saves the player's Python code and returns to the menu without resetting progress. `open_mission` resumes the current room and restores the saved code. Advancing from the last room using Return to Main Menu calls `reset_mission`: room completion/tutorial flags and saved code are cleared, and `current_room_id` becomes `None`, so the next entry starts at the first room. Saving and switching use the database's current room, so callers can retain the mission object returned during creation.

Mission owns its rooms through the Django `mission.rooms` related manager, and its saved states through the `mission.room_states` queryset. These are the database-backed equivalents of the collections in the planning document. Progress has no player/account dimension.

Image import commits each room independently and cannot run inside an outer database transaction. This lets it remove its copied image if the database operation fails. A future batch command can call it once per image.

Saved Python code is stored as workspace JSON (`{"code": {exercise ID: code}}`, with `""` for free code from Write Code) separately from room state in the existing `Puzzle.workspace_state` database field, keyed by room ID. Exit and Next Room save only the room being left; the destination loads its own entry, or an empty workspace on its first visit. Resetting a mission clears all of its saved workspaces. Existing snapshots from the old mission-wide format are assigned to the first room by migration 0006. Roomless missions use the key `"mission"`. The planned lesson feature will replace Puzzle and provide lesson-specific workspaces. Batch import, entity behavior, and the lesson system remain deferred.

Room and mission tests are grouped at the bottom of `core/tests.py`: creation/import, progress/reset, requests, and removal. Run `python -m pytest core/tests.py -k TestRoom` for those groups, or `python -m pytest core/tests.py` for the full file. The existing page tests expect the project's generated screen bundle (`npm run build`).


## Remove a room or mission

Run one of these from `group3-fall2026/project`:

```powershell
python manage.py remove_content --room-id 3
python manage.py remove_content --mission-title "Building 1"
python manage.py remove_content --all
```

Choose one target per call. `--all` removes every mission, room, and associated room-state record and resets both mission and room ID counters, so the next mission and room each start at ID 1. The database and migrations remain in place.

Removing a room reconnects its previous room to its next room and updates the mission's starting/current room references when needed. Removing the only room leaves an empty mission that can receive new rooms.

The command removes backgrounds and tutorial files referenced by the removed rooms from `gen/` once they are no longer used by another room. Original source images, unrelated files, and generated JavaScript bundles are retained.

To look up room IDs:

```powershell
python manage.py shell -c "from core.models import RoomDefinition; print(list(RoomDefinition.objects.values('room_id', 'mission__title', 'background_asset_path')))"
```

Recreated content receives database-generated IDs; use the main-menu buttons instead of old numeric links.
