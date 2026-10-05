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


def was_zombie_punched(program, client=None):
    if not program.strip():
        return {"reason": "Your program has no blocks yet.", "punched": False}
    client = client or ollama.Client()
    response = client.chat(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": f"Program:\n{program}"}],
        format=PunchResult.model_json_schema(),  # forces JSON with exactly these fields
        options={"temperature": 0},              # same program, same answer
    )
    return PunchResult.model_validate_json(response.message.content).model_dump()
