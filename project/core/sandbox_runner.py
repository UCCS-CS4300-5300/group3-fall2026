"""Child process: read a player's program from stdin, exec() it, and print what it printed.

Started only by code_runner.run_python; Django never imports this file.
"""
import io
import sys
import traceback

FILENAME = "<your code>"
MAX_OUTPUT_CHARS = 10_000


class LimitedOutput(io.StringIO):
    """Collect print() output, stopping programs that print forever."""

    def write(self, text):
        if self.tell() + len(text) > MAX_OUTPUT_CHARS:
            raise RuntimeError("Your program printed too much. Check for a loop that never ends.")
        return super().write(text)


def limit_resources():
    """Cap CPU time and memory, and block file writes and new processes (Linux/macOS only)."""
    try:
        import resource
    except ImportError:  # Windows: the parent's timeout still stops endless loops.
        return
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))


def describe(error):
    """Turn an exception into "NameError on line 2: name 'y' is not defined"."""
    if isinstance(error, SyntaxError):
        line, message = error.lineno, error.msg
    else:
        frames = [f for f in traceback.extract_tb(error.__traceback__) if f.filename == FILENAME]
        line, message = (frames[-1].lineno if frames else None), str(error)
    where = f" on line {line}" if line else ""
    return f"{type(error).__name__}{where}" + (f": {message}" if message else "")


def main():
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    code = sys.stdin.read()
    limit_resources()

    real_stdout, captured = sys.stdout, LimitedOutput()
    sys.stdout = captured
    exit_code = 0
    try:
        exec(compile(code, FILENAME, "exec"), {"__name__": "__main__"})
    except SystemExit:
        pass  # sys.exit() in player code just ends the program.
    except BaseException as error:
        print(describe(error), file=sys.stderr)
        exit_code = 1
    finally:
        sys.stdout = real_stdout
    real_stdout.write(captured.getvalue())
    sys.exit(exit_code)


main()
