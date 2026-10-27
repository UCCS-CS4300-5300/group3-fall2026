from django.db import migrations

# Seeded building -> its five room images in order, each with the exercises-document LessonID it runs.
# The Radio Station has no Slicing Room image, and the Police station has no Logic Room image,
# so building5_room3 and building2_room4 are left for rooms added later.
SEEDED_ROOM_LESSONS = {
    "The Corner Store": [
        ("corner_store_room1_variables", "building1_room1"),
        ("corner_store_room2_data_types", "building1_room2"),
        ("corner_store_room3_operators", "building1_room3"),
        ("corner_store_jumpscare_room", "building1_jumpscare"),
        ("corner_store_boss_zombie", "building1_boss"),
    ],
    "The Police station": [
        ("police_station_room1_if_else_alt", "building2_room1"),
        ("police_station_room2_else_if", "building2_room2"),
        ("police_station_room3_switch", "building2_room3"),
        ("police_station_jumpscare_room", "building2_jumpscare"),
        ("police_station_boss_zombie", "building2_boss"),
    ],
    "The Laundromat": [
        ("laundromat_room1_for", "building3_room1"),
        ("laundromat_room2_while", "building3_room2"),
        ("laundromat_room3_do_while", "building3_room3"),
        ("laundromat_jumpscare_zombie", "building3_jumpscare"),
        ("laundromat_boss_zombie", "building3_boss"),
    ],
    "The Morgue": [
        ("morgue_room1_indexing_alt", "building4_room1"),
        ("morgue_room2_traversal", "building4_room2"),
        ("morgue_room3_modifying", "building4_room3"),
        ("morgue_jumpscare_room", "building4_jumpscare"),
        ("morgue_jumpscare_zombie", "building4_boss"),
    ],
    "The Radio Station": [
        ("radio_station_room1_concatenation", "building5_room1"),
        ("radio_station_room2_indexing", "building5_room2"),
        ("radio_station_room4_methods", "building5_room4"),
        ("radio_station_jumpscare_room", "building5_jumpscare"),
        ("radio_station_boss_zombie", "building5_boss"),
    ],
    "The Diner": [
        ("diner_room1_define_and_call", "building6_room1"),
        ("diner_room2_parameters_and_return", "building6_room2"),
        ("diner_room3_scope", "building6_room3"),
        ("diner_jumpscare_zombie", "building6_jumpscare"),
        ("diner_boss_zombie", "building6_boss"),
    ],
    "The Hotel": [
        ("hotel_room1_lobby", "building7_room1"),
        ("hotel_room2_stairwell", "building7_room2"),
        ("hotel_room3_hallway", "building7_room3"),
        ("hotel_jumpscare_room", "building7_jumpscare"),
        ("hotel_boss_zombie", "building7_boss"),
    ],
    "The Factory": [
        ("factory_room1_classes_and_objects", "building8_room1"),
        ("factory_room2_constructors_and_methods", "building8_room2"),
        ("factory_room3_inheritance", "building8_room3"),
        ("factory_jumpscare_zombie", "building8_jumpscare"),
        ("factory_boss_zombie", "building8_boss"),
    ],
    "The Funhouse": [
        ("funhouse_room1_base_case", "building9_room1"),
        ("funhouse_room2_call_stack", "building9_room2"),
        ("funhouse_room3_recursive_problems", "building9_room3"),
        ("funhouse_jumpscare_zombie", "building9_jumpscare"),
        ("funhouse_boss_zombie", "building9_boss"),
    ],
    "The Hospital": [
        ("hospital_room1_linear_search", "building10_room1"),
        ("hospital_room2_binary_search", "building10_room2"),
        ("hospital_room4_microscope_lab", "building10_room3"),
        ("hospital_jumpscare_room", "building10_jumpscare"),
        ("hospital_jumpscare_zombie", "building10_boss"),
    ],
}
# Lessons the Corner Store used before the exercises document, restored on reverse.
PREVIOUS_CORNER_STORE_LESSONS = {
    "corner_store_jumpscare_room": "jumpscare_cashier",
    "corner_store_boss_zombie": "boss_variables",
}


def _set_lessons(apps, lesson_for_image, boss_for_mission):
    """Set seeded rooms' LessonIDs and missions' boss LessonIDs, clearing progress in rooms that changed."""
    Mission = apps.get_model("core", "Mission")
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomState = apps.get_model("core", "RoomState")
    Puzzle = apps.get_model("core", "Puzzle")
    for title, rooms in SEEDED_ROOM_LESSONS.items():
        for mission in Mission.objects.filter(title=title):
            mission.boss_lesson_id = boss_for_mission(title, rooms)
            mission.save(update_fields=["boss_lesson_id"])
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


def assign_exercise_lessons(apps, schema_editor):
    _set_lessons(apps, lambda image, lesson_id: lesson_id, lambda title, rooms: rooms[-1][1])


def restore_previous_lessons(apps, schema_editor):
    _set_lessons(
        apps,
        lambda image, lesson_id: PREVIOUS_CORNER_STORE_LESSONS.get(image, ""),
        lambda title, rooms: "boss_variables" if title == "The Corner Store" else "",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_corner_store_jumpscare"),
    ]

    operations = [
        migrations.RunPython(assign_exercise_lessons, restore_previous_lessons),
    ]
