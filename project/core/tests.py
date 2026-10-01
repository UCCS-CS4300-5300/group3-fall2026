import pytest
from django.urls import reverse
from django.db import IntegrityError
from .models import Mission
from .models import Puzzle

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