import pytest
import re
from types import SimpleNamespace
from unittest.mock import MagicMock
from django.urls import reverse
from django.contrib.staticfiles import finders
from django.db import IntegrityError
from pydantic import ValidationError
from .models import Mission
from .models import Puzzle
from .mission_generator import MAX_ATTEMPTS, MissionData, MissionGenerationError, generate_mission
from .block_checker import check_program, parse_program, program_problems

# Mission Database Tests

@pytest.mark.django_db
def test_mission_has_title():
    mission = Mission.objects.create(
        title="Reach the Exit"
    )

    assert mission.title == "Reach the Exit"

@pytest.mark.django_db
def test_mission_has_description():
    mission = Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit."
    )

    assert mission.description == "Guide the character to the exit."

@pytest.mark.django_db
def test_mission_has_instructions():
    mission = Mission.objects.create(
        title="Reach the Exit",
        instructions="Use for loops, if statements, and while loops to reach the exit. Avoid hazards and the zombie horde behind you!"
    )

    assert mission.instructions == "Use for loops, if statements, and while loops to reach the exit. Avoid hazards and the zombie horde behind you!"

@pytest.mark.django_db
def test_mission_string_representation():
    mission = Mission.objects.create(
        title="Reach the Exit"
    )

    assert str(mission) == "Reach the Exit"

# Puzzle and Mission Relationship Tests

@pytest.mark.django_db
def test_mission_and_puzzle_have_relationship():
    mission = Mission.objects.create(
        title="Reach the Exit"
    )

    puzzle = Puzzle.objects.create(
        mission=mission
    )

    assert puzzle.mission == mission
    assert mission.puzzle == puzzle

@pytest.mark.django_db
def test_mission_can_only_have_one_puzzle():
    mission = Mission.objects.create(
        title="Reach the Exit"
    )

    Puzzle.objects.create(
        mission=mission
    )

    with pytest.raises(IntegrityError):
        Puzzle.objects.create(
            mission=mission
        )

@pytest.mark.django_db
def test_puzzle_string_representation():
    mission = Mission.objects.create(
        title="Reach the Exit"
    )

    puzzle = Puzzle.objects.create(
        mission=mission
    )

    assert str(puzzle) == "Puzzle for Reach the Exit"

# Tests to ensure that mission information renders on practice.html

@pytest.mark.django_db
def test_practice_renders_mission(client):
    Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit.",
        instructions="Use loops to reach the exit."
    )

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert b"Reach the Exit" in response.content
    assert b"Guide the character to the exit." in response.content
    assert b"Use loops to reach the exit." in response.content
    assert b"core/practice/dist/practice_app.js" in response.content

@pytest.mark.django_db
def test_practice_renders_newest_mission(client):
    Mission.objects.create(title="Old Mission")
    Mission.objects.create(title="New Mission")

    response = client.get(reverse("core:home"))

    assert b"New Mission" in response.content
    assert b"Old Mission" not in response.content

# AI Mission Generator Tests (fake Ollama client, no real model calls)

def fake_ollama(reply):
    ai = MagicMock()
    ai.chat.return_value = SimpleNamespace(message=SimpleNamespace(content=reply))
    return ai

ZOMBIE_CODE = "repeat until finish\n  if zombie ahead\n    punch\n  move forward"

def zombie_mission(**changes):
    mission = {
        "title": "Zombie Hallway",
        "description": "A zombie blocks the hallway!",
        "instructions": "Use a loop and an if to punch the zombie, then walk to the exit.",
        "intended_code": [{"block": "repeat until finish", "inside": [
            {"block": "if zombie ahead", "inside": ["punch"]},
            "move forward",
        ]}],
        "tests": [{"action": "Punch zombie", "check": "Is punch inside if zombie ahead?", "block": "punch"}],
    }
    mission.update(changes)
    return mission

def zombie_hallway_reply():
    return MissionData(**zombie_mission()).model_dump_json()

@pytest.mark.django_db
def test_generate_mission_saves_ai_output():
    mission = generate_mission("loops", client=fake_ollama(zombie_hallway_reply()))

    saved = Mission.objects.get(pk=mission.pk)
    assert saved.title == "Zombie Hallway"
    assert saved.description == "A zombie blocks the hallway!"
    assert saved.instructions == "Use a loop and an if to punch the zombie, then walk to the exit."

@pytest.mark.django_db
def test_generate_mission_saves_intended_code_and_tests_on_puzzle():
    mission = generate_mission("loops", client=fake_ollama(zombie_hallway_reply()))

    puzzle = Puzzle.objects.get(mission=mission)
    assert puzzle.solution == ZOMBIE_CODE
    assert puzzle.tests == [{"action": "Punch zombie", "check": "Is punch inside if zombie ahead?", "block": "punch"}]

@pytest.mark.django_db
def test_generate_mission_sends_topic_and_schema_to_ai():
    ai = fake_ollama(zombie_hallway_reply())

    generate_mission("while loops", client=ai)

    kwargs = ai.chat.call_args.kwargs
    assert "while loops" in kwargs["messages"][-1]["content"]
    assert kwargs["format"] == MissionData.model_json_schema()

@pytest.mark.django_db
def test_generate_mission_bad_reply_saves_nothing():
    ai = fake_ollama('{"title": "Missing the other fields"}')

    with pytest.raises(MissionGenerationError):
        generate_mission(client=ai)

    assert ai.chat.call_count == MAX_ATTEMPTS
    assert Mission.objects.count() == 0
    assert Puzzle.objects.count() == 0

@pytest.mark.django_db
def test_generate_mission_retries_after_bad_reply():
    ai = MagicMock()
    ai.chat.side_effect = [
        SimpleNamespace(message=SimpleNamespace(content='{"title": "cut off mid')),
        SimpleNamespace(message=SimpleNamespace(content=zombie_hallway_reply())),
    ]

    mission = generate_mission(client=ai)

    assert ai.chat.call_count == 2
    assert mission.title == "Zombie Hallway"

@pytest.mark.django_db
def test_practice_renders_puzzle_checks_and_intended_code(client):
    mission = Mission.objects.create(title="Zombie Dash")
    Puzzle.objects.create(
        mission=mission,
        solution="punch zombie",
        tests=[{"action": "Punch zombie", "check": "Was zombie punched?"}]
    )

    response = client.get(reverse("core:home"))

    assert b"Punch zombie" in response.content
    assert b"Was zombie punched?" in response.content
    assert b"Intended code" in response.content

@pytest.mark.django_db
def test_practice_renders_mission_without_puzzle(client):
    Mission.objects.create(title="Reach the Exit")

    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert b"Checks" not in response.content

@pytest.mark.django_db
def test_practice_renders_without_missions(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert b"No mission available" in response.content

# AI mission rules: only real blocks, sensible nesting, and a punch inside if zombie ahead

def test_mission_rejects_blocks_that_dont_exist():
    with pytest.raises(ValidationError):
        MissionData(**zombie_mission(intended_code=["jump over lava"]))

def test_mission_rejects_punch_outside_if_zombie_ahead():
    with pytest.raises(ValidationError, match="punch inside if zombie ahead"):
        MissionData(**zombie_mission(intended_code=["move forward", "punch"]))

def test_mission_rejects_blocks_after_repeat_until_finish():
    code = zombie_mission()["intended_code"] + ["move forward"]
    with pytest.raises(ValidationError, match="nothing can come after"):
        MissionData(**zombie_mission(intended_code=code))

def test_mission_rejects_test_for_block_not_in_code():
    tests = [{"action": "Turn", "check": "Did it turn?", "block": "turn left"}]
    with pytest.raises(ValidationError, match="not in intended_code"):
        MissionData(**zombie_mission(tests=tests))

def test_mission_schema_limits_ai_to_real_blocks():
    schema = str(MissionData.model_json_schema())
    assert "if zombie ahead" in schema
    assert "punch" in schema

# Block checker: parsing programs and comparing the student's blocks to the intended code

def test_parse_program_tracks_nesting():
    assert parse_program(ZOMBIE_CODE) == [
        ("repeat until finish",),
        ("repeat until finish", "if zombie ahead"),
        ("repeat until finish", "if zombie ahead", "punch"),
        ("repeat until finish", "move forward"),
    ]

def test_parse_program_attaches_else_to_its_if():
    paths = parse_program("if path ahead\n  move forward\nelse\n  turn left")
    assert paths[-1] == ("else (if path ahead)", "turn left")

def test_program_problems_finds_empty_if_and_stray_else():
    problems = program_problems("if zombie ahead\nelse\n  punch")
    assert '"if zombie ahead" needs blocks inside it' in problems

    assert program_problems("move forward\nelse\n  punch") == ['"else" must come right after an if, at the same indent']

def test_check_program_passes_matching_blocks():
    result = check_program(ZOMBIE_CODE, [], ZOMBIE_CODE)
    assert result["passed"]
    assert result["missing"] == []

def test_check_program_allows_extra_blocks():
    student = "repeat until finish\n  if zombie ahead\n    punch\n  turn left\n  move forward"
    assert check_program(ZOMBIE_CODE, [], student)["passed"]

def test_check_program_reports_punch_in_wrong_place():
    student = "repeat until finish\n  punch\n  move forward"
    result = check_program(ZOMBIE_CODE, [{"action": "Punch", "check": "?", "block": "punch"}], student)

    assert not result["passed"]
    assert result["missing"] == ["repeat until finish → if zombie ahead", "repeat until finish → if zombie ahead → punch"]
    assert result["tests"][0]["passed"] is False

def test_check_program_counts_repeated_blocks():
    result = check_program("move forward\nmove forward", [], "move forward")
    assert result["missing"] == ["move forward"]

def test_check_program_skips_tests_without_a_block():
    result = check_program(ZOMBIE_CODE, [{"action": "Punch zombie", "check": "Was zombie punched?"}], "")
    assert result["tests"][0]["passed"] is None

# Check endpoint used by the practice page's "Check my blocks" button

@pytest.fixture
def zombie_puzzle():
    mission = Mission.objects.create(title="Zombie Hallway")
    Puzzle.objects.create(mission=mission, solution=ZOMBIE_CODE,
                          tests=[{"action": "Punch zombie", "check": "?", "block": "punch"}])
    return mission

@pytest.mark.django_db
def test_check_blocks_view_passes_correct_program(client, zombie_puzzle):
    url = reverse("core:check_blocks", args=[zombie_puzzle.id])
    response = client.post(url, {"program": ZOMBIE_CODE}, content_type="application/json")

    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["tests"][0]["passed"] is True

@pytest.mark.django_db
def test_check_blocks_view_reports_missing_blocks(client, zombie_puzzle):
    url = reverse("core:check_blocks", args=[zombie_puzzle.id])
    response = client.post(url, {"program": "move forward"}, content_type="application/json")

    assert response.json()["passed"] is False
    assert "repeat until finish → if zombie ahead → punch" in response.json()["missing"]

@pytest.mark.django_db
def test_check_blocks_view_rejects_bad_request(client, zombie_puzzle):
    url = reverse("core:check_blocks", args=[zombie_puzzle.id])
    response = client.post(url, {"wrong": 1}, content_type="application/json")

    assert response.status_code == 400

@pytest.mark.django_db
def test_check_blocks_view_404s_without_puzzle(client):
    mission = Mission.objects.create(title="No Puzzle")
    response = client.post(reverse("core:check_blocks", args=[mission.id]), {"program": ""}, content_type="application/json")

    assert response.status_code == 404

@pytest.mark.django_db
def test_practice_shows_check_button_for_puzzle(client, zombie_puzzle):
    response = client.get(reverse("core:home"))

    assert b"Check my blocks" in response.content
    assert reverse("core:check_blocks", args=[zombie_puzzle.id]).encode() in response.content
# Map page tests (page change, map loads, level)

def test_map_url_resolves_to_map_path():
    assert reverse("core:map") == "/map/"
    assert reverse("core:home") == "/"

@pytest.mark.django_db
def test_map_page_loads(client):
    response = client.get(reverse("core:map"))

    assert response.status_code == 200
    assert "core/map.html" in [t.name for t in response.templates]

def navLinks(response):
    # hrefs inside the page-nav only, so a logo or footer link can't satisfy the test
    nav = re.search(r'<nav[^>]*page-nav[^>]*>(.*?)</nav>', response.content.decode(), re.DOTALL)
    return re.findall(r'<a[^>]*href="([^"]+)"', nav.group(1))

@pytest.mark.django_db
def test_map_page_nav_links_to_both_pages(client):
    links = navLinks(client.get(reverse("core:map")))

    assert reverse("core:home") in links
    assert reverse("core:map") in links

@pytest.mark.django_db
def test_practice_page_nav_links_to_both_pages(client):
    links = navLinks(client.get(reverse("core:home")))

    assert reverse("core:home") in links
    assert reverse("core:map") in links

@pytest.mark.django_db
def test_nav_links_lead_to_working_pages(client):
    for link in navLinks(client.get(reverse("core:map"))):
        assert client.get(link).status_code == 200

@pytest.mark.django_db
def test_map_page_has_game_elements(client):
    response = client.get(reverse("core:map"))

    for elementId in ["blockly-workspace", "map-visualization", "map-run", "map-reset", "map-status"]:
        assert f'id="{elementId}"'.encode() in response.content

@pytest.mark.django_db
def test_map_page_serves_level_one(client):
    response = client.get(reverse("core:map"))

    assert response.context["level"] == 1

@pytest.mark.django_db
def test_map_page_script_is_built(client):
    response = client.get(reverse("core:map"))

    assert b"core/map/dist/map_app.js" in response.content
    assert finders.find("core/map/dist/map_app.js") is not None
