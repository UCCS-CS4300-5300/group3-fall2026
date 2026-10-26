from django.db import migrations

JUMPSCARE_ROOM = "The Corner Store/corner_store_jumpscare_room.jpeg"


def add_jumpscare(apps, schema_editor):
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomDefinition.objects.filter(background_asset_path=JUMPSCARE_ROOM).update(lesson_id="jumpscare_cashier")


def remove_jumpscare(apps, schema_editor):
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomDefinition.objects.filter(background_asset_path=JUMPSCARE_ROOM).update(lesson_id="")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_mission_tutorials_unlocked"),
    ]

    operations = [
        migrations.RunPython(add_jumpscare, remove_jumpscare),
    ]
