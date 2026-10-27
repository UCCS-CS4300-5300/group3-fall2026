"""Lesson lookup by LessonID, separate from database models."""

from .exercises import ExerciseLesson, load_exercise_lessons


def create_lesson_from_id(lesson_id: str):
    """Return a lesson instance for its ID, None for a blank ID, or raise ValueError for an unknown ID."""
    if lesson_id == "":
        return None
    # Every room, Jumpscare and Boss in the exercises document has its own LessonID.
    exercise_lessons = load_exercise_lessons()
    if lesson_id in exercise_lessons:
        return ExerciseLesson(exercise_lessons[lesson_id])
    raise ValueError(f"Unknown LessonID: {lesson_id}")
