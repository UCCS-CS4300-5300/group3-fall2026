from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0007_seed_buildings")]

    operations = [
        migrations.AddField(
            model_name="roomdefinition",
            name="lesson_id",
            field=models.CharField("LessonID", blank=True, default="", max_length=100),
        ),
    ]
