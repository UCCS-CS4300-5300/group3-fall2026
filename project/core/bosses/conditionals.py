"""Execute the Police Station boss in action units, without animation playback."""

from ..blockly.block_program import WorkspaceProgramReader


BOSS_ID = "police_station_boss_zombie"
DEFENSES = {
    "grab": "dodge",
    "swipe": "block",
    "lunge": "step_back",
    "high_swing": "duck",
    "charge": "step_aside",
}
FIXED_ATTACK = "lunge"

# =========================================================================
# Define the intended action budget and request blocks from the shared pool
# =========================================================================
# Executed path through the intended code, after removal of the final guard.
# Unselected defenses and the else branch contribute no action units.
INTENDED_ACTIONS = ("make_noise", "wait", "step_forward", DEFENSES[FIXED_ATTACK], "attack")
ACTION_UNITS = len(INTENDED_ACTIONS)
APPROACH_UNITS = INTENDED_ACTIONS.index(DEFENSES[FIXED_ATTACK])
BLOCK_LIMITS = {
    "controls_if": 3,
    "controls_ifelse": 1,
    "boss_switch": 1,
    "boss_case": len(DEFENSES),
    **{f"boss_{defense}": 1 for defense in DEFENSES.values()},
}


def request_workspace_blocks():
    return {
        "requested_blocks": [
            "controls_if", "controls_ifelse", "boss_switch", "boss_case", "logic_operation",
            "boss_undetected", "boss_not_close", "boss_make_noise", "boss_wait",
            "boss_step_forward", "boss_hold_position", "boss_dodge", "boss_block",
            "boss_step_back", "boss_duck", "boss_step_aside", "boss_attack",
        ],
        "limits": BLOCK_LIMITS.copy(),
        "case_labels": list(DEFENSES),
        "switch_expression": "attack_type",
        "allow_if_mutation": False,
        "submission_format": "workspace",
        "playback": "deferred",
    }


def get_initial_requirements():
    return {}


def get_initial_variables():
    return ActionUnitEncounter().describe_state()


# ===============================================================
# Resolve action-unit state changes without playing the animation
# ===============================================================
class ActionUnitEncounter:
    def __init__(self):
        self.turn = 0
        self.detected = False
        self.phase = "undetected"
        self.events = []
        self.feedback = "The program ended before the zombie was defeated. Try again."

    def describe_state(self):
        return {
            "turn": self.turn,
            "action_units": ACTION_UNITS,
            "progress": self.turn / ACTION_UNITS,
            "undetected": not self.detected,
            "not_close": self.turn < APPROACH_UNITS,
            "attack_type": FIXED_ATTACK if self.detected and self.turn >= APPROACH_UNITS else None,
            "phase": self.phase,
        }

    def record_execution_step(self, node, kind, before, result=None):
        # before/after turns are action-unit boundaries. Stage 4 can multiply
        # them by total animation duration / ACTION_UNITS; no playback runs here.
        self.events.append({
            "block_id": node["block_id"],
            "kind": kind,
            "before": before,
            "after": self.describe_state(),
            "result": result,
        })

    def evaluate_condition(self, node):
        before = self.describe_state()
        if "condition" in node:
            result = before[node["condition"]]
        elif node["operator"] == "AND":
            result = self.evaluate_condition(node["left"]) and self.evaluate_condition(node["right"])
        else:
            result = self.evaluate_condition(node["left"]) or self.evaluate_condition(node["right"])
        self.record_execution_step(node, "condition", before, result)
        return result

    def fail_encounter(self, message):
        self.phase = "failed"
        self.feedback = message

    # ============================================================================
    # Consume one action unit and resolve detection, defense, or the finishing hit
    # ============================================================================
    def apply_action(self, node):
        before = self.describe_state()
        action = node["action"]
        self.turn += 1

        if self.phase == "attacking":
            if action == DEFENSES[FIXED_ATTACK]:
                self.phase = "defended"
            else:
                self.fail_encounter("The zombie lunged. Use step_back() to defend before your next action.")
        elif action == "attack":
            if self.phase == "defended":
                self.phase = "defeated"
                self.feedback = "The zombie is defeated. You win!"
            else:
                self.fail_encounter("Defend against the zombie's attack before the finishing hit.")
        elif action in DEFENSES.values():
            self.fail_encounter("The zombie has not attacked yet. Your defense was too early.")
        else:
            if action == "make_noise":
                self.detected = True
            if self.detected and self.phase != "defended":
                self.phase = "attacking" if self.turn >= APPROACH_UNITS else "approaching"

        if self.turn >= ACTION_UNITS and self.phase not in {"failed", "defeated"}:
            self.fail_encounter(f"All {ACTION_UNITS} action units are used up. Try again.")

        self.record_execution_step(node, "action", before, action)

    # ============================================================================
    # Follow selected branches without charging time for decisions or skipped code
    # ============================================================================
    def execute_statement_chain(self, nodes):
        for node in nodes:
            if self.phase in {"failed", "defeated"}:
                break
            if "action" in node:
                self.apply_action(node)
            elif "condition" in node:
                selected = self.evaluate_condition(node["condition"])
                self.record_execution_step(node, "if", self.describe_state(), selected)
                self.execute_statement_chain(node["yes"] if selected else node["no"])
            else:
                # Select once before executing the case. Its next sibling is
                # another choice, never an instruction to fall through.
                before = self.describe_state()
                selected = next(
                    (case for case in node["cases"] if case["label"] == before["attack_type"]),
                    None,
                )
                if selected is None:
                    self.fail_encounter("The switch was reached before the zombie's attack.")
                self.record_execution_step(node, "switch", before, before["attack_type"])
                if selected:
                    self.record_execution_step(selected, "case", self.describe_state(), selected["label"])
                    self.execute_statement_chain(selected["body"])


# ============================================================================
# Validate the requested blocks, then return their ordered action-unit results
# ============================================================================
def evaluate_workspace_program(workspace):
    config = request_workspace_blocks()
    program = WorkspaceProgramReader(
        config["requested_blocks"], config["limits"], config["case_labels"]
    ).read_connected_program(workspace)

    runner = ActionUnitEncounter()
    initial = runner.describe_state()
    runner.execute_statement_chain(program)
    state = runner.describe_state()

    return {
        "encounter": BOSS_ID,
        "initial_state": initial,
        "state": state,
        "events": runner.events,
        "passed": runner.phase == "defeated",
        "feedback": runner.feedback,
        "details": [
            f"Action units: {state['turn']}/{state['action_units']}.",
            f"Attack: {state['attack_type'] or 'not revealed'}.",
        ],
    }


# =============================================================
# Accept a workspace through the shared room-submission handler
# =============================================================
def evaluate_submission(submission, requirements):
    # Accept the older key while previously loaded pages refresh their bundle.
    workspace = submission.get("workspace", submission.get("boss_workspace"))
    return evaluate_workspace_program(workspace)
