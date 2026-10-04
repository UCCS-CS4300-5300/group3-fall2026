import os

import ollama
from django.db import transaction
from pydantic import BaseModel, Field, ValidationError, field_validator

from .models import Mission, Puzzle

# Any model from `ollama list`. Bigger models write better missions but need more RAM.
MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")
# Small models occasionally ramble forever or return broken JSON, so cap each reply and retry
MAX_TOKENS = 1024
MAX_ATTEMPTS = 3

# The practice page only has three blocks: if, zombie (plugs into the if) and punch zombie.
# These are the only lines the AI may write in intended_code.
PRACTICE_BLOCKS = ["if zombie", "punch zombie"]

SYSTEM_PROMPT = """You write missions for Code Blocks, a game where students learn programming \
by snapping together blocks to guide a character across a grid map to an exit, avoiding hazards \
and the zombie horde behind them.

Blocks students can use: if, zombie and punch zombie. The zombie block plugs into the if, so \
write them together as "if zombie". These are the only blocks; never invent new ones.

Each mission has:
- title: a short, catchy name, under 60 characters
- description: one or two sentences of story setup the student reads first
- instructions: what the student has to do, naming the programming concepts they should use. \
Plain sentences, no code.
- intended_code: the blocks that solve the mission, one block per line, indented two spaces \
inside ifs. Only block names, never Python or JavaScript. For example:
if zombie
  punch zombie
- tests: 2 to 4 checks for the student's program. Each has an action the program should do \
and a yes/no question that checks it happened. For example: action "Punch zombie", \
check "Was zombie punched?"

Write your own story, code and tests for this mission; don't copy the examples. \
Write for beginners: friendly, concrete, and short. Respond in JSON."""


class TestStep(BaseModel):
    action: str
    check: str


# The exact shape we want back from the AI.
# title/description/instructions go on the Mission, intended_code/tests go on its Puzzle.
class MissionData(BaseModel):
    title: str
    description: str
    instructions: str
    intended_code: str
    tests: list[TestStep] = Field(min_length=1)

    @field_validator("intended_code")
    @classmethod
    def only_practice_blocks(cls, code):
        unknown = [line.strip() for line in code.splitlines()
                   if line.strip() and line.strip() not in PRACTICE_BLOCKS]
        if unknown:
            raise ValueError(f"intended_code uses blocks that don't exist: {unknown}")
        return code


class MissionGenerationError(Exception):
    pass


def generate_mission(topic="", client=None):
    '''
    Asks a local Ollama model for a new mission, then builds a Mission and its Puzzle and saves them.
    `topic` is optional, e.g. "while loops". Needs the Ollama app running.
    '''
    client = client or ollama.Client()

    prompt = "Write a new mission."
    if topic:
        prompt += f" It should teach: {topic}"

    for _ in range(MAX_ATTEMPTS):
        response = client.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            # Forces the reply to be JSON with exactly the MissionData fields
            format=MissionData.model_json_schema(),
            options={"num_predict": MAX_TOKENS},
        )
        try:
            data = MissionData.model_validate_json(response.message.content)
            break
        except ValidationError as e:
            error = e
    else:
        raise MissionGenerationError(f"The model did not return a valid mission after {MAX_ATTEMPTS} tries: {error}")

    with transaction.atomic():
        mission = Mission.objects.create(
            title=data.title[:120],
            description=data.description,
            instructions=data.instructions,
        )
        Puzzle.objects.create(
            mission=mission,
            solution=data.intended_code,
            tests=[test.model_dump() for test in data.tests],
        )
    return mission
