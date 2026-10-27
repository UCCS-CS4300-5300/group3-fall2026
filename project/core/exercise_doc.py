"""Parse the "Zombie: Python Exercises for Every Room" Word document into lesson data."""

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
RELS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

BUILDING_HEADING = re.compile(r"Building (\d+): (.+?) \((.+)\)$")
ROOM_HEADING = re.compile(r"Room (\d+): (.+)$")
EXERCISE_HEADING = re.compile(r"(Exercise ([\d.]+)|Jumpscare Zombie|Boss Zombie): (.+)$")
TIMER = re.compile(r"Suggested timer: (\d+) seconds")
# Labels whose value is the following Code or list paragraphs rather than the rest of the line.
BLOCK_LABELS = {
    "Expected output": "expected_output",
    "Solution": "solution",
    "Broken code": "starting_code",
    "Fixed code": "solution",
    "What the player sees when it runs": "error_shown",
}
LINE_LABELS = {
    "Object": "object", "Task": "task", "Hint": "hint",
    "Explanation": "explanation", "Source": "source", "Uses": "uses",
}


def _paragraphs(docx_path: Path):
    """Yield (style, text, link URLs) for each body paragraph, keeping code line breaks."""
    with zipfile.ZipFile(docx_path) as archive:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
        relationships = ElementTree.fromstring(archive.read("word/_rels/document.xml.rels"))
    link_targets = {rel.get("Id"): rel.get("Target") for rel in relationships.iter(f"{RELS}Relationship")}
    for paragraph in document.find(f"{W}body").iter(f"{W}p"):
        style = paragraph.find(f"{W}pPr/{W}pStyle")
        text = ""
        for element in paragraph.iter():
            if element.tag == f"{W}t":
                text += element.text or ""
            elif element.tag == f"{W}tab":
                text += "\t"
            elif element.tag in (f"{W}br", f"{W}cr"):
                text += "\n"
        links = [link_targets[link.get(f"{R}id")] for link in paragraph.iter(f"{W}hyperlink") if link.get(f"{R}id") in link_targets]
        yield (style.get(f"{W}val") if style is not None else ""), text, links


def parse_exercise_document(docx_path: Path) -> list[dict]:
    """Return one lesson per topic room, Jumpscare and Boss, each holding its exercises in document order."""
    lessons = []
    building = room = exercise = None
    block_field = None  # Field collecting the Code/list paragraphs after a block label.

    for style, text, links in _paragraphs(docx_path):
        text = text.strip("\n")
        if style == "Heading2":
            match = BUILDING_HEADING.match(text.strip())
            building = {"number": int(match[1]), "title": match[2], "concept": match[3]} if match else None
            room = exercise = block_field = None
            continue
        if building is None:
            continue
        if style == "Heading3":
            match = ROOM_HEADING.match(text.strip())
            number = int(match[1]) if match else None
            room = {
                "lesson_id": f"building{building['number']}_room{number}" if match else f"building{building['number']}_boss",
                "building": building["number"], "building_title": building["title"], "concept": building["concept"],
                "room": match[2] if match else "Boss Room", "kind": "room" if match else "boss",
                "teaches": "", "exercises": [],
            }
            lessons.append(room)
            exercise = block_field = None
            continue
        if room is None:
            continue
        if style == "Heading4":
            match = EXERCISE_HEADING.match(text.strip())
            kind = "exercise" if match[2] else "jumpscare" if match[1] == "Jumpscare Zombie" else "boss"
            exercise = {
                "id": match[2] or f"{building['number']}-{kind}", "kind": kind, "title": match[3],
                "object": "", "task": "", "expected_output": "", "hint": "", "solution": "",
                "starting_code": "", "explanation": "", "source": "", "source_urls": [],
            }
            if kind == "jumpscare":
                # A Jumpscare sits under the topic room it hides in but runs as its own encounter.
                lessons.append({
                    **room, "lesson_id": f"building{building['number']}_jumpscare", "kind": "jumpscare",
                    "room": f"Jumpscare: {match[3]}", "hides_in": room["room"], "teaches": "", "exercises": [],
                })
                exercise.update(bugs=[], error_shown="", timer_seconds=None)
            lessons[-1]["exercises"].append(exercise)
            block_field = None
            continue

        label, _, value = text.partition(":")
        if exercise is None:
            if label == "Teaches":
                room["teaches"] = value.strip()
            continue
        if style == "Code" and block_field:
            exercise[block_field] = f"{exercise[block_field]}\n{text}" if exercise[block_field] else text
        elif style == "ListParagraph" and block_field == "bugs":
            exercise["bugs"].append(text.strip())
        elif label in BLOCK_LABELS and not value.strip():
            block_field = BLOCK_LABELS[label]
            exercise[block_field] = ""
        elif label.startswith("Bugs to fix"):
            block_field = "bugs"
        elif label in LINE_LABELS:
            block_field = None
            exercise[LINE_LABELS[label]] = value.strip()
            if label == "Source":
                exercise["source_urls"] = links
        elif TIMER.search(text):
            exercise["timer_seconds"] = int(TIMER.search(text)[1])
        elif text.strip():
            raise ValueError(f"Unrecognised line in exercise {exercise['id']}: {text!r}")

    # Jumpscares have no hint in the document; show their bug list on request instead.
    for lesson in lessons:
        for exercise in lesson["exercises"]:
            if exercise["kind"] == "jumpscare" and not exercise["hint"]:
                exercise["hint"] = " ".join(exercise["bugs"])
    return lessons
