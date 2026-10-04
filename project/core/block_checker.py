'''
Reads block programs written as text (one block per line, indented for nesting) and checks
a student's program against the AI's intended code.

The practice page turns the student's Blockly workspace into the same text format, so both
sides can be compared line by line, e.g.

repeat until finish
  if zombie ahead
    punch
  move forward
'''
import re
from collections import Counter

# Every block a program may contain. The AI is only allowed to write these,
# and the practice page writes the student's blocks with exactly these words.
ACTION_PATTERN = "(move forward|turn left|turn right|punch)"
# Blocks that hold other blocks inside them
CONTAINER_BLOCK_PATTERN = "(repeat until finish|repeat [2-9] times|if path (ahead|left|right)|if zombie ahead|else)"
BLOCK_PATTERN = f"({ACTION_PATTERN}|{CONTAINER_BLOCK_PATTERN})"
# "else" is stored as e.g. "else (if path ahead)" once parsed, so match anything after it
CONTAINER_PATTERN = re.compile(r"repeat .*|if .*|else.*")


def normalize(line):
    return " ".join(line.lower().split())


def parse_program(text):
    '''
    Turns a block program into a list of paths, one per block, in program order.
    A path is the block plus every block it sits inside, outermost first:
    ("repeat until finish", "if zombie ahead", "punch").
    An "else" is labeled with the if it belongs to, e.g. "else (if path ahead)".
    '''
    paths = []
    # Each entry is (indent width, path of the block that opened this level)
    stack = []
    # The last block seen at each indent width, so "else" can find its if
    last_at_indent = {}

    for raw in text.expandtabs(4).splitlines():
        line = normalize(raw)
        if not line:
            continue
        indent = len(raw.expandtabs(4)) - len(raw.expandtabs(4).lstrip())

        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else ()

        if line == "else" and indent in last_at_indent:
            line = f"else ({last_at_indent[indent]})"

        path = parent + (line,)
        paths.append(path)
        stack.append((indent, path))
        last_at_indent[indent] = line
        # Blocks deeper than this one belong to an earlier parent now
        for deeper in [i for i in last_at_indent if i > indent]:
            del last_at_indent[deeper]

    return paths


def describe(path):
    return " → ".join(path)


def program_problems(text):
    '''Lists what is wrong with how a program's blocks are put together, e.g. an empty repeat.'''
    paths = parse_program(text)
    problems = []
    for i, path in enumerate(paths):
        block = path[-1]
        has_children = i + 1 < len(paths) and paths[i + 1][:len(path)] == path
        if CONTAINER_PATTERN.fullmatch(block) and not has_children:
            problems.append(f'"{block}" needs blocks inside it')
        if not CONTAINER_PATTERN.fullmatch(block) and has_children:
            problems.append(f'nothing can go inside "{block}"')
        if block.startswith("else") and not block.startswith("else (if "):
            problems.append('"else" must come right after an if, at the same indent')
        # The repeat until finish block has no connector on its bottom
        if block == "repeat until finish" and any(
                later[:-1] == path[:-1] for later in paths[i + 1:] if len(later) == len(path)):
            problems.append('nothing can come after "repeat until finish"')
    return problems


def has_zombie_punch(paths):
    '''True if some "punch" sits inside an "if zombie ahead".'''
    return any(path[-1] == "punch" and "if zombie ahead" in path[:-1] for path in paths)


def check_program(intended_code, tests, student_program):
    '''
    Compares the student's program to the intended code.

    Returns:
      passed: every intended block is in the student's program, inside the same blocks
      missing: the intended blocks the student is missing, e.g. "if zombie ahead → punch"
      tests: each AI test with passed True/False, or None when the test names no block
    Extra student blocks are allowed.
    '''
    intended = parse_program(intended_code)
    student = parse_program(student_program)
    student_counts = Counter(student)

    # Counted, so three "move forward" blocks need three in the student's program too
    missing = Counter(intended) - student_counts
    missing_paths = []
    for path in intended:
        if missing[path] > 0:
            missing_paths.append(path)
            missing[path] -= 1

    results = []
    for test in tests:
        block = normalize(test.get("block", ""))
        if not block:
            passed = None
        else:
            # Check the block where the intended code puts it, so "punch" has to be inside
            # "if zombie ahead" when that's how the intended code was written
            where = next((path for path in intended if path[-1] == block), None)
            if where:
                passed = student_counts[where] > 0
            else:
                passed = any(path[-1] == block for path in student)
        results.append({**test, "passed": passed})

    return {
        "passed": not missing_paths,
        "missing": [describe(path) for path in missing_paths],
        "tests": results,
    }
