# Room planes and lesson pictures

`mission_<id>_floor_profiles.json` contains room-owned data:

- Mission/room identity and background image identity.
- Four floor corners in normalized original-image coordinates.
- `path.start_image` and `path.end_image` for the approach on that plane.

`core/lessons.py` retains existing lesson behavior and supplies visual-setting lookup.
The existing `core/lesson_runner.py` continues to apply typed variable assignments.
Its `core/data/lesson_profiles.json` contains the authored presentation records:

- `sprite_asset`: independently selectable image for that lesson.
- `foot_anchor`: fraction of sprite width/height used to attach its feet.
- `end_height`: final sprite height as a fraction of original background height.
- `duration_ms`: approach duration, currently 2500 ms.

All 50 current room activities have separate lesson presentation records, initially
referencing the existing `core/png_movement/cat.jpg`. The image file is shared;
each lesson's choice is independent. To change one lesson's picture, change only
its `sprite_asset` entry. Add the replacement image under this feature's static
asset directory and use its `core/png_movement/...` static path.

The catalogue's `placements` maps mission ID and room ID to a lesson reference:

```json
{
  "placements": {
    "1": {
      "1": "corner_store_room1_variables",
      "4": "corner_store_jumpscare_room"
    }
  }
}
```

These are explicit content references, chosen once from the activity names.
They are not inferred from the background filename at runtime. A lesson can be
placed in another room by referencing the same record there; it will use that
destination room's plane and path. Plane coordinates are never stored on lessons.

`playback` in the lesson catalogue contains the agreed gameplay settings: speed
1–20 with normal speed 10, 500 ms of visible approach before an instant success
can trigger death, and an 80-degree clockwise rotation around the feet.

Gameplay movement is enabled only in a mission's last room (`next_room_id` is
empty). Other rooms retain their complete authored profiles but receive no active
preview payload. Their default movement controller accepts the same calls and
does nothing. Run therefore needs no room-specific enabled checks.

Run starts movement locally before sending the program request. A passing lesson
or successful legacy punch rotates the sprite at its current position after the
visibility minimum. A failed lesson continues to the endpoint. Server-reported
speed changes affect future progress without teleporting the sprite. Reset,
navigation, and a newer attempt invalidate older translation responses. Network or
program-validation errors cancel motion and leave Run available to retry.

`load_room_plane(mission_id, room_id, background_asset)` returns just the prepared
plane and image-space path. `load_room_floor(...)` composes those values with the
placed lesson's presentation to retain the current browser preview payload.
Rooms without a matching plane profile use the default plane/path; placements
without a lesson reference independently use the default presentation. A changed
background falls back to the default plane while keeping its placed lesson image.

These presentation records are separate from the existing database `lesson_id`
behavior selector (`boss_variables`, `jumpscare_cashier`, or blank). No lesson
database identity is changed by the data separation. This is not the planned
database Lesson/placement migration.
