"""Run player-written Python with exec() in a separate process and compare its printed output."""

import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).with_name("exec_runner.py")
TIME_LIMIT_SECONDS = 5
MAX_OUTPUT_CHARACTERS = 20_000


def run_python(code: str) -> dict:
    """Return {"output", "error"}: the program's stdout and its traceback, or a time-limit message."""
    # WARNING: exec() runs arbitrary Python with this server's permissions; the process only limits time.
    try:
        completed = subprocess.run(
            [sys.executable, "-I", str(RUNNER)], input=code.encode(), capture_output=True,
            timeout=TIME_LIMIT_SECONDS,
        )
    except subprocess.TimeoutExpired as timeout:
        return {
            "output": _decode(timeout.stdout),
            "error": f"Your program ran for more than {TIME_LIMIT_SECONDS} seconds and was stopped. Check for a loop that never ends.",
        }
    return {"output": _decode(completed.stdout), "error": _decode(completed.stderr)}


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
