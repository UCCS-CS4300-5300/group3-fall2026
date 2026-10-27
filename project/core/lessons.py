"""Lesson behavior, separate from database models."""

from .code_runner import run_python
from .exercises import ExerciseLesson, load_exercise_lessons


class BossLessonVar:
    """Variables boss: the player's Python changes the boss zombie's variables, run with exec()."""

    default_requirements = {"exercises": ["boss"], "zombie_alive": False}
    instructions = "A zombie is approaching! Click the zombie, then write Python that changes its variables to defeat it."
    exercises = [{
        "id": "boss",
        "kind": "boss",
        "title": "The Boss Zombie",
        "object": "A huge zombie blocks the exit. It starts with zombie_alive = True and zombie_speed = 10.",
        "task": "Write Python that assigns new values to the zombie's variables. Set zombie_alive to False to defeat it. zombie_speed must stay at least 1.",
        # Nothing is printed: the final variables decide the fight, and the page shows them.
        "expected_output": "",
        "hint": "Assign a variable with =, for example zombie_speed = 5. True and False start with a capital letter.",
        "starting_code": "",
    }]

    def get_initial_zombie_variables(self) -> dict[str, bool | int]:
        """Return a fresh {zombie_alive: True, zombie_speed: 10} for each attempt."""
        return {"zombie_alive": True, "zombie_speed": 10}

    def public_exercises(self) -> list[dict]:
        """Return the boss as the room's one clickable object."""
        return self.exercises

    def check_exercise(self, exercise_id: str, code: str, requirements: dict | None = None) -> dict:
        """Run code with exec() on fresh variables; return output, error, final variables, passed, and feedback."""
        if exercise_id != "boss":
            raise ValueError("This exercise is not in this room.")
        if requirements is None:
            requirements = self.default_requirements

        initial_variables = self.get_initial_zombie_variables()
        result = run_python(code, initial_variables)
        variables = result["variables"]
        result["passed"] = False
        if variables is None:
            result["feedback"] = "✗ Your program crashed. Read the error, fix the code and run it again."
        elif type(variables["zombie_speed"]) is not int or variables["zombie_speed"] < 1:
            result["feedback"] = "✗ Zombie speed must be a whole number of at least 1."
        # Only the final alive state decides victory; changing speed cannot defeat the zombie.
        elif variables["zombie_alive"] is requirements["zombie_alive"]:
            result["passed"] = True
            result["feedback"] = "✓ The zombie is dead. You win!"
        elif variables["zombie_speed"] < initial_variables["zombie_speed"]:
            result["feedback"] = "✗ The zombie eats you slower."
        else:
            result["feedback"] = "✗ The zombie is still alive. Try again."
        return result


# Stable LessonIDs map to classes so each encounter gets its own instance.
LESSONS = {
    "boss_variables": BossLessonVar,
}


def create_lesson_from_id(lesson_id: str):
    """Return a lesson instance for its ID, None for a blank ID, or raise ValueError for an unknown ID."""
    if lesson_id == "":
        return None
    if lesson_id in LESSONS:
        return LESSONS[lesson_id]()
    # Rooms and Jumpscares use the exercises document; boss rooms keep their own lessons.
    exercise_lessons = load_exercise_lessons()
    if lesson_id in exercise_lessons:
        return ExerciseLesson(exercise_lessons[lesson_id])
    raise ValueError(f"Unknown LessonID: {lesson_id}")
