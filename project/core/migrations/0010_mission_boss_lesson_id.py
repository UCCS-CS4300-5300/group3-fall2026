from django.db import migrations, models


def configure_seeded_variables_boss(apps, schema_editor):
    """Configure the known seeded variables mission and place its boss in the final linked room."""
    Mission = apps.get_model("core", "Mission")
    RoomDefinition = apps.get_model("core", "RoomDefinition")
    RoomState = apps.get_model("core", "RoomState")
    Puzzle = apps.get_model("core", "Puzzle")
    for mission in Mission.objects.filter(title="The Corner Store", description="Variables & Data Types"):
        room_id = mission.first_room_id
        visited_room_ids = set()
        last_room = None
        while room_id is not None:
            if room_id in visited_room_ids:
                raise ValueError("Mission room chain is invalid; cannot assign its boss.")
            visited_room_ids.add(room_id)
            last_room = RoomDefinition.objects.get(pk=room_id, mission_id=mission.pk)
            room_id = last_room.next_room_id
        mission.boss_lesson_id = "boss_variables"
        mission.save(update_fields=["boss_lesson_id"])
        if last_room is None:
            continue
        if last_room.lesson_id not in ("", "boss_variables"):
            raise ValueError("The final room already has a different lesson.")
        changed_rooms = RoomDefinition.objects.filter(mission_id=mission.pk, lesson_id="boss_variables").exclude(pk=last_room.pk)
        changed_room_ids = list(changed_rooms.values_list("pk", flat=True))
        changed_rooms.update(lesson_id="")
        if last_room.lesson_id != "boss_variables":
            last_room.lesson_id = "boss_variables"
            last_room.save(update_fields=["lesson_id"])
            changed_room_ids.append(last_room.pk)
        RoomState.objects.filter(room_id__in=changed_room_ids).update(completed=False, encounter_state={})
        for puzzle in Puzzle.objects.filter(mission_id=mission.pk):
            for changed_room_id in changed_room_ids:
                puzzle.workspace_state.pop(str(changed_room_id), None)
            puzzle.save(update_fields=["workspace_state"])


class Migration(migrations.Migration):
    dependencies = [("core", "0009_roomstate_encounter_state")]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="boss_lesson_id",
            field=models.CharField("Boss LessonID", blank=True, default="", max_length=100),
        ),
        migrations.RunPython(configure_seeded_variables_boss, migrations.RunPython.noop),
    ]
