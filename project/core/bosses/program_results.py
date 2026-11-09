"""Give every program response the same feedback and detail-line fields."""


# ========================================================================
# Describe results without requiring boss-specific branches in the browser
# ========================================================================
def describe_run_result(result):
    response = dict(result)

    if "feedback" not in response and "punched" in response:
        outcome = "✓ The zombie was punched!" if response["punched"] else "✗ The zombie was not punched."
        response["feedback"] = f"{outcome} {response.get('reason', '')}".strip()

    if "details" not in response:
        response["details"] = [
            f"{name} = {str(value).lower() if isinstance(value, bool) else value}"
            for name, value in response.get("variables", {}).items()
        ]

    return response
