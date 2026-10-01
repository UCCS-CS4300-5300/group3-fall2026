import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Choice, Mission, Node

SEEDED_TITLES = ["Pharmacy Run", "Radio Tower", "Hospital Generator"]


@pytest.fixture
def mission():
    mission = Mission.objects.create(title="Test Run", summary="A short test mission.", order=99)
    start = Node.objects.create(mission=mission, title="Fork", scene="Two doors.", prompt="Pick one.")
    left = Node.objects.create(
        mission=mission, title="Left Door", scene="A hallway.", prompt="Walk it.",
        map_level=1, success_text="Made it through.",
    )
    end = Node.objects.create(mission=mission, title="Camp", scene="Home again.", prompt="Done.")
    Choice.objects.create(node=start, side=Choice.LEFT, label="Left door", next_node=left)
    Choice.objects.create(node=start, side=Choice.RIGHT, label="Right door", next_node=end)
    Choice.objects.create(node=left, side=Choice.LEFT, label="Go home", next_node=end)
    mission.start_node = start
    mission.save()
    return mission


def node_named(mission, title):
    return mission.nodes.get(title=title)


# Models

@pytest.mark.django_db
def test_node_challenge_and_end_flags(mission):
    assert not node_named(mission, "Fork").is_challenge
    assert node_named(mission, "Left Door").is_challenge
    assert not node_named(mission, "Fork").is_end
    assert node_named(mission, "Camp").is_end


@pytest.mark.django_db
def test_choice_must_stay_in_mission(mission):
    other = Mission.objects.create(title="Other")
    stray = Node.objects.create(mission=other, title="Elsewhere", scene="-", prompt="-")
    choice = Choice(node=node_named(mission, "Camp"), side=Choice.LEFT, label="Wander off", next_node=stray)
    with pytest.raises(ValidationError):
        choice.full_clean()


@pytest.mark.django_db
def test_start_node_must_belong_to_mission(mission):
    other = Mission.objects.create(title="Other", start_node=node_named(mission, "Fork"))
    with pytest.raises(ValidationError):
        other.full_clean()


@pytest.mark.django_db
def test_map_level_must_exist(mission):
    node = node_named(mission, "Left Door")
    node.map_level = 11
    with pytest.raises(ValidationError):
        node.full_clean()


# Seeded missions

@pytest.mark.django_db
def test_seeded_missions_exist_in_order():
    assert list(Mission.objects.values_list("title", flat=True)) == SEEDED_TITLES


@pytest.mark.django_db
@pytest.mark.parametrize("title", SEEDED_TITLES)
def test_seeded_mission_is_playable(title):
    mission = Mission.objects.get(title=title)
    start = mission.start_node
    assert start is not None
    assert sorted(start.choices.values_list("side", flat=True)) == ["left", "right"]

    # Every path from the start reaches an end node, and every node is reachable.
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node.id in seen:
            continue
        seen.add(node.id)
        for node_field in ("scene", "prompt"):
            assert getattr(node, node_field)
        if node.is_challenge:
            assert node.success_text
        stack.extend(choice.next_node for choice in node.choices.all())
    assert seen == set(mission.nodes.values_list("id", flat=True))
    assert any(node.is_end for node in mission.nodes.all())


@pytest.mark.django_db
def test_seeded_missions_get_harder():
    levels = [
        sorted(set(m.nodes.exclude(map_level=None).values_list("map_level", flat=True)))
        for m in Mission.objects.all()
    ]
    assert levels == [[1, 2, 3], [4, 5, 6], [7, 8, 9, 10]]


# Pages

@pytest.mark.django_db
def test_mission_list_page(client, mission):
    Mission.objects.create(title="Hidden Mission", is_active=False)
    r = client.get(reverse("missions:list"))
    assert r.status_code == 200
    assert b"Test Run" in r.content
    assert b"Pharmacy Run" in r.content
    assert b"Hidden Mission" not in r.content


@pytest.mark.django_db
def test_start_redirects_to_start_node(client, mission):
    r = client.get(reverse("missions:start", args=[mission.id]))
    assert r.status_code == 302
    assert r.url == reverse("missions:node", args=[mission.id, mission.start_node_id])


@pytest.mark.django_db
def test_start_without_start_node_is_404(client):
    empty = Mission.objects.create(title="Empty")
    assert client.get(reverse("missions:start", args=[empty.id])).status_code == 404


@pytest.mark.django_db
def test_story_node_page_shows_left_and_right_choices(client, mission):
    start = mission.start_node
    r = client.get(reverse("missions:node", args=[mission.id, start.id]))
    content = r.content.decode()
    assert r.status_code == 200
    assert "Two doors." in content and "Pick one." in content
    assert "Left door" in content and "Right door" in content
    assert reverse("missions:node", args=[mission.id, node_named(mission, "Left Door").id]) in content
    assert "map_app.js" not in content


@pytest.mark.django_db
def test_challenge_node_page_loads_map_level_and_hides_choices(client, mission):
    node = node_named(mission, "Left Door")
    r = client.get(reverse("missions:node", args=[mission.id, node.id]))
    content = r.content.decode()
    assert r.status_code == 200
    assert "window.MAP_LEVEL = 1;" in content
    assert "core/map/dist/map_app.js" in content
    assert "missions/mission_node.js" in content
    assert "data-reveal-on-solve hidden" in content
    assert "Made it through." in content


@pytest.mark.django_db
def test_node_from_another_mission_is_404(client, mission):
    other = Mission.objects.get(title="Pharmacy Run")
    r = client.get(reverse("missions:node", args=[other.id, mission.start_node_id]))
    assert r.status_code == 404


@pytest.mark.django_db
def test_reaching_end_node_completes_mission(client, mission):
    end = node_named(mission, "Camp")
    r = client.get(reverse("missions:node", args=[mission.id, end.id]))
    assert b"Mission complete" in r.content

    listing = client.get(reverse("missions:list")).content.decode()
    test_run_card = listing.split("Test Run")[1].split("</li>")[0]
    assert "Completed" in test_run_card
    assert "Play again" in test_run_card


# API

@pytest.mark.django_db
def test_api_mission_list(client, mission):
    data = client.get(reverse("missions:api_list")).json()
    titles = [m["title"] for m in data["missions"]]
    assert titles == SEEDED_TITLES + ["Test Run"]
    test_run = data["missions"][-1]
    assert test_run == {
        "id": mission.id, "title": "Test Run", "summary": "A short test mission.",
        "start_node": mission.start_node_id, "completed": False,
    }


@pytest.mark.django_db
def test_api_node_json(client, mission):
    start = mission.start_node
    left = node_named(mission, "Left Door")
    data = client.get(reverse("missions:api_node", args=[mission.id, start.id])).json()
    assert data["title"] == "Fork"
    assert data["challenge"] is None
    assert data["is_end"] is False
    assert [(c["side"], c["label"]) for c in data["choices"]] == [("left", "Left door"), ("right", "Right door")]
    assert data["choices"][0]["next_node"] == left.id

    data = client.get(reverse("missions:api_node", args=[mission.id, left.id])).json()
    assert data["challenge"] == {"type": "map", "level": 1}
    assert data["success_text"] == "Made it through."


@pytest.mark.django_db
def test_api_node_from_another_mission_is_404(client, mission):
    other = Mission.objects.get(title="Pharmacy Run")
    r = client.get(reverse("missions:api_node", args=[other.id, mission.start_node_id]))
    assert r.status_code == 404
