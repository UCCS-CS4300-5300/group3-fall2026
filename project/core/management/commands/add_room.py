from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from core.models import Mission
from core.rooms import create_room_from_image


class Command(BaseCommand):
    help = "Copy one background image and create a room in an existing mission."

    def add_arguments(self, parser):
        parser.add_argument("--mission-title", required=True)
        parser.add_argument("--source-image", required=True, type=Path)
        parser.add_argument("--category", required=True)
        parser.add_argument("--background-name", required=True)
        parser.add_argument("--tutorial-document", required=True)

    def handle(self, *args, **options):
        try:
            mission = Mission.objects.get(title=options["mission_title"])
        except Mission.DoesNotExist as error:
            raise CommandError("Mission title was not found. Create the mission first.") from error
        except Mission.MultipleObjectsReturned as error:
            raise CommandError("Mission title is ambiguous. Use a distinct mission title.") from error
        try:
            room_definition, _ = create_room_from_image(
                mission=mission,
                source_image_path=options["source_image"],
                category=options["category"],
                background_name=options["background_name"],
                tutorial_document_path=options["tutorial_document"],
            )
        except (OSError, ValueError, ValidationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(
            f"Created room {room_definition.room_id}: {room_definition.background_asset_path}"
        ))
