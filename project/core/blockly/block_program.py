"""Read the shared block vocabulary under an encounter's requested allowances."""

from collections import Counter


# =======================================================================
# Identify supported block roles and bound the size of submitted programs
# =======================================================================
ACTION_NAMES = {
    "make_noise",
    "wait",
    "step_forward",
    "hold_position",
    "attack",
    "dodge",
    "block",
    "step_back",
    "duck",
    "step_aside",
}
CONDITION_NAMES = {"undetected", "not_close"}
MAX_NESTING_DEPTH = 30
MAX_PLACED_BLOCKS = 200


# ==================================================================
# Validate every connected block before any encounter action can run
# ==================================================================
class WorkspaceProgramReader:
    """Validate all placed blocks before executing any selected branch."""

    def __init__(self, requested_blocks, limits, case_labels):
        self.requested_blocks = set(requested_blocks)
        self.limits = limits
        self.case_labels = set(case_labels)
        # Share counters across nested reads so skipped branches still use allowances.
        self.ids = set()
        self.counts = Counter()

    # ===========================================================
    # Read one connected program and count blocks in every branch
    # ===========================================================
    def read_connected_program(self, workspace):
        if not isinstance(workspace, dict) or not isinstance(workspace.get("blocks"), dict):
            raise ValueError("Build one connected program before running.")

        roots = workspace["blocks"].get("blocks")
        if not isinstance(roots, list) or len(roots) != 1:
            raise ValueError("Connect all placed blocks into one program before running.")

        # Validate the complete structure before an encounter executes any part of it.
        program = self.read_statement_chain(roots[0])

        for block_type, limit in self.limits.items():
            if self.counts[block_type] > limit:
                label = block_type.removeprefix("boss_").removeprefix("controls_")
                raise ValueError(f"Too many {label} blocks. Maximum: {limit}.")

        return program

    # =============================================================================
    # Check block identity, structure, and availability before reading its contents
    # =============================================================================
    def read_block_metadata(self, block, depth):
        if (
            not isinstance(block, dict)
            or depth > MAX_NESTING_DEPTH
            or len(self.ids) >= MAX_PLACED_BLOCKS
        ):
            raise ValueError("The program is malformed or too large.")

        block_id, block_type = block.get("id"), block.get("type")
        if not isinstance(block_id, str) or not block_id or block_id in self.ids:
            raise ValueError("Each block needs a unique Blockly ID.")
        if not isinstance(block_type, str):
            raise ValueError("Unsupported block type.")
        if block.get("enabled") is False or block.get("disabledReasons"):
            raise ValueError("Remove or enable disabled blocks before running.")

        valid_inputs = isinstance(block.get("inputs", {}), dict)
        valid_fields = isinstance(block.get("fields", {}), dict)
        if not valid_inputs or not valid_fields:
            raise ValueError("Invalid block inputs or fields.")

        if block_type not in self.requested_blocks:
            raise ValueError(f"This encounter does not offer {block_type}.")

        self.ids.add(block_id)
        self.counts[block_type] += 1

        return {"block_id": block_id, "type": block_type}

    # ===========================================================
    # Read a named input connection while allowing an empty input
    # ===========================================================
    def get_connected_block(self, block, name):
        connection = block.get("inputs", {}).get(name)
        if connection is None:
            return None
        # Shadow blocks are Blockly fallback values, not supplied student blocks.
        if (
            not isinstance(connection, dict)
            or "shadow" in connection
            or "block" not in connection
        ):
            raise ValueError("Use the supplied blocks in each input.")

        return connection["block"]

    # ============================================================
    # Reject inputs that do not belong to the supplied block shape
    # ============================================================
    def check_input_names(self, block, allowed):
        if set(block.get("inputs", {})) - set(allowed):
            raise ValueError("Unsupported block input. Use the supplied block shapes.")

    # ======================================================================
    # Read Boolean inputs and validate both sides of each logical expression
    # ======================================================================
    def read_condition(self, block, depth):
        if block is None:
            raise ValueError("Connect a condition to every condition input.")

        node = self.read_block_metadata(block, depth)
        if "next" in block:
            raise ValueError("Conditions cannot have following statements.")

        if node["type"].startswith("boss_") and node["type"][5:] in CONDITION_NAMES:
            self.check_input_names(block, [])
            node["condition"] = node["type"].removeprefix("boss_")
        elif node["type"] == "logic_operation":
            self.check_input_names(block, ["A", "B"])
            node["operator"] = block.get("fields", {}).get("OP", "AND")
            if node["operator"] not in ("AND", "OR"):
                raise ValueError("Use AND or OR to combine conditions.")
            # Read both inputs even though execution may later short-circuit one.
            node["left"] = self.read_condition(self.get_connected_block(block, "A"), depth + 1)
            node["right"] = self.read_condition(self.get_connected_block(block, "B"), depth + 1)
        else:
            raise ValueError("Use a requested Boolean block in each condition input.")

        return node

    # ==========================================================================
    # Preserve statement order while keeping switch choices out of action stacks
    # ==========================================================================
    def read_statement_chain(self, block, depth=0, case_chain=False):
        nodes = []

        while block is not None:
            node = self.read_block_metadata(block, depth)
            block_type = node["type"]

            # The switch's choice chain contains cases; each case body contains statements.
            if case_chain:
                self.read_case_body(block, node, depth)
            elif block_type.startswith("boss_") and block_type[5:] in ACTION_NAMES:
                self.check_input_names(block, [])
                node["action"] = block_type[5:]
            elif block_type in ("controls_if", "controls_ifelse"):
                self.read_if_branches(block, node, depth)
            elif block_type == "boss_switch":
                self.read_switch_choices(block, node, depth)
            else:
                raise ValueError("Unsupported statement, or a case placed outside switch.")

            nodes.append(node)

            # Follow sibling statements without increasing their nesting depth.
            following = block.get("next")
            if following is not None:
                if not isinstance(following, dict) or "block" not in following:
                    raise ValueError("Invalid statement connection.")
                block = following["block"]
            else:
                block = None

        return nodes

    # ===========================================================
    # Read a valid case label and require a connected action body
    # ===========================================================
    def read_case_body(self, block, node, depth):
        if node["type"] != "boss_case":
            raise ValueError("Only case blocks may connect directly inside switch.")

        self.check_input_names(block, ["ATTACK", "DO"])
        # Zombie action values select a case; they never execute an action or
        # consume a turn. Count them as placed blocks and validate their type.
        attack = self.get_connected_block(block, "ATTACK")
        if attack is None:
            raise ValueError("Connect a zombie action to each case.")
        attack_node = self.read_block_metadata(attack, depth + 1)
        self.check_input_names(attack, [])
        label = attack_node["type"].removeprefix("boss_")
        if "next" in attack or label not in self.case_labels:
            choices = ", ".join(sorted(self.case_labels))
            raise ValueError(f"Each case needs a valid label: {choices}.")

        node["label"] = label
        node["body"] = self.read_statement_chain(
            self.get_connected_block(block, "DO"), depth + 1,
        )
        if not node["body"]:
            raise ValueError("Connect an action inside each case.")

    # ============================================================================
    # Read the condition and both branches without allowing extra mutator branches
    # ============================================================================
    def read_if_branches(self, block, node, depth):
        # Saved mutator state must not provide a way around the if/else allowance.
        extra = block.get("extraState", {})
        if not isinstance(extra, dict) or extra.get("elseIfCount") or extra.get("hasElse"):
            raise ValueError("Use the supplied if and if/else blocks without extra branches.")

        allowed_inputs = ["IF0", "DO0"]
        if node["type"] == "controls_ifelse":
            allowed_inputs.append("ELSE")
        self.check_input_names(block, allowed_inputs)

        node["condition"] = self.read_condition(
            self.get_connected_block(block, "IF0"), depth + 1,
        )
        node["yes"] = self.read_statement_chain(
            self.get_connected_block(block, "DO0"), depth + 1,
        )
        node["no"] = self.read_statement_chain(
            self.get_connected_block(block, "ELSE"), depth + 1,
        )

    # ===============================================================
    # Read case choices and require each requested label exactly once
    # ===============================================================
    def read_switch_choices(self, block, node, depth):
        self.check_input_names(block, ["CASES"])
        node["cases"] = self.read_statement_chain(
            self.get_connected_block(block, "CASES"), depth + 1, case_chain=True,
        )

        # Validate the choice set here; selecting a case belongs to the encounter runner.
        labels = [case["label"] for case in node["cases"]]

        if len(set(labels)) != len(labels):
            raise ValueError("Duplicate case name. Each label may appear only once.")
        if set(labels) != self.case_labels:
            raise ValueError("Add one case for each requested case label.")
