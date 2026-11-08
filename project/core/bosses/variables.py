"""Request pooled variable blocks and evaluate the variables encounter."""

from ..lesson_runner import apply_assignments_to_variables


BOSS_ID = "boss_variables"


# =====================================================================
# Evaluate variable assignments and keep the lesson registry compatible
# =====================================================================
# Shared movement settings are read when an attempt runs, after the lesson
# registry has finished importing this class.
class BossLessonVar:
    """Variables lesson using assignments to the boss zombie's state."""

    default_requirements = {"zombie_alive": False}
    instructions = "A zombie is approaching! Use the available blocks to defeat it."

    def get_initial_zombie_variables(self) -> dict[str, bool | int]:
        """Return a fresh {zombie_alive: True, zombie_speed: 10} for each attempt."""
        from ..lessons import load_movement_settings

        return {"zombie_alive": True, "zombie_speed": load_movement_settings()["normal_speed"]}

    def apply_assignments_to_zombie_variables(self, assignments: list[dict], requirements: dict | None = None) -> dict:
        """Apply assignments to fresh variables and check saved requirements; return state, actions, passed, and feedback."""
        if requirements is None:
            requirements = self.default_requirements

        initial_variables = self.get_initial_zombie_variables()
        result = apply_assignments_to_variables(assignments, initial_variables)

        from ..lessons import load_movement_settings

        settings = load_movement_settings()

        def bounded_speed(value):
            return min(settings["speed_max"], max(settings["speed_min"], value))

        # The runner validates exact integer types first. Clamp both the final
        # state and reported actions so clients never receive unbounded speeds.
        for action in result["actions"]:
            if action["variable"] == "zombie_speed":
                action["value"] = bounded_speed(action["value"])

        result["variables"]["zombie_speed"] = bounded_speed(result["variables"]["zombie_speed"])

        # Only the final alive state decides victory; changing speed cannot defeat the zombie.
        result["passed"] = result["variables"]["zombie_alive"] is requirements["zombie_alive"]

        if result["passed"]:
            result["feedback"] = "The zombie is dead. You win!"
        elif result["variables"]["zombie_speed"] < initial_variables["zombie_speed"]:
            result["feedback"] = "The zombie eats you slower."
        else:
            result["feedback"] = "The zombie is still alive. Try again."
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


# =============================================================
# Supply the workspace request and fresh encounter requirements
# =============================================================
def request_workspace_blocks():
    return {
        "requested_blocks": BossLessonVar().get_blocks(),
        "submission_format": "assignments",
        "playback": "continuous",
    }


def get_initial_requirements():
    return BossLessonVar.default_requirements.copy()


def get_initial_variables():
    return BossLessonVar().get_initial_zombie_variables()


# ========================================================================
# Evaluate typed assignments against the room's saved victory requirements
# ========================================================================
def evaluate_submission(submission, requirements):
    return BossLessonVar().apply_assignments_to_zombie_variables(
        submission.get("assignments"), requirements=requirements,
    )
