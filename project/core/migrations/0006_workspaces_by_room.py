from django.db import migrations


def separate_workspaces(apps, schema_editor):
    Puzzle = apps.get_model('core', 'Puzzle')
    puzzles = Puzzle.objects.using(schema_editor.connection.alias).select_related('mission')
    for puzzle in puzzles.iterator():
        if puzzle.workspace_state:
            # The old format did not record a room. Preserve that work in the first room.
            room_id = puzzle.mission.first_room_id
            key = str(room_id) if room_id is not None else 'mission'
            puzzle.workspace_state = {key: puzzle.workspace_state}
            puzzle.save(using=schema_editor.connection.alias, update_fields=['workspace_state'])


def combine_workspaces(apps, schema_editor):
    Puzzle = apps.get_model('core', 'Puzzle')
    puzzles = Puzzle.objects.using(schema_editor.connection.alias).select_related('mission')
    for puzzle in puzzles.iterator():
        room_id = puzzle.mission.first_room_id
        key = str(room_id) if room_id is not None else 'mission'
        puzzle.workspace_state = puzzle.workspace_state.get(key, {})
        puzzle.save(using=schema_editor.connection.alias, update_fields=['workspace_state'])


class Migration(migrations.Migration):
    dependencies = [('core', '0005_puzzle_workspace_state')]

    operations = [migrations.RunPython(separate_workspaces, combine_workspaces)]
