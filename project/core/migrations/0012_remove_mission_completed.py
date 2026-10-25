from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0011_mission_completed")]

    operations = [
        migrations.RemoveField(
            model_name="mission",
            name="completed",
        ),
    ]
