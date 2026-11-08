"""Lesson behavior, block choices, and room/picture data associations."""

import json
from pathlib import Path



EXERCISES_PATH = Path(__file__).parent / "exercises" / "exercises.json"
ROOM_DATA_PATH = Path(__file__).parent / "exercises" / "room_data.json"
BOSSES_PATH = Path(__file__).parent / "exercises" / "bosses.json"

"""Return exercise content selected by lesson_id."""
def load_exercise_set(exercise_set_id):

    if not exercise_set_id:
        return {}
    with EXERCISES_PATH.open(encoding="utf-8") as file:
        sets = {entry["lesson_id"]: entry for entry in json.load(file)}
    return sets.get(exercise_set_id, {})

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


from .bosses.variables import BossLessonVar


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
