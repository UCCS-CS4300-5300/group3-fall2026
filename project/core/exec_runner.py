"""Run a player's program from stdin with exec(); code_runner starts this in its own Python process."""

import json
import sys
import traceback

# Same marker as code_runner.VARIABLES_MARKER; this file runs isolated, so it can't import it.
VARIABLES_MARKER = "\0variables:"

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# stdin is {"code": "...", "variables": {name: starting value}}.
request = json.loads(sys.stdin.read())
variables = request["variables"]
namespace = {"__name__": "__main__", **variables}
try:
    exec(compile(request["code"], "main.py", "exec"), namespace)
except BaseException as error:
    sys.stdout.flush()
    # Drop this file's frame so the traceback starts at the player's code.
    traceback.print_exception(type(error), error, error.__traceback__.tb_next)
    sys.exit(1)

# Report the starting variables' final values after the program's own output.
if variables:
    final_values = {name: namespace.get(name) for name in variables}
    print(VARIABLES_MARKER + json.dumps(final_values, default=repr), end="", file=sys.__stdout__)
