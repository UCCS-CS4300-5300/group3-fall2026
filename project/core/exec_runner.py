"""Run a player's program from stdin with exec(); code_runner starts this in its own Python process."""

import sys
import traceback

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

code = sys.stdin.read()
try:
    exec(compile(code, "main.py", "exec"), {"__name__": "__main__"})
except BaseException as error:
    sys.stdout.flush()
    # Drop this file's frame so the traceback starts at the player's code.
    traceback.print_exception(type(error), error, error.__traceback__.tb_next)
    sys.exit(1)
