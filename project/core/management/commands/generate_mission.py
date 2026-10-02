from django.core.management.base import BaseCommand

from core.mission_generator import generate_mission


class Command(BaseCommand):
    help = "Ask a local Ollama model to write a new mission and save it to the database."

    def add_arguments(self, parser):
        parser.add_argument("topic", nargs="?", default="", help='What the mission should teach, e.g. "while loops"')

    def handle(self, *args, **options):
        mission = generate_mission(options["topic"])
        self.stdout.write(self.style.SUCCESS(f"Created mission {mission.pk}: {mission.title}"))
