"""Lesson behavior, block choices, and room/picture data associations."""

import json
from pathlib import Path

from .lesson_runner import apply_assignments_to_variables


LESSON_PROFILES_PATH = Path(__file__).parent / "data" / "lesson_profiles.json"


def _load_visual_catalogue():
    """Read authored lesson visuals and placements, rejecting unknown versions."""
    catalogue = json.loads(LESSON_PROFILES_PATH.read_text(encoding="utf-8"))
    if type(catalogue.get("version")) is not int or catalogue["version"] != 1:
        raise ValueError("Unsupported lesson presentation schema.")
    return catalogue


def _lesson_visual_settings(catalogue, lesson_reference):
    if lesson_reference is None:
        return dict(catalogue["default"])

    try:
        return dict(catalogue["lessons"][lesson_reference])
    except KeyError as error:
        raise ValueError(f"Unknown lesson presentation: {lesson_reference}") from error


def load_lesson_visuals(lesson_reference=None):
    """Return a lesson's image, foot anchor, final height, and duration settings.

    References select JSON records, never paths. None selects the fallback.
    Height is relative to background height; duration uses milliseconds. Movement
    preparation validates these settings against the room's plane and path.
    """
    return _lesson_visual_settings(_load_visual_catalogue(), lesson_reference)


def load_movement_settings():
    """Return shared speed bounds, visible approach time, and death rotation."""
    return _load_visual_catalogue()["playback"]


def load_room_lesson_visuals(mission_id, room_id):
    """Resolve a room's lesson reference without copying its plane into the lesson.

    Multiple rooms may reference one lesson. Unassigned rooms use default visuals.
    """
    catalogue = _load_visual_catalogue()
    placements = catalogue["placements"].get(str(mission_id), {})
    return _lesson_visual_settings(catalogue, placements.get(str(room_id)))


class BossLessonVar:
    """Variables lesson using assignments to the boss zombie's state."""

    default_requirements = {"zombie_alive": False}
    instructions = "A zombie is approaching! Use the available blocks to defeat it."

    def get_initial_zombie_variables(self) -> dict[str, bool | int]:
        """Return a fresh {zombie_alive: True, zombie_speed: 10} for each attempt."""
        return {"zombie_alive": True, "zombie_speed": load_movement_settings()["normal_speed"]}

    def apply_assignments_to_zombie_variables(self, assignments: list[dict], requirements: dict | None = None) -> dict:
       
        """Apply assignments to fresh variables and check saved requirements; return state, actions, passed, and feedback."""
        if requirements is None:
            requirements = self.default_requirements
        
        initial_variables = self.get_initial_zombie_variables()
        result = apply_assignments_to_variables(assignments, initial_variables)
        
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

class JumpscareCashierLesson:
    """Corner Store jumpscare: fix the cashier's broken register program, one block per line."""

    default_requirements = {"output": "Total: $15.0"}
    instructions = "The cash drawer slams open and the undead cashier lunges over the counter! The register should print the cost of 6 cans at $2.50, but it crashes. Fix the blocks and run them."
    # Each block's dropdown options mapped to the Python they run; read(name) raises NameError for unset names.
    register_lines = {
        "cans": {
            '"6"': lambda read: "6",
            'int("6")': lambda read: int("6"),
            "6": lambda read: 6,
        },
        "price": {
            "2.50": lambda read: 2.50,
            '"2.50"': lambda read: "2.50",
            "int(2.50)": lambda read: int(2.50),
        },
        "total": {
            "cans * price": lambda read: read("cans") * read("price"),
            "cans + price": lambda read: read("cans") + read("price"),
            "price - cans": lambda read: read("price") - read("cans"),
        },
        "print": {
            "total": lambda read: "Total: $" + read("total"),
            "str(total)": lambda read: "Total: $" + str(read("total")),
            "int(total)": lambda read: "Total: $" + int(read("total")),
        },
    }
    # Broken program from the exercise: cans is text and total is joined onto text unconverted.
    starting_workspace = {
        "blocks": {
            "languageVersion": 0,
            "blocks": [{
                "type": "screen_cashier_cans", "x": 40, "y": 40, "fields": {"VALUE": '"6"'},
                "next": {"block": {
                    "type": "screen_cashier_price", "fields": {"VALUE": "2.50"},
                    "next": {"block": {
                        "type": "screen_cashier_total", "fields": {"VALUE": "cans * price"},
                        "next": {"block": {"type": "screen_cashier_print", "fields": {"VALUE": "total"}}},
                    }},
                }},
            }],
        }
    }

    def get_initial_zombie_variables(self) -> dict:
        """Return no zombie variables; the register program starts empty."""
        return {}

    def apply_assignments_to_zombie_variables(self, assignments: list[dict], requirements: dict | None = None) -> dict:
        """Run the register lines in order with real Python types; return the output and whether it matches."""
        if requirements is None:
            requirements = self.default_requirements
        if not isinstance(assignments, list):
            raise ValueError("The program must be a list of blocks.")

        variables, printed = {}, []
        try:
            for line in assignments:
                text = self._run_register_line(line, variables)
                if text is not None:
                    printed.append(text)
        except (TypeError, NameError) as error:
            # Show the error Python itself raises, as the player would see it.
            printed.append(f"{type(error).__name__}: {error}")

        output = "\n".join(printed)
        passed = output == requirements["output"]
        return {
            "variables": {"output": output},
            "passed": passed,
            "feedback": "The cashier drops. You survived!" if passed else "The cashier is still coming. Fix the code.",
        }

    def _run_register_line(self, line, variables: dict):
        """Run one register line; return the text it prints, or None."""
        if not isinstance(line, dict):
            raise ValueError("This program contains an unsupported block.")

        def read(name):
            if name not in variables:
                raise NameError(f"name '{name}' is not defined")
            return variables[name]

        variable, value = line.get("variable"), line.get("value")
        try:
            run = self.register_lines[variable][value]
        except (KeyError, TypeError) as error:
            raise ValueError("This program contains an unsupported block.") from error

        result = run(read)
        if variable == "print":
            return result
        variables[variable] = result
        return None

    def get_blocks(self) -> list[str]:
        """Return the four register-line Blockly type IDs offered in this lesson's toolbox."""
        return [
            "screen_cashier_cans",
            "screen_cashier_price",
            "screen_cashier_total",
            "screen_cashier_print",
        ]


# Stable LessonIDs map to classes so each encounter gets its own instance.
LESSONS = {
    "boss_variables": BossLessonVar, "jumpscare_cashier": JumpscareCashierLesson,
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
