# Floor calibration and lesson pictures

Non-boss room geometry and lesson visuals now live alongside their exercises in
`core/exercises/exercises.json` under `room_profile` and `visuals`.
Select those records using `RoomDefinition.exercise_set_id`, not database IDs.

`mission_<id>_floor_profiles.json` retains only each mission's existing boss
geometry: background identity, normalized floor corners, and image-space path.
Boss picture choices and placements remain in `core/data/lesson_profiles.json`,
alongside default visuals and shared playback settings. Boss callers continue
using the same mission/room IDs and existing loader signatures.

`png_move_floor.json` is the fallback plane/path. A background identity mismatch
uses this fallback while retaining the selected lesson's picture settings.
`png_move_projection_fixture.json` is the projection test reference.

`load_room_plane(...)` returns geometry and a path. `load_room_floor(...)`
composes those with picture settings and validates the resulting movement.
Non-boss callers pass `exercise_set_id`; boss callers omit it.

Movement remains enabled only in the final linked room. Run, reset, speed
bounds, minimum visible time, death rotation, and gameplay evaluation are
unchanged by the storage move. Executable behavior still uses the database
`lesson_id` selector (`boss_variables`, `jumpscare_cashier`, or blank).
