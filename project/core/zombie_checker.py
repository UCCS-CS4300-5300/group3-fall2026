import ollama
from pydantic import BaseModel

from .mission_generator import BLOCK_LIST, MODEL

SYSTEM_PROMPT = f"""You check programs in Code Blocks, a beginner coding game.

Blocks:
{BLOCK_LIST}

Programs are one block per line, indented two spaces inside ifs. Blocks indented under an if \
only run when the if is true.

Imagine running the program once with a zombie in the square ahead. First write reason: one \
short, friendly sentence for a beginner. Then punched: true only if a punch zombie block \
actually ran. Respond in JSON."""


# reason comes before punched so the model explains first, then decides
class PunchResult(BaseModel):
    reason: str
    punched: bool


def was_zombie_punched(program):
    if not program.strip():
        return {"reason": "Your program has no blocks yet.", "punched": False}
    open_ifs = []  # (indent, condition is true) for each if we're inside
    for line in program.splitlines():
        block = line.strip()
        if not block:
            continue
        indent = len(line) - len(line.lstrip())
        while open_ifs and open_ifs[-1][0] >= indent:
            open_ifs.pop()
        runs = all(is_true for _, is_true in open_ifs)
        if block == "punch zombie" and runs:
            return {"reason": "Your punch zombie block ran, so the zombie got knocked out!", "punched": True}
        if block.startswith("if"):
            open_ifs.append((indent, block == "if zombie"))
    if "if (empty)" in program:
        return {"reason": "Your if block needs the zombie block plugged into it.", "punched": False}
    return {"reason": "No punch zombie block ran. Put one inside your if zombie block.", "punched": False}
