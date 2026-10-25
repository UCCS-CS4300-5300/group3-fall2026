from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0006_workspaces_by_room")]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="completed",
            field=models.BooleanField(default=False),
        ),
    ]
