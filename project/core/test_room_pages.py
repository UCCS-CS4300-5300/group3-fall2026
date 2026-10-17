import pytest
from django.test import Client
from django.urls import reverse

from .models import Mission, RoomDefinition, RoomState

pytestmark = pytest.mark.django_db


@pytest.fixture
def room_mission():
    mission = Mission.objects.create(title="The Corner Store")
    first = RoomDefinition.objects.create(
        mission=mission, background_asset_path="backgrounds/storefront.jpg",
        tutorial_document_path="tutorials/entrance.md",
    )
    last = RoomDefinition.objects.create(
        mission=mission, background_asset_path="backgrounds/loading-bay.jpg",
        tutorial_document_path="tutorials/loading-bay.md",
    )
    first.next_room = last
    first.save()
    mission.first_room = first
    mission.save()
    return mission, first, last


def test_menu_button_opens_selected_mission_background(client, room_mission):
    mission, first, _ = room_mission
    Mission.objects.create(title="Newer mission")
    menu = client.get(reverse("core:main-menu"))
    assert f'/screen/?mission={mission.pk}'.encode() in menu.content
    response = client.get(reverse("core:screen"), {"mission": mission.pk})
    assert response.context["room"] == first
    assert b'/static/backgrounds/storefront.jpg' in response.content
    assert b'Next Room' in response.content


def test_next_button_changes_background_then_returns_to_menu(client, room_mission):
    mission, first, last = room_mission
    client.get(reverse("core:screen"), {"mission": mission.pk})
    room_state = RoomState.objects.get(room=first)
    room_state.tutorial_read = True
    room_state.save()
    next_url = reverse("core:next-room", args=[mission.pk])
    response = client.post(next_url, {"room_id": first.pk}, follow=True)
    assert response.context["room"] == last
    assert b'/static/backgrounds/loading-bay.jpg' in response.content
    assert b'Return to Main Menu' in response.content
    assert RoomState.objects.get(room=first).tutorial_read
    response = client.post(next_url, {"room_id": last.pk})
    assert response.status_code == 302
    assert response.url == reverse("core:main-menu")
    mission.refresh_from_db()
    assert mission.current_room_id is None
    assert not mission.room_states.filter(tutorial_read=True).exists()
    assert client.get(reverse("core:screen"), {"mission": mission.pk}).context["room"] == first


def test_old_submission_cannot_skip_a_room(client, room_mission):
    mission, first, last = room_mission
    client.get(reverse("core:screen"), {"mission": mission.pk})
    next_url = reverse("core:next-room", args=[mission.pk])
    client.post(next_url, {"room_id": first.pk})
    assert client.post(next_url, {"room_id": first.pk}).status_code == 400
    mission.refresh_from_db()
    assert mission.current_room_id == last.pk


def test_next_requires_post_and_csrf(room_mission):
    mission, first, _ = room_mission
    client = Client(enforce_csrf_checks=True)
    url = reverse("core:next-room", args=[mission.pk])
    assert client.get(url).status_code == 405
    assert client.post(url, {"room_id": first.pk}).status_code == 403


def test_unknown_mission_returns_404(client):
    assert client.get(reverse("core:screen"), {"mission": 99999}).status_code == 404


def test_exit_resets_all_rooms_and_restarts_at_first(client, room_mission):
    mission, first, last = room_mission
    client.get(reverse("core:screen"), {"mission": mission.pk})
    client.post(reverse("core:next-room", args=[mission.pk]), {"room_id": first.pk})
    mission.room_states.update(tutorial_read=True, completed=True)
    response = client.post(reverse("core:exit-mission", args=[mission.pk]))
    assert response.status_code == 302
    assert response.url == reverse("core:main-menu")
    mission.refresh_from_db()
    assert mission.current_room_id is None
    assert mission.first_room_id == first.pk
    assert mission.rooms.count() == 2
    assert not mission.room_states.filter(tutorial_read=True).exists()
    assert not mission.room_states.filter(completed=True).exists()
    assert client.get(reverse("core:screen"), {"mission": mission.pk}).context["room"] == first


def test_exit_requires_post_and_csrf(room_mission):
    mission, _, _ = room_mission
    client = Client(enforce_csrf_checks=True)
    url = reverse("core:exit-mission", args=[mission.pk])
    assert client.get(url).status_code == 405
    assert client.post(url).status_code == 403


def test_screen_has_exit_instead_of_screen_navigation(client, room_mission):
    mission, _, _ = room_mission
    response = client.get(reverse("core:screen"), {"mission": mission.pk})
    assert b'>Exit</button>' in response.content
    assert b'>Screen</a>' not in response.content
    assert reverse("core:exit-mission", args=[mission.pk]).encode() in response.content
    assert b'>Screen</a>' not in client.get(reverse("core:main-menu")).content
