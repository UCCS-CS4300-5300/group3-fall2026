from django.db import migrations

# Seeded building -> its room images in order, each with the exercises-document LessonID it runs.
# Boss rooms are left out: they keep their own lessons (the Corner Store boss stays "boss_variables").
# The Radio Station has no Slicing Room image, and the Police station has no Logic Room image,
# so building5_room3 and building2_room4 are left for rooms added later.
SEEDED_ROOM_LESSONS = {
    "The Corner Store": [
        ("corner_store_room1_variables", "building1_room1"),
        ("corner_store_room2_data_types", "building1_room2"),
        ("corner_store_room3_operators", "building1_room3"),
        ("corner_store_jumpscare_room", "building1_jumpscare"),
    ],
    "The Police station": [
        ("police_station_room1_if_else_alt", "building2_room1"),
        ("police_station_room2_else_if", "building2_room2"),
        ("police_station_room3_switch", "building2_room3"),
        ("police_station_jumpscare_room", "building2_jumpscare"),
    ],
    "The Laundromat": [
        ("laundromat_room1_for", "building3_room1"),
        ("laundromat_room2_while", "building3_room2"),
        ("laundromat_room3_do_while", "building3_room3"),
        ("laundromat_jumpscare_zombie", "building3_jumpscare"),
    ],
    "The Morgue": [
        ("morgue_room1_indexing_alt", "building4_room1"),
        ("morgue_room2_traversal", "building4_room2"),
        ("morgue_room3_modifying", "building4_room3"),
        ("morgue_jumpscare_room", "building4_jumpscare"),
    ],
    "The Radio Station": [
        ("radio_station_room1_concatenation", "building5_room1"),
        ("radio_station_room2_indexing", "building5_room2"),
        ("radio_station_room4_methods", "building5_room4"),
        ("radio_station_jumpscare_room", "building5_jumpscare"),
    ],
    "The Diner": [
        ("diner_room1_define_and_call", "building6_room1"),
        ("diner_room2_parameters_and_return", "building6_room2"),
        ("diner_room3_scope", "building6_room3"),
        ("diner_jumpscare_zombie", "building6_jumpscare"),
    ],
    "The Hotel": [
        ("hotel_room1_lobby", "building7_room1"),
        ("hotel_room2_stairwell", "building7_room2"),
        ("hotel_room3_hallway", "building7_room3"),
        ("hotel_jumpscare_room", "building7_jumpscare"),
    ],
    "The Factory": [
        ("factory_room1_classes_and_objects", "building8_room1"),
        ("factory_room2_constructors_and_methods", "building8_room2"),
        ("factory_room3_inheritance", "building8_room3"),
        ("factory_jumpscare_zombie", "building8_jumpscare"),
    ],
    "The Funhouse": [
        ("funhouse_room1_base_case", "building9_room1"),
        ("funhouse_room2_call_stack", "building9_room2"),
        ("funhouse_room3_recursive_problems", "building9_room3"),
        ("funhouse_jumpscare_zombie", "building9_jumpscare"),
    ],
    "The Hospital": [
        ("hospital_room1_linear_search", "building10_room1"),
        ("hospital_room2_binary_search", "building10_room2"),
        ("hospital_room4_microscope_lab", "building10_room3"),
        ("hospital_jumpscare_room", "building10_jumpscare"),
    ],
}
# Lessons the Corner Store used before the exercises document, restored on reverse.
PREVIOUS_CORNER_STORE_LESSONS = {
    "corner_store_jumpscare_room": "jumpscare_cashier",
}


def _set_lessons(apps, lesson_for_image):
    """Set seeded rooms' LessonIDs, clearing progress and saved code in rooms that changed."""
    Mission = apps.get_model("core", "Mission")
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomState = apps.get_model("core", "RoomState")
    Puzzle = apps.get_model("core", "Puzzle")
    for title, rooms in SEEDED_ROOM_LESSONS.items():
        for mission in Mission.objects.filter(title=title):
            changed_room_ids = []
            for image, lesson_id in rooms:
                new_lesson_id = lesson_for_image(image, lesson_id)
                for room in RoomDefinition.objects.filter(mission=mission, background_asset_path=f"{title}/{image}.jpeg"):
                    if room.lesson_id != new_lesson_id:
                        room.lesson_id = new_lesson_id
                        room.save(update_fields=["lesson_id"])
                        changed_room_ids.append(room.pk)
            RoomState.objects.filter(room_id__in=changed_room_ids).update(completed=False, encounter_state={})
            for puzzle in Puzzle.objects.filter(mission=mission):
                for room_id in changed_room_ids:
                    puzzle.workspace_state.pop(str(room_id), None)
                puzzle.save(update_fields=["workspace_state"])


def _reset_boss_rooms(apps):
    """Boss requirements now list the boss exercise, so saved boss attempts start over."""
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomState = apps.get_model("core", "RoomState")
    boss_room_ids = RoomDefinition.objects.filter(lesson_id="boss_variables").values_list("pk", flat=True)
    RoomState.objects.filter(room_id__in=list(boss_room_ids)).update(completed=False, encounter_state={})


def assign_exercise_lessons(apps, schema_editor):
    _set_lessons(apps, lambda image, lesson_id: lesson_id)
    _reset_boss_rooms(apps)


def restore_previous_lessons(apps, schema_editor):
    _set_lessons(apps, lambda image, lesson_id: PREVIOUS_CORNER_STORE_LESSONS.get(image, ""))
    _reset_boss_rooms(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_corner_store_jumpscare"),
    ]

    operations = [
        migrations.RunPython(assign_exercise_lessons, restore_previous_lessons),
    ]
