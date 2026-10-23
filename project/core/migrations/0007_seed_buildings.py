from django.db import migrations

# Each building becomes a mission; its images become rooms in order.
# Image paths are relative to project/assets/, which is served as static files.
# can add or remove extra buildings for now its 3 rooms, 1 jumpscare, 1 boss room.
BUILDINGS = [
    ("The Corner Store", "Variables & Data Types", [
        "corner_store_room1_variables",
        "corner_store_room2_data_types",
        "corner_store_room3_operators",
        "corner_store_jumpscare_room",
        "corner_store_boss_zombie",
    ]),
    ("The Police station", "Conditionals", [
        "police_station_room1_if_else_alt",
        "police_station_room2_else_if",
        "police_station_room3_switch",
        "police_station_jumpscare_room",
        "police_station_boss_zombie",
    ]),
    ("The Laundromat", "Loops", [
        "laundromat_room1_for",
        "laundromat_room2_while",
        "laundromat_room3_do_while",
        "laundromat_boss_zombie",
        "laundromat_boss_zombie",
    ]),
    ("The Morgue", "Arrays", [
        "morgue_room1_indexing_alt",
        "morgue_room2_traversal",
        "morgue_room3_modifying",
        "morgue_jumpscare_room",
        "morgue_jumpscare_zombie",
    ]),
    ("The Radio Station", "Strings", [
        "radio_station_room1_concatenation",
        "radio_station_room2_indexing",
        "radio_station_room4_methods",
        "radio_station_jumpscare_room",
        "radio_station_boss_zombie",
    ]),
    ("The Diner", "Functions", [
        "diner_room1_define_and_call",
        "diner_room2_parameters_and_return",
        "diner_room3_scope",
        "diner_jumpscare_zombie",
        "diner_boss_zombie",
    ]),
    ("The Hotel", "Dictionaries / Maps", [
        "hotel_room1_lobby",
        "hotel_room2_stairwell",
        "hotel_room3_hallway",
        "hotel_jumpscare_room",
        "hotel_boss_zombie",
    ]),
    ("The Factory", "Classes & Objects", [
        "factory_room1_classes_and_objects",
        "factory_room2_constructors_and_methods",
        "factory_room3_inheritance",
        "factory_jumpscare_zombie",
        "factory_boss_zombie",
    ]),
    ("The Funhouse", "Recursion", [
        "funhouse_room1_base_case",
        "funhouse_room2_call_stack",
        "funhouse_room3_recursive_problems",
        "funhouse_jumpscare_zombie",
        "funhouse_boss_zombie",
    ]),
    ("The Hospital", "Searching & Sorting", [
        "hospital_room1_linear_search",
        "hospital_room2_binary_search",
        "hospital_room4_microscope_lab",
        "hospital_jumpscare_room",
        "hospital_jumpscare_zombie",
    ]),
]


def seed_buildings(apps, schema_editor):
    Mission = apps.get_model("core", "Mission")
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomState = apps.get_model("core", "RoomState")
    for title, concept, images in BUILDINGS:
        mission = Mission.objects.create(title=title, description=concept)
        previous_room = None
        for image in images:
            room = RoomDefinition.objects.create(
                mission=mission,
                background_asset_path=f"{title}/{image}.jpeg",
                tutorial_document_path=f"tutorials/{image}.md",
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
    Mission.objects.filter(title__in=[title for title, _, _ in BUILDINGS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_workspaces_by_room"),
    ]

    operations = [
        migrations.RunPython(seed_buildings, remove_buildings),
    ]
