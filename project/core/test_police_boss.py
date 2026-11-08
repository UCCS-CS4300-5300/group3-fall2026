"""Essential Stage 3 checks; animation and pointer testing comes later."""

from copy import deepcopy
from itertools import count

import pytest
from django.urls import reverse

from .models import Mission, RoomDefinition, RoomState
from .bosses.conditionals import BOSS_ID, evaluate_workspace_program


@pytest.fixture
def program():
    ids = count()

    def block(kind, inputs=None, fields=None):
        return {"type": kind, "id": f"block-{next(ids)}", "fields": fields or {},
                "inputs": {key: {"block": value} for key, value in (inputs or {}).items()}}

    noise = block("boss_make_noise")
    noise["next"] = {"block": block("controls_if", {
        "IF0": block("boss_not_close"), "DO0": block("boss_wait"),
    })}
    detection = block("controls_if", {"IF0": block("boss_undetected"), "DO0": noise})
    approach = block("controls_ifelse", {
        "IF0": block("boss_not_close"), "DO0": block("boss_step_forward"),
        "ELSE": block("boss_hold_position"),
    })
    cases = [block("boss_case", {"DO": block("boss_" + defense)}, {"ATTACK": attack})
             for attack, defense in [("grab", "dodge"), ("swipe", "block"), ("lunge", "step_back"),
                                     ("high_swing", "duck"), ("charge", "step_aside")]]
    for first, second in zip(cases, cases[1:]):
        first["next"] = {"block": second}
    choice = block("boss_switch", {"CASES": cases[0]})
    finish = block("boss_attack")
    for first, second in zip([detection, approach, choice], [approach, choice, finish]):
        first["next"] = {"block": second}
    return {"blocks": {"languageVersion": 0, "blocks": [detection]}}


def first_case(program):
    choice = program["blocks"]["blocks"][0]["next"]["block"]["next"]["block"]
    return choice["inputs"]["CASES"]["block"]


def test_intended_program_wins_without_case_fallthrough(program):
    result = evaluate_workspace_program(program)
    actions = [event["result"] for event in result["events"] if event["kind"] == "action"]
    assert result["passed"] is True
    assert actions == ["make_noise", "wait", "step_forward", "step_back", "attack"]


def test_actions_advance_five_units_and_decisions_consume_none(program):
    result = evaluate_workspace_program(program)
    actions = [event for event in result["events"] if event["kind"] == "action"]
    assert [event["after"]["progress"] for event in actions] == [0.2, 0.4, 0.6, 0.8, 1.0]
    assert all(
        event["after"]["turn"] - event["before"]["turn"] == (event["kind"] == "action")
        for event in result["events"]
    )


def test_each_evaluation_starts_from_the_same_state(program):
    assert evaluate_workspace_program(program) == evaluate_workspace_program(program)


def test_wrong_defense_stops_the_program_before_its_finishing_hit(program):
    invalid = deepcopy(program)
    grab = first_case(invalid)
    lunge = grab["next"]["block"]["next"]["block"]
    grab["inputs"]["DO"], lunge["inputs"]["DO"] = lunge["inputs"]["DO"], grab["inputs"]["DO"]
    result = evaluate_workspace_program(invalid)
    assert result["passed"] is False
    assert not any(event["result"] == "attack" for event in result["events"])


def test_placed_if_blocks_cannot_exceed_the_allowance(program):
    excess = deepcopy(program)
    for index in range(2):
        excess["blocks"]["blocks"][0] = {
            "type": "controls_if", "id": f"extra-if-{index}", "inputs": {
                "IF0": {"block": {"type": "boss_undetected", "id": f"extra-condition-{index}"}},
                "DO0": {"block": excess["blocks"]["blocks"][0]},
            },
        }
    with pytest.raises(ValueError, match="Too many if blocks"):
        evaluate_workspace_program(excess)


def test_duplicate_case_names_are_rejected(program):
    first_case(program)["fields"]["ATTACK"] = "lunge"
    with pytest.raises(ValueError, match="Duplicate case"):
        evaluate_workspace_program(program)


@pytest.fixture
def police_room(db, monkeypatch):
    mission = Mission.objects.create(title="The Police station")
    room = RoomDefinition.objects.create(mission=mission)
    mission.first_room = mission.current_room = room
    mission.save()
    RoomState.objects.create(room=room)

    def catalogue(mission_id, room_id):
        return {"lesson_id": BOSS_ID} if (mission_id, room_id) == (mission.pk, room.pk) else {}

    monkeypatch.setattr("core.bosses.load_boss_room", catalogue)
    return room


@pytest.fixture
def submit_program(client, police_room):
    def submit(workspace):
        return client.post(reverse("core:check_program"), {
            "mission_id": police_room.mission_id, "room_id": police_room.pk,
            "workspace": workspace,
            "passed": True,  # A client claim must never decide completion.
        }, content_type="application/json").json()
    return submit


@pytest.fixture
def early_attack():
    return {"blocks": {"blocks": [{"type": "boss_attack", "id": "early"}]}}


def test_client_success_claim_cannot_complete_the_room(submit_program, police_room, early_attack):
    result = submit_program(early_attack)
    assert result["passed"] is False
    assert RoomState.objects.get(room=police_room).completed is False


def test_retry_starts_fresh_and_does_not_erase_a_win(submit_program, police_room, program, early_attack):
    failed = submit_program(early_attack)
    successful = submit_program(program)
    submit_program(early_attack)
    assert successful["initial_state"] == failed["initial_state"]
    assert RoomState.objects.get(room=police_room).completed is True


def test_verified_win_saves_completion_and_unlocks_exit(client, submit_program, police_room, program):
    submit_program(program)
    assert RoomState.objects.get(room=police_room).completed is True
    response = client.post(
        reverse("core:next-room", args=[police_room.mission_id]), {"room_id": police_room.pk},
    )
    assert response.url == reverse("core:main-menu")


def test_unfinished_encounter_cannot_finish_the_mission(client, police_room):
    response = client.post(
        reverse("core:next-room", args=[police_room.mission_id]), {"room_id": police_room.pk},
    )
    assert response.url != reverse("core:main-menu")
