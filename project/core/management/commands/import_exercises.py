import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.exercise_doc import parse_exercise_document
from core.exercises import EXERCISES_PATH


class Command(BaseCommand):
    help = "Read the Python exercises Word document and rewrite core/exercises.json."

    def add_arguments(self, parser):
        parser.add_argument("docx", type=Path, help="Path to 'Zombie Python Exercises for Every Room.docx'.")

    def handle(self, *args, **options):
        try:
            lessons = parse_exercise_document(options["docx"])
        except (OSError, KeyError, ValueError) as error:
            raise CommandError(str(error)) from error
        EXERCISES_PATH.write_text(json.dumps(lessons, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        count = sum(len(lesson["exercises"]) for lesson in lessons)
        self.stdout.write(self.style.SUCCESS(f"Wrote {count} exercises in {len(lessons)} lessons to {EXERCISES_PATH}"))
