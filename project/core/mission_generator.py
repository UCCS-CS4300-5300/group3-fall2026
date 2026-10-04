import os
from typing import Annotated

import ollama
from django.db import transaction
from pydantic import BaseModel, Field, ValidationError, model_validator

from .block_checker import (
    ACTION_PATTERN, BLOCK_PATTERN, CONTAINER_BLOCK_PATTERN, has_zombie_punch, normalize, parse_program, program_problems,
)
from .models import Mission, Puzzle

# Any model from `ollama list`. Bigger models write better missions but need more RAM.
MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")
# Small models occasionally ramble forever or return broken JSON, so cap each reply and retry
MAX_TOKENS = 1024
MAX_ATTEMPTS = 3

SYSTEM_PROMPT = """You write missions for Code Blocks, a game where students learn programming \
by snapping together blocks to guide a character across a grid map to an exit, while a zombie \
blocks the way.

These are the only blocks. Write each one exactly like this, with N a number:
move forward
turn left
turn right
punch
repeat until finish
repeat N times
if path ahead
if path left
if path right
if zombie ahead
else

Every mission has a zombie, so the intended code must put punch inside if zombie ahead.

Each mission has:
- title: a short, catchy name, under 60 characters
- description: one or two sentences of story setup the student reads first
- instructions: what the student has to do, naming the programming concepts they should use. \
Plain sentences, no code.
- intended_code: the list of blocks that solve the mission. Blocks that go inside a repeat, \
if or else are listed in its "inside". Nothing can come after repeat until finish. For example:
[{"block": "repeat until finish", "inside": [{"block": "if zombie ahead", "inside": ["punch"]}, "move forward"]}]
- tests: 2 to 4 checks for the student's program. Each has an action the program should do, \
a yes/no question that checks it happened, and the one block from intended_code that proves it. \
For example: action "Punch the zombie", check "Is punch inside if zombie ahead?", block "punch"

Write your own story, code and tests for this mission; don't copy the examples. \
Write for beginners: friendly, concrete, and short. Respond in JSON."""


# The block patterns go into the JSON schema sent to Ollama, which stops the model from writing
# blocks that don't exist. Actions are plain strings, so the model can't put blocks inside them.
Action = Annotated[str, Field(pattern=f"^{ACTION_PATTERN}$")]


class Container(BaseModel):
    block: str = Field(pattern=f"^{CONTAINER_BLOCK_PATTERN}$")
    # The blocks inside this repeat, if or else
    inside: list["Action | Container"] = Field(min_length=1, max_length=6)


Step = Action | Container


def steps_to_lines(steps, depth=0):
    for step in steps:
        if isinstance(step, Container):
            yield "  " * depth + step.block
            yield from steps_to_lines(step.inside, depth + 1)
        else:
            yield "  " * depth + step


class TestStep(BaseModel):
    action: str
    check: str
    # One block from intended_code; the practice page checks the student placed it
    block: str = Field(pattern=f"^{BLOCK_PATTERN}$")


# The exact shape we want back from the AI.
# title/description/instructions go on the Mission, intended_code/tests go on its Puzzle.
class MissionData(BaseModel):
    title: str
    description: str
    instructions: str
    # Nested rather than indented text: small models nest JSON far more reliably than they indent
    intended_code: list[Step] = Field(min_length=1, max_length=8)
    tests: list[TestStep] = Field(min_length=1, max_length=4)

    @property
    def code(self):
        """intended_code as indented text, one block per line."""
        return "\n".join(steps_to_lines(self.intended_code))

    @model_validator(mode="after")
    def code_makes_sense(self):
        problems = program_problems(self.code)
        if not has_zombie_punch(parse_program(self.code)):
            problems.append("intended_code must put punch inside if zombie ahead")
        lines = {path[-1] for path in parse_program(self.code)}
        problems += [f'test block "{test.block}" is not in intended_code'
                     for test in self.tests if normalize(test.block) not in lines]
        if problems:
            raise ValueError("; ".join(problems))
        return self


class MissionGenerationError(Exception):
    pass


def generate_mission(topic="", client=None):
    '''
    Asks a local Ollama model for a new mission, then builds a Mission and its Puzzle and saves them.
    `topic` is optional, e.g. "while loops". Needs the Ollama app running.
    '''
    client = client or ollama.Client()

    prompt = "Write a new mission where a zombie blocks the path and the student's code punches it."
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
            solution=data.code,
            tests=[test.model_dump() for test in data.tests],
        )
    return mission
