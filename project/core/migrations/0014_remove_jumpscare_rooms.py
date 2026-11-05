from django.db import migrations, models


def remove_jumpscare_rooms(apps, schema_editor):
    """Keep each building's jumpscare exercise on its mission, then unlink and delete the jumpscare room."""
    Mission = apps.get_model("core", "Mission")
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    Puzzle = apps.get_model("core", "Puzzle")
    for room in RoomDefinition.objects.filter(exercise_set_id__endswith="_jumpscare"):
        mission = Mission.objects.get(pk=room.mission_id)
        mission.jumpscare_exercise_set_id = room.exercise_set_id
        RoomDefinition.objects.filter(next_room_id=room.pk).update(next_room_id=room.next_room_id)
        if mission.first_room_id == room.pk:
            mission.first_room_id = room.next_room_id
        if mission.current_room_id == room.pk:
            mission.current_room_id = room.next_room_id or mission.first_room_id
        mission.save(update_fields=["jumpscare_exercise_set_id", "first_room", "current_room"])
        for puzzle in Puzzle.objects.filter(mission_id=mission.pk):
            puzzle.workspace_state.pop(str(room.pk), None)
            puzzle.save(update_fields=["workspace_state"])
        room.delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0013_mission_tutorials_unlocked")]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="jumpscare_exercise_set_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.RunPython(remove_jumpscare_rooms, migrations.RunPython.noop),
    ]
