"""Run player-written Python with exec() in a separate process and compare its printed output."""

import json
import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).with_name("exec_runner.py")
TIME_LIMIT_SECONDS = 5
MAX_OUTPUT_CHARACTERS = 20_000
# exec_runner prints this before the final variable values, after the program's own output.
VARIABLES_MARKER = "\0variables:"


def run_python(code: str, variables: dict | None = None) -> dict:
    """Return {"output", "error"}: the program's stdout and its traceback, or a time-limit message.

    With variables, the program starts with them defined and "variables" holds their final values,
    or None when the program crashed or was stopped.
    """
    # WARNING: exec() runs arbitrary Python with this server's permissions; the process only limits time.
    request = json.dumps({"code": code, "variables": variables or {}}).encode()
    try:
        completed = subprocess.run(
            [sys.executable, "-I", str(RUNNER)], input=request, capture_output=True,
            timeout=TIME_LIMIT_SECONDS,
        )
    except subprocess.TimeoutExpired as timeout:
        result = {
            "output": _decode(timeout.stdout),
            "error": f"Your program ran for more than {TIME_LIMIT_SECONDS} seconds and was stopped. Check for a loop that never ends.",
        }
        if variables:
            result["variables"] = None
        return result
    stdout, marker, final_values = completed.stdout.rpartition(VARIABLES_MARKER.encode())
    if not marker:
        stdout = final_values
    result = {"output": _decode(stdout), "error": _decode(completed.stderr)}
    if variables:
        result["variables"] = json.loads(final_values) if marker else None
    return result


def _decode(data: bytes | None) -> str:
    text = (data or b"").decode("utf-8", errors="replace")
    if len(text) > MAX_OUTPUT_CHARACTERS:
        return text[:MAX_OUTPUT_CHARACTERS] + "\n... (output cut off)"
    return text


def outputs_match(actual: str, expected: str) -> bool:
    """Compare printed output line by line, ignoring trailing spaces and trailing blank lines."""
    def normalize(text):
        return "\n".join(line.rstrip() for line in text.rstrip().splitlines())
    return normalize(actual) == normalize(expected)
