from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from core.rooms import create_mission


class Command(BaseCommand):
    help = "Create an empty mission for adding rooms. IDs are generated automatically."

    def add_arguments(self, parser):
        parser.add_argument("--title", required=True)

    def handle(self, *args, **options):
        try:
            mission = create_mission(title=options["title"])
        except ValidationError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Created mission {mission.pk}: {mission.title}"))
