from django.core.management.base import BaseCommand, CommandError

from core.models import Mission, RoomDefinition
from core.room_removal import remove_content


class Command(BaseCommand):
    help = "Remove a room, a mission, or all mission/room content, including unused generated files."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument("--room-id", type=int)
        target.add_argument("--mission-title")
        target.add_argument("--all", action="store_true", dest="remove_all")

    def handle(self, *args, **options):
        try:
            mission_count, room_count = remove_content(
                room_id=options["room_id"], mission_title=options["mission_title"],
                remove_all=options["remove_all"],
            )
        except RoomDefinition.DoesNotExist as error:
            raise CommandError("Room ID was not found.") from error
        except Mission.DoesNotExist as error:
            raise CommandError("Mission title was not found.") from error
        except Mission.MultipleObjectsReturned as error:
            raise CommandError("Mission title is ambiguous. Use a distinct mission title.") from error
        except ValueError as error:
            raise CommandError(str(error)) from error
        except OSError as error:
            raise CommandError(f"Records were removed, but generated-file cleanup failed: {error}") from error
        self.stdout.write(self.style.SUCCESS(
            f"Removed {mission_count} mission(s) and {room_count} room(s)."
        ))
