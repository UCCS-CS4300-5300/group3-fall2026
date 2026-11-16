"""Lesson behavior, block choices, and room/picture data associations."""

import json
from pathlib import Path



EXERCISES_PATH = Path(__file__).parent / "exercises" / "exercises.json"
QUIZZES_PATH = Path(__file__).parent / "exercises" / "quizzes.json"
ROOM_DATA_PATH = Path(__file__).parent / "exercises" / "room_data.json"
BOSSES_PATH = Path(__file__).parent / "exercises" / "bosses.json"

"""Return exercise content selected by lesson_id."""
def load_exercise_set(exercise_set_id):

    if not exercise_set_id:
        return {}
    with EXERCISES_PATH.open(encoding="utf-8") as file:
        sets = {entry["lesson_id"]: entry for entry in json.load(file)}
    return sets.get(exercise_set_id, {})


def load_quiz_set(quiz_set_id):
    """Return quiz content selected by a room's exercise_set_id."""
    if not quiz_set_id:
        return {}
    with QUIZZES_PATH.open(encoding="utf-8") as file:
        sets = {entry["lesson_id"]: entry for entry in json.load(file)}
    return sets.get(quiz_set_id, {})


"""Return room geometry/visuals or shared settings selected by lesson_id."""
def load_room_data(exercise_set_id):

    if not exercise_set_id:
        return {}
    with ROOM_DATA_PATH.open(encoding="utf-8") as file:
        sets = {entry["lesson_id"]: entry for entry in json.load(file)}
    return sets.get(exercise_set_id, {})

"""Return a boss's geometry and visuals from the combined boss catalog."""
def load_boss_room(mission_id, room_id):

    if type(mission_id) is not int or mission_id <= 0:
        return {}
    with BOSSES_PATH.open(encoding="utf-8") as file:
        return next((entry for entry in json.load(file)
                     if entry["mission_id"] == mission_id and entry["room_id"] == room_id), {})

"""Return a lesson's image, foot anchor, final height, and duration settings."""
def load_lesson_visuals(lesson_reference=None):
    """
    References select JSON records, never paths.
    None selects the fallback.
    Height is relative to background height; duration uses milliseconds.
    Movement preparation validates these settings against the room's plane and path."""
    if lesson_reference is None:
        return dict(load_room_data("settings")["default"]["visuals"])
    with BOSSES_PATH.open(encoding="utf-8") as file:

        for entry in json.load(file):
            if entry["lesson_id"] == lesson_reference:
                return dict(entry["visuals"])

    raise ValueError(f"Unknown lesson presentation: {lesson_reference}")

"""Return shared speed bounds, visible approach time, and death rotation."""
def load_movement_settings():
    return load_room_data("settings")["playback"]

"""Read non-boss visuals from room_data.json or boss visuals from bosses.json."""
def load_room_lesson_visuals(mission_id, room_id, exercise_set_id=""):
    """
    exercise_set_id selects the same record as the room's exercise popup.
    Unknown or unplaced content uses default visuals."""
    if exercise_set_id:
        entry = load_room_data(exercise_set_id)
        if "visuals" in entry:
            return dict(entry["visuals"])
        return load_lesson_visuals()

    boss = load_boss_room(mission_id, room_id)
    return dict(boss["visuals"]) if boss else load_lesson_visuals()


from .bosses.variables import BossLessonVar


# Stable LessonIDs map to classes so each encounter gets its own instance.
LESSONS = {
    "boss_variables": BossLessonVar,
}


def create_lesson_from_id(lesson_id: str):
    """Return a lesson instance for its ID, None for a blank ID, or raise ValueError for an unknown ID."""
    if lesson_id == "":
        return None
    try:
        lesson_class = LESSONS[lesson_id]
    except KeyError as error:
        raise ValueError(f"Unknown LessonID: {lesson_id}") from error
    return lesson_class()
