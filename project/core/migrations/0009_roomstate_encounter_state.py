from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0008_roomdefinition_lesson_id")]

    operations = [
        migrations.AddField(
            model_name="roomstate",
            name="encounter_state",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
