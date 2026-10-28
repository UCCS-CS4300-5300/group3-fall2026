from django.db import migrations, models

# Each building becomes a mission; its images become rooms in order.
# Image paths are relative to project/assets/, which is served as static files.
# Each room is (image, exercises.json lesson_id, LessonID); blank IDs mean none.
# Exercise sets are matched by room position, since some building names differ in exercises.json.
BUILDINGS = [
    ("The Corner Store", "Variables & Data Types", "boss_variables", [
        ("corner_store_room1_variables", "building1_room1", ""),
        ("corner_store_room2_data_types", "building1_room2", ""),
        ("corner_store_room3_operators", "building1_room3", ""),
        ("corner_store_jumpscare_room", "building1_jumpscare", "jumpscare_cashier"),
        ("corner_store_boss_zombie", "", "boss_variables"),
    ]),
    ("The Police station", "Conditionals", "", [
        ("police_station_room1_if_else_alt", "building2_room1", ""),
        ("police_station_room2_else_if", "building2_room2", ""),
        ("police_station_room3_switch", "building2_room3", ""),
        ("police_station_jumpscare_room", "building2_jumpscare", ""),
        ("police_station_boss_zombie", "", ""),
    ]),
    ("The Laundromat", "Loops", "", [
        ("laundromat_room1_for", "building3_room1", ""),
        ("laundromat_room2_while", "building3_room2", ""),
        ("laundromat_room3_do_while", "building3_room3", ""),
        ("laundromat_jumpscare_zombie", "building3_jumpscare", ""),
        ("laundromat_boss_zombie", "", ""),
    ]),
    ("The Morgue", "Arrays", "", [
        ("morgue_room1_indexing_alt", "building4_room1", ""),
        ("morgue_room2_traversal", "building4_room2", ""),
        ("morgue_room3_modifying", "building4_room3", ""),
        ("morgue_jumpscare_room", "building4_jumpscare", ""),
        ("morgue_jumpscare_zombie", "", ""),
    ]),
    ("The Radio Station", "Strings", "", [
        ("radio_station_room1_concatenation", "building5_room1", ""),
        ("radio_station_room2_indexing", "building5_room2", ""),
        ("radio_station_room4_methods", "building5_room4", ""),
        ("radio_station_jumpscare_room", "building5_jumpscare", ""),
        ("radio_station_boss_zombie", "", ""),
    ]),
    ("The Diner", "Functions", "", [
        ("diner_room1_define_and_call", "building6_room1", ""),
        ("diner_room2_parameters_and_return", "building6_room2", ""),
        ("diner_room3_scope", "building6_room3", ""),
        ("diner_jumpscare_zombie", "building6_jumpscare", ""),
        ("diner_boss_zombie", "", ""),
    ]),
    ("The Hotel", "Dictionaries / Maps", "", [
        ("hotel_room1_lobby", "building7_room1", ""),
        ("hotel_room2_stairwell", "building7_room2", ""),
        ("hotel_room3_hallway", "building7_room3", ""),
        ("hotel_jumpscare_room", "building7_jumpscare", ""),
        ("hotel_boss_zombie", "", ""),
    ]),
    ("The Factory", "Classes & Objects", "", [
        ("factory_room1_classes_and_objects", "building8_room1", ""),
        ("factory_room2_constructors_and_methods", "building8_room2", ""),
        ("factory_room3_inheritance", "building8_room3", ""),
        ("factory_jumpscare_zombie", "building8_jumpscare", ""),
        ("factory_boss_zombie", "", ""),
    ]),
    ("The Funhouse", "Recursion", "", [
        ("funhouse_room1_base_case", "building9_room1", ""),
        ("funhouse_room2_call_stack", "building9_room2", ""),
        ("funhouse_room3_recursive_problems", "building9_room3", ""),
        ("funhouse_jumpscare_zombie", "building9_jumpscare", ""),
        ("funhouse_boss_zombie", "", ""),
    ]),
    ("The Hospital", "Searching & Sorting", "", [
        ("hospital_room1_linear_search", "building10_room1", ""),
        ("hospital_room2_binary_search", "building10_room2", ""),
        ("hospital_room4_microscope_lab", "building10_room3", ""),
        ("hospital_jumpscare_room", "building10_jumpscare", ""),
        ("hospital_jumpscare_zombie", "", ""),
    ]),
]


def seed_buildings(apps, schema_editor):
    Mission = apps.get_model("core", "Mission")
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomState = apps.get_model("core", "RoomState")
    for title, concept, boss_lesson_id, rooms in BUILDINGS:
        mission = Mission.objects.create(title=title, description=concept, boss_lesson_id=boss_lesson_id)
        previous_room = None
        for image, exercise_set_id, lesson_id in rooms:
            room = RoomDefinition.objects.create(
                mission=mission,
                background_asset_path=f"{title}/{image}.jpeg",
                tutorial_document_path=f"tutorials/{image}.md",
                lesson_id=lesson_id,
                exercise_set_id=exercise_set_id,
            )
            RoomState.objects.create(room=room)
            if previous_room is None:
                mission.first_room = room
                mission.save(update_fields=["first_room"])
            else:
                previous_room.next_room = room
                previous_room.save(update_fields=["next_room"])
            previous_room = room


def remove_buildings(apps, schema_editor):
    Mission = apps.get_model("core", "Mission")
    Mission.objects.filter(title__in=[title for title, _, _, _ in BUILDINGS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_workspaces_by_room"),
    ]

    operations = [
        migrations.AddField(
            model_name="roomdefinition",
            name="lesson_id",
            field=models.CharField("LessonID", blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="mission",
            name="boss_lesson_id",
            field=models.CharField("Boss LessonID", blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="roomdefinition",
            name="exercise_set_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.RunPython(seed_buildings, remove_buildings),
    ]
