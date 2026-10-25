"""Execute supported lesson operations without evaluating user-written code."""


def apply_assignments_to_variables(assignments: list[dict], initial_variables: dict[str, bool | int]) -> dict:
    """Apply validated assignments to copied variables; return final values and ordered actions."""
    if not isinstance(assignments, list):
        raise ValueError("The program must be a list of assignments.")

    variables = initial_variables.copy()
    actions = []
    for assignment in assignments:
        _validate_assignment_name_and_value_type(assignment, variables)
        variable = assignment["variable"]
        value = assignment["value"]
        variables[variable] = value
        actions.append({"variable": variable, "value": value})

    return {"variables": variables, "actions": actions}


def _validate_assignment_name_and_value_type(assignment, variables):
    """Reject assignments with missing or extra fields, unknown names, or mismatched value types."""
    if not isinstance(assignment, dict) or set(assignment) != {"variable", "value"}:
        raise ValueError("Each assignment needs a variable name and a value.")

    variable = assignment["variable"]
    if not isinstance(variable, str) or variable not in variables:
        raise ValueError(f"Unknown variable: {variable}")

    # Exact types matter: Python otherwise treats True and False as integers.
    expected_type = type(variables[variable])
    if type(assignment["value"]) is not expected_type:
        raise ValueError(f"{variable} requires a value of type {expected_type.__name__}.")
