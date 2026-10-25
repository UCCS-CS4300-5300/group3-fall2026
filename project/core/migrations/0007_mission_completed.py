from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0010_mission_boss_lesson_id")]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="completed",
            field=models.BooleanField(default=False),
        ),
    ]
