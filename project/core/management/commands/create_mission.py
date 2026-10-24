from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from core.rooms import create_mission


class Command(BaseCommand):
    help = "Create an empty mission for adding rooms. IDs are generated automatically."

    def add_arguments(self, parser):
        parser.add_argument("--title", required=True)
        parser.add_argument("--boss-lesson-id", default="", help="LessonID assigned to the final room, e.g. boss_variables.")

    def handle(self, *args, **options):
        try:
            mission = create_mission(title=options["title"], boss_lesson_id=options["boss_lesson_id"])
        except (ValidationError, ValueError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Created mission {mission.pk}: {mission.title}"))
