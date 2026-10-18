from django.db import migrations


def rewrite_paths(apps, replacements):
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    for room in RoomDefinition.objects.all().iterator():
        changed = []
        for field, old_prefix, new_prefix in replacements:
            value = getattr(room, field)
            if value.startswith(old_prefix):
                setattr(room, field, new_prefix + value[len(old_prefix):])
                changed.append(field)
        if changed:
            room.save(update_fields=changed)


def forwards(apps, schema_editor):
    rewrite_paths(apps, [
        ("background_asset_path", "core/assets/backgrounds/", "backgrounds/"),
        ("tutorial_document_path", "core/tutorials/", "tutorials/"),
    ])


def backwards(apps, schema_editor):
    rewrite_paths(apps, [
        ("background_asset_path", "backgrounds/", "core/assets/backgrounds/"),
        ("tutorial_document_path", "tutorials/", "core/tutorials/"),
    ])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_roomdefinition_roomstate_mission_current_room_and_more"),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
