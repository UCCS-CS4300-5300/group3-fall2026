"""Lesson behavior and block choices, separate from database models."""

from .lesson_runner import apply_assignments_to_variables


class BossLessonVar:
    """Variables lesson using assignments to the boss zombie's state."""

    def get_initial_zombie_variables(self) -> dict[str, bool | int]:
        """Return a fresh {zombie_alive: True, zombie_speed: 10} for each attempt."""
        return {"zombie_alive": True, "zombie_speed": 10}

    def apply_assignments_to_zombie_variables(self, assignments: list[dict]) -> dict:
        """Apply assignments to fresh zombie variables; return state, actions, passed, and feedback."""
        result = apply_assignments_to_variables(assignments, self.get_initial_zombie_variables())
        for action in result["actions"]:
            if action["variable"] == "zombie_speed" and action["value"] < 1:
                raise ValueError("Zombie speed must be at least 1.")
        # Only the final alive state decides victory; changing speed cannot defeat the zombie.
        result["passed"] = result["variables"]["zombie_alive"] is False
        result["feedback"] = (
            "The zombie is dead. You win!" if result["passed"]
            else "The zombie is still alive. Change its alive state to defeat it."
        )
        return result

    def get_blocks(self) -> list[str]:
        """Return the five Blockly type IDs offered in this lesson's toolbox."""
        return [
            "logic_true",
            "logic_false",
            "math_integer",
            "screen_zombie_alive",
            "screen_zombie_speed",
        ]


# Stable LessonIDs map to classes so each encounter gets its own instance.
LESSONS = {
    "boss_variables": BossLessonVar,
}


def create_lesson_from_id(lesson_id: str):
    """Construct a lesson instance from its registered LessonID, such as boss_variables.

    Return None for a blank ID so the screen uses the existing mission puzzle.
    Raise ValueError for an unregistered ID. This does not create a database record.
    """
    if lesson_id == "":
        return None
    try:
        lesson_class = LESSONS[lesson_id]
    except KeyError as error:
        raise ValueError(f"Unknown LessonID: {lesson_id}") from error
    return lesson_class()
