from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from PIL import Image
from .models import RoomDefinition, RoomState
from .lessons import BossLessonVar
from .rooms import (
    advance_from_current_room, create_mission,
    create_room_from_image, open_mission, reset_mission,
    save_current_room, switch_room,
)
from .room_removal import _remove_unused_generated_files, remove_content

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
from .tutorial_ai import load_tutorial, ask_tutor

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
    missions_before = Mission.objects.count()

    with pytest.raises(MissionGenerationError):
        generate_mission(client=ai)

    assert ai.chat.call_count == 3
    assert Mission.objects.count() == missions_before
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
    Mission.objects.all().delete()
    response = client.get(reverse("core:screen"))

    assert response.status_code == 200
    assert b"No mission available" in response.content

# Page routing, navigation, and legacy reference page tests


@pytest.mark.django_db
def test_main_menu_is_start_page_without_blockly(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "core/main-menu.html" in [t.name for t in response.templates]
    assert b"Main Menu" in response.content
    assert b"blockly" not in response.content.lower()
    assert b"<script" not in response.content.lower()
    assert b"Run Program" not in response.content

def navLinks(response):
    # hrefs inside the page-nav only, so a logo or footer link can't satisfy the test
    nav = re.search(r'<nav[^>]*page-nav[^>]*>(.*?)</nav>', response.content.decode(), re.DOTALL)
    return re.findall(r'<a[^>]*href="([^"]+)"', nav.group(1))

@pytest.mark.django_db
def test_empty_screen_has_exit_to_main_menu(client):
    Mission.objects.all().delete()
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

# Program checking


def test_punch_program_reports_zombie_punched(client):
    """POST the original if/punch text and expect HTTP 200 with punched=True."""
    response = client.post(reverse('core:check_program'), {
        'program': 'if zombie\n  punch zombie',
    }, content_type='application/json')
    assert response.status_code == 200
    assert response.json()['punched'] is True


# Room and mission system: core behavior and regression tests

@pytest.fixture
def image_source(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    settings.STATICFILES_DIRS = [tmp_path / 'gen']
    source = tmp_path / 'original.PNG'
    Image.new('RGB', (8, 8), 'blue').save(source)
    return source


def add_room(mission, source):
    return create_room_from_image(
        mission=mission, source_image_path=source, category='School',
        background_name='Chemistry Lab', tutorial_document_path='tutorials/lab.md',
    )


@pytest.fixture
def room_mission():
    mission = Mission.objects.create(title='The Corner Store')
    first = RoomDefinition.objects.create(
        mission=mission, background_asset_path='backgrounds/storefront.jpg',
        tutorial_document_path='tutorials/entrance.md',
    )
    last = RoomDefinition.objects.create(
        mission=mission, background_asset_path='backgrounds/loading-bay.jpg',
        tutorial_document_path='tutorials/loading-bay.md',
    )
    first.next_room = last
    first.save()
    mission.first_room = first
    mission.save()
    return mission, first, last


@pytest.fixture
def opened_mission(room_mission):
    mission, first, last = room_mission
    _, room_state = open_mission(mission_id=mission.pk)
    mission.refresh_from_db()
    return mission, first, last, room_state


@pytest.fixture
def progressed_mission(opened_mission):
    mission, first, last, _ = opened_mission
    RoomState.objects.create(room=last)
    mission.room_states.update(tutorial_read=True, completed=True)
    mission.current_room = last
    mission.save(update_fields=['current_room'])
    return mission, first, last


@pytest.fixture
def room_content(tmp_path, settings):
    settings.BASE_DIR = tmp_path
    mission = Mission.objects.create(title='Building')
    rooms = []
    for index in range(3):
        room = RoomDefinition.objects.create(
            mission=mission, background_asset_path=f'backgrounds/room-{index}.jpg',
            tutorial_document_path=f'tutorials/room-{index}.md',
        )
        RoomState.objects.create(room=room)
        background = tmp_path / 'gen' / room.background_asset_path
        tutorial = tmp_path / 'gen' / room.tutorial_document_path
        background.parent.mkdir(parents=True, exist_ok=True)
        tutorial.parent.mkdir(parents=True, exist_ok=True)
        background.write_text('test background')
        tutorial.write_text('test tutorial')
        if rooms:
            rooms[-1].next_room = room
            rooms[-1].save()
        rooms.append(room)
    mission.first_room = rooms[0]
    mission.current_room = rooms[1]
    mission.save()
    return mission, rooms, tmp_path


def room_ids_in_route(mission):
    """Bound traversal so a broken cycle fails the comparison instead of hanging."""
    room = mission.first_room
    room_ids = []
    for _ in range(mission.rooms.count() + 1):
        if room is None:
            break
        room_ids.append(room.pk)
        room = room.next_room
    return room_ids


@pytest.mark.django_db(transaction=True)
class TestRoomCreation:
    def test_import_copies_the_background_and_preserves_the_source(self, image_source):
        original_bytes = image_source.read_bytes()
        room, _ = add_room(create_mission(), image_source)
        assert (image_source.parent / 'gen' / room.background_asset_path).read_bytes() == original_bytes
        assert image_source.read_bytes() == original_bytes

    def test_first_import_updates_the_caller_and_saved_first_room(self, image_source):
        mission = create_mission()
        room, _ = add_room(mission, image_source)
        assert mission.first_room_id == room.pk
        assert Mission.objects.get(pk=mission.pk).first_room_id == room.pk

    def test_append_follows_room_links_instead_of_creation_order(self, image_source):
        mission = create_mission()
        first, _ = add_room(mission, image_source)
        second, _ = add_room(mission, image_source)
        third, _ = add_room(mission, image_source)
        first.next_room = third
        first.save(update_fields=['next_room'])
        third.next_room = second
        third.save(update_fields=['next_room'])
        second.next_room = None
        second.save(update_fields=['next_room'])
        fourth, _ = add_room(mission, image_source)
        assert room_ids_in_route(mission) == [first.pk, third.pk, second.pk, fourth.pk]

    def test_failed_import_rolls_back_room_creation(self, image_source):
        mission = create_mission()
        with patch('core.rooms.RoomState.objects.create', side_effect=RuntimeError('failed save')):
            with pytest.raises(RuntimeError):
                add_room(mission, image_source)
        assert not mission.rooms.exists()

    def test_failed_import_removes_its_background_copy(self, image_source):
        mission = create_mission()
        with patch('core.rooms.RoomState.objects.create', side_effect=RuntimeError('failed save')):
            with pytest.raises(RuntimeError):
                add_room(mission, image_source)
        assert list((image_source.parent / 'gen/backgrounds').iterdir()) == []

    def test_append_rejects_a_self_loop_without_creating_a_room(self, image_source):
        mission = create_mission()
        first, _ = add_room(mission, image_source)
        first.next_room = first
        first.save(update_fields=['next_room'])
        with pytest.raises(ValueError, match='chain is invalid'):
            add_room(mission, image_source)
        assert mission.rooms.count() == 1

@pytest.mark.django_db(transaction=True)
class TestBossLessonPlacement:
    def test_unknown_boss_lesson_is_rejected_before_creating_a_mission(self):
        with pytest.raises(ValueError, match='Unknown LessonID'):
            create_mission(boss_lesson_id='missing_lesson')
        assert not Mission.objects.filter(boss_lesson_id='missing_lesson').exists()

    def test_first_room_gets_the_boss_selected_by_the_create_mission_command(self, image_source):
        call_command('create_mission', title='Variables mission', boss_lesson_id='boss_variables', stdout=StringIO())
        mission = Mission.objects.get(title='Variables mission')
        room, _ = add_room(mission, image_source)
        assert RoomDefinition.objects.get(pk=room.pk).lesson_id == 'boss_variables'

    def test_appending_a_room_moves_the_boss_from_the_previous_final_room(self, image_source):
        mission = create_mission(boss_lesson_id='boss_variables')
        first, _ = add_room(mission, image_source)
        last, _ = add_room(mission, image_source)
        assert RoomDefinition.objects.get(pk=first.pk).lesson_id == ''
        assert RoomDefinition.objects.get(pk=last.pk).lesson_id == 'boss_variables'

    def test_moving_the_boss_clears_previous_completion_and_requirements(self, image_source):
        mission = create_mission(boss_lesson_id='boss_variables')
        _, old_state = add_room(mission, image_source)
        old_state.completed = True
        old_state.encounter_state = {'lesson_id': 'boss_variables', 'requirements': {'zombie_alive': False}}
        old_state.save()
        add_room(mission, image_source)
        old_state.refresh_from_db()
        assert old_state.completed is False
        assert old_state.encounter_state == {}

    def test_moving_the_boss_clears_its_blocks_and_preserves_other_rooms_blocks(self, image_source):
        mission = create_mission(boss_lesson_id='boss_variables')
        first, _ = add_room(mission, image_source)
        old_boss, _ = add_room(mission, image_source)
        Puzzle.objects.create(mission=mission, workspace_state={str(first.pk): {'keep': True}, str(old_boss.pk): {'old': True}})
        add_room(mission, image_source)
        assert Puzzle.objects.get(mission=mission).workspace_state == {str(first.pk): {'keep': True}}

    def test_removing_the_final_room_moves_the_boss_to_the_previous_room(self, image_source):
        mission = create_mission(boss_lesson_id='boss_variables')
        previous, _ = add_room(mission, image_source)
        last, _ = add_room(mission, image_source)
        remove_content(room_id=last.pk)
        assert list(mission.rooms.filter(lesson_id='boss_variables').values_list('pk', flat=True)) == [previous.pk]

    def test_replacement_boss_room_starts_without_old_completion_or_blocks(self, image_source):
        mission = create_mission(boss_lesson_id='boss_variables')
        previous, state = add_room(mission, image_source)
        last, _ = add_room(mission, image_source)
        state.completed = True
        state.save(update_fields=['completed'])
        Puzzle.objects.create(mission=mission, workspace_state={str(previous.pk): {'old': True}})
        remove_content(room_id=last.pk)
        assert RoomState.objects.get(room=previous).completed is False
        assert Puzzle.objects.get(mission=mission).workspace_state == {}

    def test_removing_an_earlier_room_preserves_the_current_boss_attempt(self, room_content):
        mission, rooms, _ = room_content
        mission.boss_lesson_id = 'boss_variables'
        mission.save(update_fields=['boss_lesson_id'])
        open_mission(mission_id=mission.pk)
        encounter = {'lesson_id': 'boss_variables', 'requirements': {'zombie_alive': False}}
        RoomState.objects.filter(room=rooms[-1]).update(encounter_state=encounter, completed=True)
        remove_content(room_id=rooms[1].pk)
        state = RoomState.objects.get(room=rooms[-1])
        assert state.encounter_state == encounter
        assert state.completed is True

    def test_opening_a_configured_mission_places_the_boss_by_link_order(self, room_content):
        mission, rooms, _ = room_content
        rooms[0].next_room = rooms[2]
        rooms[0].save(update_fields=['next_room'])
        rooms[2].next_room = rooms[1]
        rooms[2].save(update_fields=['next_room'])
        rooms[1].next_room = None
        rooms[1].save(update_fields=['next_room'])
        mission.boss_lesson_id = 'boss_variables'
        mission.save(update_fields=['boss_lesson_id'])
        open_mission(mission_id=mission.pk)
        assert list(mission.rooms.filter(lesson_id='boss_variables').values_list('pk', flat=True)) == [rooms[1].pk]

    def test_boss_placement_rejects_overwriting_a_different_lesson(self, room_mission):
        mission, _, last = room_mission
        mission.boss_lesson_id = 'boss_variables'
        mission.save(update_fields=['boss_lesson_id'])
        last.lesson_id = 'another_lesson'
        last.save(update_fields=['lesson_id'])
        with pytest.raises(ValueError, match='already has a different lesson'):
            open_mission(mission_id=mission.pk)
        assert RoomDefinition.objects.get(pk=last.pk).lesson_id == 'another_lesson'

    def test_migration_enables_the_seeded_variables_mission(self, room_mission):
        from importlib import import_module
        from django.apps import apps

        mission, _, last = room_mission
        mission.description = 'Variables & Data Types'
        mission.save(update_fields=['description'])
        migration = import_module('core.migrations.0010_mission_boss_lesson_id')
        migration.configure_seeded_variables_boss(apps, None)
        assert Mission.objects.get(pk=mission.pk).boss_lesson_id == 'boss_variables'
        assert RoomDefinition.objects.get(pk=last.pk).lesson_id == 'boss_variables'

    def test_migration_leaves_other_lesson_concepts_unconfigured(self, room_mission):
        from importlib import import_module
        from django.apps import apps

        mission, _, _ = room_mission
        mission.description = 'Conditionals'
        mission.save(update_fields=['description'])
        migration = import_module('core.migrations.0010_mission_boss_lesson_id')
        migration.configure_seeded_variables_boss(apps, None)
        assert Mission.objects.get(pk=mission.pk).boss_lesson_id == ''
        assert not mission.rooms.exclude(lesson_id='').exists()


@pytest.mark.django_db(transaction=True)
class TestRoomProgress:
    def test_switch_updates_the_destination_and_callers_current_room(self, opened_mission):
        mission, _, last, room_state = opened_mission
        destination, _ = switch_room(
            mission=mission, current_room_state=room_state, destination_room_id=last.pk,
        )
        assert destination == last
        assert mission.current_room_id == last.pk

    def test_returning_to_a_room_restores_its_progress(self, opened_mission):
        mission, first, last, room_state = opened_mission
        room_state.tutorial_read = True
        room_state.completed = True
        _, last_state = switch_room(
            mission=mission, current_room_state=room_state, destination_room_id=last.pk,
        )
        _, restored = switch_room(
            mission=mission, current_room_state=last_state, destination_room_id=first.pk,
        )
        assert restored.tutorial_read is True
        assert restored.completed is True

    def test_reopening_resumes_the_current_room(self, opened_mission):
        mission, _, last, room_state = opened_mission
        switch_room(mission=mission, current_room_state=room_state, destination_room_id=last.pk)
        assert open_mission(mission_id=mission.pk)[0] == last

    def test_advance_updates_the_destination_and_callers_current_room(self, opened_mission):
        mission, _, last, room_state = opened_mission
        destination, _ = advance_from_current_room(mission=mission, current_room_state=room_state)
        assert destination == last
        assert mission.current_room_id == last.pk

    def test_finishing_returns_to_main_menu_and_clears_current_room(self, progressed_mission):
        mission, _, last = progressed_mission
        destination = advance_from_current_room(mission=mission, current_room_state=last.room_state)
        assert destination == 'main-menu'
        assert Mission.objects.get(pk=mission.pk).current_room_id is None

    def test_finishing_clears_progress_in_every_room(self, progressed_mission):
        mission, _, last = progressed_mission
        advance_from_current_room(mission=mission, current_room_state=last.room_state)
        assert not mission.room_states.filter(tutorial_read=True).exists()
        assert not mission.room_states.filter(completed=True).exists()

    @pytest.mark.parametrize('tutorial_read, completed', [(True, False), (False, True)])
    def test_saving_keeps_the_two_progress_flags_independent(self, opened_mission, tutorial_read, completed):
        mission, first, _, room_state = opened_mission
        RoomState.objects.filter(room=first).update(tutorial_read=True, completed=True)
        room_state.tutorial_read = tutorial_read
        room_state.completed = completed
        save_current_room(mission=mission, current_room_state=room_state)
        restored = RoomState.objects.get(room=first)
        assert restored.tutorial_read is tutorial_read
        assert restored.completed is completed

    def test_empty_mission_cannot_be_opened(self):
        mission = create_mission()
        with pytest.raises(ValueError, match='no rooms'):
            open_mission(mission_id=mission.pk)

    def test_reset_preserves_other_mission_progress(self, room_content, progressed_mission):
        selected, _, _ = room_content
        other, _, _ = progressed_mission
        reset_mission(mission=selected)
        assert not other.room_states.filter(tutorial_read=False).exists()
        assert not other.room_states.filter(completed=False).exists()


@pytest.fixture
def blockly_workspace():
    return {'blocks': {'languageVersion': 0, 'blocks': [
        {'type': 'screen_punch', 'id': 'saved-punch', 'x': 40, 'y': 40},
    ]}}


@pytest.fixture
def variables_boss_room(opened_mission):
    """Return the current test room after saving its LessonID as boss_variables."""
    _, room, _, _ = opened_mission
    room.lesson_id = 'boss_variables'
    room.save(update_fields=['lesson_id'])
    return room


@pytest.fixture
def opened_boss_room_with_requirements(variables_boss_room):
    """Open the variables boss room and return its definition and saved encounter state."""
    return open_mission(mission_id=variables_boss_room.mission_id)


@pytest.mark.django_db
class TestLessonEncounterPersistence:
    def test_opening_a_lesson_room_saves_its_requirements(self, opened_boss_room_with_requirements):
        room, _ = opened_boss_room_with_requirements
        assert RoomState.objects.get(room=room).encounter_state == {
            'lesson_id': 'boss_variables', 'requirements': {'zombie_alive': False},
        }

    def test_screen_refresh_reuses_saved_requirements(self, client, opened_boss_room_with_requirements):
        room, room_state = opened_boss_room_with_requirements
        with patch.object(BossLessonVar, 'default_requirements', {'zombie_alive': True}):
            response = client.get(reverse('core:screen'), {'mission': room.mission_id})
        assert response.status_code == 200
        assert RoomState.objects.get(room=room).encounter_state == room_state.encounter_state

    def test_retry_checks_saved_requirements_without_recreating_them(self, client, opened_boss_room_with_requirements):
        room, room_state = opened_boss_room_with_requirements
        with patch.object(BossLessonVar, 'default_requirements', {'zombie_alive': True}):
            response = client.post(reverse('core:check_program'), {
                'mission_id': room.mission_id, 'room_id': room.pk,
                'assignments': [{'variable': 'zombie_alive', 'value': False}],
            }, content_type='application/json')
        assert response.json()['passed'] is True
        assert RoomState.objects.get(room=room).encounter_state == room_state.encounter_state

    def test_exit_and_reopen_preserve_saved_requirements(self, client, opened_boss_room_with_requirements):
        room, room_state = opened_boss_room_with_requirements
        client.post(reverse('core:exit-mission', args=[room.mission_id]))
        with patch.object(BossLessonVar, 'default_requirements', {'zombie_alive': True}):
            response = client.get(reverse('core:screen'), {'mission': room.mission_id})
        assert response.status_code == 200
        assert RoomState.objects.get(room=room).encounter_state == room_state.encounter_state

    def test_reset_clears_requirements_in_every_room(self, opened_boss_room_with_requirements, room_mission):
        room, room_state = opened_boss_room_with_requirements
        mission, _, last = room_mission
        RoomState.objects.create(room=last, encounter_state=room_state.encounter_state)
        reset_mission(mission=mission)
        assert not mission.room_states.exclude(encounter_state={}).exists()
        assert RoomDefinition.objects.get(pk=room.pk).lesson_id == 'boss_variables'

    def test_reset_preserves_other_missions_requirements(self, opened_boss_room_with_requirements, room_content):
        room, room_state = opened_boss_room_with_requirements
        other, _, _ = room_content
        other.room_states.update(encounter_state=room_state.encounter_state)
        reset_mission(mission=room.mission)
        assert not other.room_states.exclude(encounter_state=room_state.encounter_state).exists()

    def test_reopening_after_reset_creates_new_requirements(self, opened_boss_room_with_requirements):
        room, _ = opened_boss_room_with_requirements
        reset_mission(mission=room.mission)
        _, room_state = open_mission(mission_id=room.mission_id)
        assert room_state.encounter_state == {
            'lesson_id': 'boss_variables', 'requirements': {'zombie_alive': False},
        }

    def test_saving_room_progress_preserves_requirements(self, opened_boss_room_with_requirements):
        room, room_state = opened_boss_room_with_requirements
        room_state.tutorial_read = True
        save_current_room(mission=room.mission, current_room_state=room_state)
        assert RoomState.objects.get(room=room).encounter_state == room_state.encounter_state

    def test_rooms_without_a_lesson_have_no_encounter_requirements(self, opened_mission):
        _, room, _, _ = opened_mission
        assert RoomState.objects.get(room=room).encounter_state == {}


@pytest.mark.django_db
class TestBossCompletion:
    def test_passing_the_boss_saves_completion(self, client, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        response = client.post(reverse('core:check_program'), {
            'mission_id': room.mission_id, 'room_id': room.pk,
            'assignments': [{'variable': 'zombie_alive', 'value': False}],
        }, content_type='application/json')
        assert response.status_code == 200
        assert RoomState.objects.get(room=room).completed is True

    def test_slowing_the_boss_does_not_save_completion(self, client, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        response = client.post(reverse('core:check_program'), {
            'mission_id': room.mission_id, 'room_id': room.pk,
            'assignments': [{'variable': 'zombie_speed', 'value': 3}],
        }, content_type='application/json')
        assert response.json()['passed'] is False
        assert RoomState.objects.get(room=room).completed is False

    def test_failed_retry_preserves_a_saved_success(self, client, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        client.post(reverse('core:check_program'), {
            'mission_id': room.mission_id, 'room_id': room.pk,
            'assignments': [{'variable': 'zombie_alive', 'value': False}],
        }, content_type='application/json')
        response = client.post(reverse('core:check_program'), {
            'mission_id': room.mission_id, 'room_id': room.pk, 'assignments': [],
        }, content_type='application/json')
        assert response.json()['passed'] is False
        assert RoomState.objects.get(room=room).completed is True

    def test_unsolved_boss_stays_open_with_feedback_even_if_request_claims_completion(self, client, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        response = client.post(reverse('core:next-room', args=[room.mission_id]), {
            'room_id': room.pk, 'completed': True,
        }, follow=True)
        assert b'Defeat the boss before leaving this room.' in response.content
        assert Mission.objects.get(pk=room.mission_id).current_room_id == room.pk

    def test_navigation_rejects_an_unsaved_completion_flag(self, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        room_state = RoomState.objects.get(room=room)
        room_state.completed = True
        with pytest.raises(ValueError, match='Defeat the boss'):
            advance_from_current_room(mission=room.mission, current_room_state=room_state)
        assert RoomState.objects.get(room=room).completed is False

    def test_saved_boss_success_allows_finishing_the_mission(self, client, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        client.post(reverse('core:check_program'), {
            'mission_id': room.mission_id, 'room_id': room.pk,
            'assignments': [{'variable': 'zombie_alive', 'value': False}],
        }, content_type='application/json')
        response = client.post(reverse('core:next-room', args=[room.mission_id]), {'room_id': room.pk})
        assert response.url == reverse('core:main-menu')
        assert Mission.objects.get(pk=room.mission_id).current_room_id is None

    def test_exit_and_reopen_preserve_saved_boss_success(self, client, unsolved_final_boss_room):
        room = unsolved_final_boss_room
        client.post(reverse('core:check_program'), {
            'mission_id': room.mission_id, 'room_id': room.pk,
            'assignments': [{'variable': 'zombie_alive', 'value': False}],
        }, content_type='application/json')
        client.post(reverse('core:exit-mission', args=[room.mission_id]))
        response = client.get(reverse('core:screen'), {'mission': room.mission_id})
        assert response.context['room'] == room
        assert RoomState.objects.get(room=room).completed is True


@pytest.fixture
def unsolved_final_boss_room(progressed_mission):
    """Return the current final boss room with saved completion cleared for the attempt."""
    mission, _, room = progressed_mission
    mission.boss_lesson_id = 'boss_variables'
    mission.save(update_fields=['boss_lesson_id'])
    room.lesson_id = 'boss_variables'
    room.save(update_fields=['lesson_id'])
    RoomState.objects.filter(room=room).update(completed=False)
    return room


@pytest.mark.django_db
class TestLessonRunRequests:
    def test_alive_assignment_response_keeps_default_speed(self, client, variables_boss_room):
        """Submit alive=False; expect False in the response while speed remains 10."""
        response = client.post(reverse('core:check_program'), {
            'mission_id': variables_boss_room.mission_id,
            'room_id': variables_boss_room.pk,
            'assignments': [{'variable': 'zombie_alive', 'value': False}],
        }, content_type='application/json')
        assert response.status_code == 200
        assert response.json()['variables'] == {'zombie_alive': False, 'zombie_speed': 10}

    def test_second_submission_returns_new_speed(self, client, variables_boss_room):
        client.post(reverse('core:check_program'), {
            'mission_id': variables_boss_room.mission_id,
            'room_id': variables_boss_room.pk,
            'assignments': [{'variable': 'zombie_speed', 'value': 3}],
        }, content_type='application/json')
        response = client.post(reverse('core:check_program'), {
            'mission_id': variables_boss_room.mission_id,
            'room_id': variables_boss_room.pk,
            'assignments': [{'variable': 'zombie_speed', 'value': 7}],
        }, content_type='application/json')
        assert response.json()['variables']['zombie_speed'] == 7

    def test_zero_speed_request_returns_validation_error(self, client, variables_boss_room):
        response = client.post(reverse('core:check_program'), {
            'mission_id': variables_boss_room.mission_id,
            'room_id': variables_boss_room.pk,
            'assignments': [{'variable': 'zombie_speed', 'value': 0}],
        }, content_type='application/json')
        assert response.status_code == 400
        assert response.json()['error'] == 'Zombie speed must be at least 1.'


@pytest.mark.django_db
class TestRoomRequests:
    @pytest.mark.parametrize('lesson_id, expected_text, excluded_text', [
        ('boss_variables', BossLessonVar.instructions, 'Follow the mission puzzle instructions.'),
        ('', 'Follow the mission puzzle instructions.', BossLessonVar.instructions),
    ])
    def test_screen_shows_instructions_for_the_selected_lesson(self, client, room_mission, lesson_id, expected_text, excluded_text):
        mission, first, _ = room_mission
        mission.instructions = 'Follow the mission puzzle instructions.'
        mission.save(update_fields=['instructions'])
        first.lesson_id = lesson_id
        first.save(update_fields=['lesson_id'])
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        assert expected_text.encode() in response.content
        assert excluded_text.encode() not in response.content

    @pytest.mark.parametrize('lesson_id, shows_mission_puzzle', [('', True), ('boss_variables', False)])
    def test_screen_shows_mission_checks_and_solution_only_without_a_lesson(self, client, room_mission, lesson_id, shows_mission_puzzle):
        mission, first, _ = room_mission
        first.lesson_id = lesson_id
        first.save(update_fields=['lesson_id'])
        Puzzle.objects.create(
            mission=mission, solution='if zombie\n  punch zombie',
            tests=[{'action': 'Punch zombie', 'check': 'Mission punch check'}],
        )
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        assert (b'Mission punch check' in response.content) is shows_mission_puzzle
        assert (b'if zombie' in response.content) is shows_mission_puzzle

    @pytest.mark.parametrize('lesson_id', ['', 'boss_variables'])
    def test_screen_renders_rooms_with_or_without_a_lesson(self, client, room_mission, lesson_id):
        mission, first, _ = room_mission
        first.lesson_id = lesson_id
        first.save(update_fields=['lesson_id'])
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        assert response.status_code == 200
        assert 'no-store' in response.headers['Cache-Control']

    @pytest.mark.parametrize('lesson_id, expected_blocks', [
        ('', None),
        ('boss_variables', [
            'logic_true', 'logic_false', 'math_integer',
            'screen_zombie_alive', 'screen_zombie_speed',
        ]),
    ])
    def test_screen_embeds_block_types_for_room_lesson(self, client, room_mission, lesson_id, expected_blocks):
        mission, first, _ = room_mission
        first.lesson_id = lesson_id
        first.save(update_fields=['lesson_id'])
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        block_data = re.search(
            r'<script id="screen-available-blocks" type="application/json">(.*?)</script>',
            response.content.decode(), re.DOTALL,
        )
        assert block_data is not None
        assert json.loads(block_data.group(1)) == expected_blocks

    def test_screen_uses_the_requested_mission_background(self, client, room_mission):
        mission, first, _ = room_mission
        Mission.objects.create(title='Newer mission')
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        assert response.context['room'] == first
        assert b'/static/backgrounds/storefront.jpg' in response.content

    def test_exit_returns_to_menu_and_resumes_current_room(self, client, progressed_mission):
        mission, _, last = progressed_mission
        response = client.post(reverse('core:exit-mission', args=[mission.pk]))
        assert response.url == reverse('core:main-menu')
        assert client.get(reverse('core:screen'), {'mission': mission.pk}).context['room'] == last

    def test_exit_preserves_progress_in_every_room(self, client, progressed_mission):
        mission, _, _ = progressed_mission
        client.post(reverse('core:exit-mission', args=[mission.pk]))
        assert not mission.room_states.filter(tutorial_read=False).exists()
        assert not mission.room_states.filter(completed=False).exists()

    def test_exit_restores_placed_blocks_on_reopening(self, client, opened_mission, blockly_workspace):
        mission, _, _, _ = opened_mission
        client.post(reverse('core:exit-mission', args=[mission.pk]), {
            'workspace_json': json.dumps(blockly_workspace),
        })
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        assert response.context['workspace_state'] == blockly_workspace

    def test_return_to_main_menu_clears_saved_blocks(self, client, progressed_mission, blockly_workspace):
        mission, first, last = progressed_mission
        Puzzle.objects.create(mission=mission, workspace_state={
            str(first.pk): blockly_workspace, str(last.pk): blockly_workspace,
        })
        response = client.post(reverse('core:next-room', args=[mission.pk]), {
            'room_id': last.pk, 'workspace_json': json.dumps(blockly_workspace),
        })
        assert response.url == reverse('core:main-menu')
        assert Puzzle.objects.get(mission=mission).workspace_state == {}

    def test_next_room_starts_with_an_empty_workspace(self, client, opened_mission, blockly_workspace):
        mission, first, last, _ = opened_mission
        response = client.post(reverse('core:next-room', args=[mission.pk]), {
            'room_id': first.pk, 'workspace_json': json.dumps(blockly_workspace),
        }, follow=True)
        assert response.context['room'] == last
        assert response.context['workspace_state'] == {}

    def test_saving_another_room_keeps_the_first_rooms_blocks(self, client, opened_mission, blockly_workspace):
        mission, first, last, _ = opened_mission
        client.post(reverse('core:next-room', args=[mission.pk]), {
            'room_id': first.pk, 'workspace_json': json.dumps(blockly_workspace),
        })
        client.post(reverse('core:exit-mission', args=[mission.pk]), {
            'workspace_json': json.dumps({'blocks': {'languageVersion': 0, 'blocks': [
                {'type': 'screen_zombie', 'id': 'room-two-zombie', 'x': 60, 'y': 80},
            ]}}),
        })
        switch_room(
            mission=mission, current_room_state=RoomState.objects.get(room=last),
            destination_room_id=first.pk,
        )
        response = client.get(reverse('core:screen'), {'mission': mission.pk})
        assert response.context['workspace_state'] == blockly_workspace

    def test_unknown_mission_returns_404(self, client):
        assert client.get(reverse('core:screen'), {'mission': 99999}).status_code == 404


@pytest.mark.django_db(transaction=True)
class TestRoomRemoval:
    @pytest.mark.parametrize('index', [0, 1, 2])
    def test_remove_command_repairs_route_and_current_room(self, room_content, index):
        mission, rooms, _ = room_content
        removed = rooms[index]
        mission.current_room = removed
        mission.save(update_fields=['current_room'])
        remaining_ids = [room.pk for room in rooms if room.pk != removed.pk]
        expected_current = rooms[index + 1].pk if index < 2 else rooms[0].pk
        call_command('remove_content', room_id=removed.pk, stdout=StringIO())
        mission.refresh_from_db()
        assert room_ids_in_route(mission) == remaining_ids
        assert mission.current_room_id == expected_current

    def test_removing_the_only_room_clears_mission_references(self, image_source):
        mission = create_mission()
        room, _ = add_room(mission, image_source)
        mission.current_room = room
        mission.save(update_fields=['current_room'])
        remove_content(room_id=room.pk)
        mission.refresh_from_db()
        assert mission.first_room_id is None
        assert mission.current_room_id is None

    def test_cleanup_skips_original_files_and_continues(self, room_content):
        mission, rooms, root = room_content
        original = root / 'original.jpg'
        original.write_text('source image')
        unused = rooms[0].tutorial_document_path
        mission.delete()
        paths = MagicMock(spec=set)
        paths.__iter__.return_value = iter([str(original), unused])
        _remove_unused_generated_files(paths)
        assert original.read_text() == 'source image'
        assert not (root / 'gen' / unused).exists()

    def test_cleanup_skips_shared_files_and_continues(self, room_content):
        mission, rooms, root = room_content
        shared = rooms[0].tutorial_document_path
        unused = rooms[1].tutorial_document_path
        RoomDefinition.objects.create(
            mission=create_mission(title='Other'), tutorial_document_path=shared,
            background_asset_path='backgrounds/other.jpg',
        )
        mission.delete()
        paths = MagicMock(spec=set)
        paths.__iter__.return_value = iter([shared, unused])
        _remove_unused_generated_files(paths)
        assert (root / 'gen' / shared).exists()
        assert not (root / 'gen' / unused).exists()

    def test_remove_mission_command_preserves_other_missions(self, room_content):
        mission, _, _ = room_content
        mission_id = mission.pk
        other = create_mission(title='Other')
        call_command('remove_content', mission_title=mission.title, stdout=StringIO())
        assert not Mission.objects.filter(pk=mission_id).exists()
        assert Mission.objects.filter(pk=other.pk).exists()

    def test_remove_all_command_clears_missions_and_cleans_only_referenced_files(self, room_content):
        _, _, root = room_content
        create_mission(title='Empty mission')
        unrelated = root / 'gen/backgrounds/not-imported.jpg'
        unrelated.write_text('unrelated file')
        call_command('remove_content', remove_all=True, stdout=StringIO())
        remaining_files = [path for path in (root / 'gen').rglob('*') if path.is_file()]
        assert not Mission.objects.exists()
        assert remaining_files == [unrelated]
        mission = create_mission(title='Fresh mission')
        assert mission.pk == 1
        room = RoomDefinition.objects.create(
            mission=mission, background_asset_path='backgrounds/fresh.jpg',
            tutorial_document_path='tutorials/fresh.md',
        )
        assert room.pk == 1


# New AI Tutorial tests 

def test_load_tutorial():
    lesson = load_tutorial("conditionals")

    assert "Conditional statements" in lesson 
    assert "punch zombie" in lesson

def test_load_unknown_tutorial():
    with pytest.raises(ValueError):
        load_tutorial("variables")

def test_ask_tutor_uses_tutorial_document():
    # Mocks ollama so the tests dont require a running model 
    ai = MagicMock()
    ai.chat.return_value = SimpleNamespace(
        message=SimpleNamespace(
            content="An if statement checks a condition."
            )
        )

    answer = ask_tutor(
        "conditionals", "What does an if statement do?",
        client=ai,
    )

    messages = ai.chat.call_args.kwargs["messages"]

    assert "punch zombie" in messages[0]["content"]
    assert messages[1]["content"] == "What does an if statement do?"
    assert answer == "An if statement checks a condition."
