import pytest
import json
import re
from types import SimpleNamespace
from unittest.mock import MagicMock
from django.urls import reverse
from django.contrib.staticfiles import finders
from django.db import IntegrityError
from .models import Mission
from .models import Puzzle
from .mission_generator import MissionData, MissionGenerationError, generate_mission

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

# Tests to ensure that mission information renders on screen.html

@pytest.mark.django_db
def test_screen_renders_mission(client):
    Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit.",
        instructions="Use loops to reach the exit."
    )

    response = client.get(reverse("core:screen"))

    assert response.status_code == 200
    assert b"Reach the Exit" in response.content
    assert b"Guide the character to the exit." in response.content
    assert b"Use loops to reach the exit." in response.content
    assert b"core/screen/dist/screen.js" in response.content
    assert finders.find("core/screen/dist/screen.js") is not None

@pytest.mark.django_db
def test_screen_renders_newest_mission(client):
    Mission.objects.create(title="Old Mission")
    Mission.objects.create(title="New Mission")

    response = client.get(reverse("core:screen"))

    assert b"New Mission" in response.content
    assert b"Old Mission" not in response.content

# AI Mission Generator Tests (fake Ollama client, no real model calls)

def fake_ollama(reply):
    ai = MagicMock()
    ai.chat.return_value = SimpleNamespace(message=SimpleNamespace(content=reply))
    return ai

def lava_leap_reply():
    return MissionData(
        title="Lava Leap",
        description="The floor is lava!",
        instructions="Use a loop to hop across the stones.",
        tests=[{"action": "Jump over lava", "check": "Did the character cross the lava?"}]
    ).model_dump_json()

@pytest.mark.django_db
def test_generate_mission_saves_ai_output():
    mission = generate_mission("loops", client=fake_ollama(lava_leap_reply()))

    saved = Mission.objects.get(pk=mission.pk)
    assert saved.title == "Lava Leap"
    assert saved.description == "The floor is lava!"
    assert saved.instructions == "Use a loop to hop across the stones."

@pytest.mark.django_db
def test_generate_mission_saves_intended_code_and_tests_on_puzzle():
    mission = generate_mission("loops", client=fake_ollama(lava_leap_reply()))

    puzzle = Puzzle.objects.get(mission=mission)
    assert puzzle.solution == "if zombie\n  punch zombie"
    assert puzzle.tests == [{"action": "Jump over lava", "check": "Did the character cross the lava?"}]

@pytest.mark.django_db
def test_generate_mission_sends_topic_and_schema_to_ai():
    ai = fake_ollama(lava_leap_reply())

    generate_mission("while loops", client=ai)

    kwargs = ai.chat.call_args.kwargs
    assert "while loops" in kwargs["messages"][-1]["content"]
    assert kwargs["format"] == MissionData.model_json_schema()

@pytest.mark.django_db
def test_generate_mission_bad_reply_saves_nothing():
    ai = fake_ollama('{"title": "Missing the other fields"}')

    with pytest.raises(MissionGenerationError):
        generate_mission(client=ai)

    assert ai.chat.call_count == 3
    assert Mission.objects.count() == 0
    assert Puzzle.objects.count() == 0

@pytest.mark.django_db
def test_generate_mission_retries_after_bad_reply():
    ai = MagicMock()
    ai.chat.side_effect = [
        SimpleNamespace(message=SimpleNamespace(content='{"title": "cut off mid')),
        SimpleNamespace(message=SimpleNamespace(content=lava_leap_reply())),
    ]

    mission = generate_mission(client=ai)

    assert ai.chat.call_count == 2
    assert mission.title == "Lava Leap"

def test_ai_is_not_asked_for_code():
    assert "intended_code" not in MissionData.model_json_schema()["properties"]

@pytest.mark.django_db
def test_generate_mission_ignores_code_from_ai():
    reply = json.loads(lava_leap_reply())
    reply["intended_code"] = "if zombie:\n  jump over lava\nelse:\n  move_forward"
    ai = fake_ollama(json.dumps(reply))

    mission = generate_mission(client=ai)

    assert ai.chat.call_count == 1
    assert Puzzle.objects.get(mission=mission).solution == "if zombie\n  punch zombie"

@pytest.mark.django_db
def test_screen_renders_puzzle_checks_and_intended_code(client):
    mission = Mission.objects.create(title="Zombie Dash")
    Puzzle.objects.create(
        mission=mission,
        solution="punch zombie",
        tests=[{"action": "Punch zombie", "check": "Was zombie punched?"}]
    )

    response = client.get(reverse("core:screen"))

    assert b"Punch zombie" in response.content
    assert b"Was zombie punched?" in response.content
    assert b"Intended code" in response.content

@pytest.mark.django_db
def test_screen_renders_mission_without_puzzle(client):
    Mission.objects.create(title="Reach the Exit")

    response = client.get(reverse("core:screen"))

    assert response.status_code == 200
    assert b"Checks" not in response.content

@pytest.mark.django_db
def test_screen_renders_without_missions(client):
    response = client.get(reverse("core:screen"))

    assert response.status_code == 200
    assert b"No mission available" in response.content

# Page routing, navigation, and legacy reference page tests

def test_page_urls():
    assert reverse("core:main-menu") == "/"
    assert reverse("core:old-map") == "/old-map/"
    assert reverse("core:screen") == "/screen/"


@pytest.mark.django_db
def test_main_menu_is_start_page_without_blockly(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "core/main-menu.html" in [t.name for t in response.templates]
    assert b"Main Menu" in response.content
    assert b"blockly" not in response.content.lower()
    assert b"<script" not in response.content.lower()
    assert b"Run Program" not in response.content

@pytest.mark.django_db
def test_old_map_page_loads(client):
    response = client.get(reverse("core:old-map"))

    assert response.status_code == 200
    assert "core/old-map.html" in [t.name for t in response.templates]

def navLinks(response):
    # hrefs inside the page-nav only, so a logo or footer link can't satisfy the test
    nav = re.search(r'<nav[^>]*page-nav[^>]*>(.*?)</nav>', response.content.decode(), re.DOTALL)
    return re.findall(r'<a[^>]*href="([^"]+)"', nav.group(1))

@pytest.mark.django_db
def test_old_map_page_nav_links_to_both_pages(client):
    links = navLinks(client.get(reverse("core:old-map")))

    assert reverse("core:main-menu") in links
    assert reverse("core:old-map") in links

@pytest.mark.django_db
def test_empty_screen_has_exit_to_main_menu(client):
    links = navLinks(client.get(reverse("core:screen")))

    assert reverse("core:screen") not in links
    assert reverse("core:main-menu") in links


@pytest.mark.django_db
def test_main_menu_has_no_direct_screen_navigation(client):
    links = navLinks(client.get(reverse("core:main-menu")))

    assert reverse("core:main-menu") in links
    assert reverse("core:screen") not in links

@pytest.mark.django_db
def test_nav_links_lead_to_working_pages(client):
    for page in ["core:main-menu", "core:screen", "core:old-map"]:
        for link in navLinks(client.get(reverse(page))):
            assert client.get(link).status_code == 200

@pytest.mark.django_db
def test_old_map_page_has_game_elements(client):
    response = client.get(reverse("core:old-map"))

    for elementId in ["blockly-workspace", "old-map-visualization", "old-map-run", "old-map-reset", "old-map-status"]:
        assert f'id="{elementId}"'.encode() in response.content

@pytest.mark.django_db
def test_old_map_page_serves_level_one(client):
    response = client.get(reverse("core:old-map"))

    assert response.context["level"] == 1

@pytest.mark.django_db
def test_old_map_page_script_is_built(client):
    response = client.get(reverse("core:old-map"))

    assert b"core/old-map/dist/old-map_app.js" in response.content
    assert finders.find("core/old-map/dist/old-map_app.js") is not None
