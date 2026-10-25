from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0008_remove_mission_completed")]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="tutorials_unlocked",
            field=models.BooleanField(default=False),
        ),
    ]
