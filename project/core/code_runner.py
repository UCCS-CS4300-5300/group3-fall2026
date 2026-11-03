"""Run player Python in a separate, time-limited process so a bad program can't hang Django."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RUNNER_PATH = Path(__file__).with_name("sandbox_runner.py")
TIME_LIMIT_SECONDS = 3
MAX_CODE_CHARS = 10_000


def run_python(code: str) -> dict:
    """Return {"output": what the program printed, "error": a friendly message or ""}."""
    if len(code) > MAX_CODE_CHARS:
        return {"output": "", "error": "Your program is too long."}
    # Empty environment so player code can't read secrets like SECRET_KEY from os.environ.
    env = {"SYSTEMROOT": os.environ["SYSTEMROOT"]} if os.name == "nt" else {}
    with tempfile.TemporaryDirectory() as work_dir:
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(RUNNER_PATH)],
                input=code, capture_output=True, encoding="utf-8",
                timeout=TIME_LIMIT_SECONDS, cwd=work_dir, env=env,
            )
        except subprocess.TimeoutExpired:
            return {"output": "", "error": "Your program took too long. Check for a loop that never ends."}
    error = completed.stderr.strip()
    if completed.returncode != 0 and not error:
        # Killed by the CPU or memory limit before it could explain itself.
        error = "Your program used too much time or memory."
    return {"output": completed.stdout, "error": error}
