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
    detection = block("controls_if", {"IF0": block("boss_undetected"), "DO0": noise})
    approach = block("controls_ifelse", {
        "IF0": block("boss_not_close"), "DO0": block("boss_wait"),
        "ELSE": block("boss_step_forward"),
    })
    cases = [block("boss_case", {"ATTACK": block("boss_" + attack), "DO": block("boss_" + defense)})
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
    assert actions == ["make_noise", "wait", "step_back", "attack"]


def test_actions_advance_four_units_and_decisions_consume_none(program):
    result = evaluate_workspace_program(program)
    actions = [event for event in result["events"] if event["kind"] == "action"]
    assert [event["after"]["progress"] for event in actions] == [0.25, 0.5, 0.75, 1.0]
    assert all(
        event["after"]["turn"] - event["before"]["turn"] == (event["kind"] == "action")
        for event in result["events"]
    )


def test_each_evaluation_starts_from_the_same_state(program):
    assert evaluate_workspace_program(program) == evaluate_workspace_program(program)


@pytest.mark.parametrize(("actions", "times"), [
    (["wait", "step_forward", "wait"], [0, 0, 0]),
    (["wait", "make_noise", "make_noise"], [0, 1, 2]),
])
def test_zombie_clock_starts_with_noise_and_does_not_restart(actions, times):
    blocks = [{"type": "boss_" + action, "id": f"action-{index}"}
              for index, action in enumerate(actions)]
    for first, second in zip(blocks, blocks[1:]):
        first["next"] = {"block": second}
    result = evaluate_workspace_program({"blocks": {"blocks": [blocks[0]]}})
    assert [event["after"]["time"] for event in result["events"]] == times
    assert result["state"]["progress"] == times[-1] / result["state"]["action_units"]


def test_defense_uses_zombie_time_instead_of_total_actions():
    actions = ["wait", "make_noise", "step_back"]
    blocks = [{"type": "boss_" + action, "id": f"action-{index}"}
              for index, action in enumerate(actions)]
    for first, second in zip(blocks, blocks[1:]):
        first["next"] = {"block": second}
    result = evaluate_workspace_program({"blocks": {"blocks": [blocks[0]]}})
    assert result["passed"] is False
    assert "defense was too early" in result["feedback"]


def test_else_branch_uses_one_action_and_can_still_match_the_attack_time(program):
    detection = program["blocks"]["blocks"][0]
    approach = detection["next"]["block"]
    approach["inputs"]["IF0"]["block"]["type"] = "boss_undetected"
    result = evaluate_workspace_program(program)
    actions = [event["result"] for event in result["events"] if event["kind"] == "action"]
    assert result["passed"] is True
    assert actions == ["make_noise", "step_forward", "step_back", "attack"]


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
    for index in range(3):
        excess["blocks"]["blocks"][0] = {
            "type": "controls_if", "id": f"extra-if-{index}", "inputs": {
                "IF0": {"block": {"type": "boss_undetected", "id": f"extra-condition-{index}"}},
                "DO0": {"block": excess["blocks"]["blocks"][0]},
            },
        }
    with pytest.raises(ValueError, match="Too many if blocks"):
        evaluate_workspace_program(excess)


def test_duplicate_case_names_are_rejected(program):
    first_case(program)["inputs"]["ATTACK"]["block"]["type"] = "boss_lunge"
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
def playback_clock(monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr("core.bosses.playback_attempts.time", lambda: clock["now"])
    return clock


@pytest.fixture
def finish_program(client, police_room, playback_clock):
    def finish(result, missed_block=None):
        playback_clock["now"] += 10
        data = {
            "mission_id": police_room.mission_id, "room_id": police_room.pk,
            "finish_playback": result["playback_id"],
        }
        if missed_block is not None:
            data["missed_block"] = missed_block
        return client.post(reverse("core:check_program"), data, content_type="application/json").json()
    return finish


@pytest.fixture
def early_attack():
    return {"blocks": {"blocks": [{"type": "boss_attack", "id": "early"}]}}


def test_client_success_claim_cannot_complete_the_room(submit_program, police_room, early_attack):
    result = submit_program(early_attack)
    assert result["passed"] is False
    assert RoomState.objects.get(room=police_room).completed is False


def test_retry_starts_fresh_and_does_not_erase_a_win(submit_program, finish_program, police_room, program, early_attack):
    failed = submit_program(early_attack)
    successful = submit_program(program)
    finish_program(successful)
    submit_program(early_attack)
    assert successful["initial_state"] == failed["initial_state"]
    assert RoomState.objects.get(room=police_room).completed is True


def test_verified_win_saves_completion_and_unlocks_exit(client, submit_program, finish_program, police_room, program):
    finish_program(submit_program(program))
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


def test_program_verdict_cannot_finish_playback_early(client, submit_program, police_room, playback_clock, program):
    planned = submit_program(program)
    response = client.post(reverse("core:check_program"), {
        "mission_id": police_room.mission_id, "room_id": police_room.pk,
        "finish_playback": planned["playback_id"],
    }, content_type="application/json")
    assert response.status_code == 400
    assert RoomState.objects.get(room=police_room).completed is False


@pytest.mark.parametrize("action", ["step_back", "attack"])
def test_missed_combat_slot_fails_without_saving_a_win(submit_program, finish_program, police_room, program, action):
    planned = submit_program(program)
    defense = next(event for event in planned["events"] if event.get("requires_timing") and event["result"] == action)
    result = finish_program(planned, defense["block_id"])
    assert result["passed"] is False
    assert RoomState.objects.get(room=police_room).completed is False


def test_new_run_invalidates_previous_playback(client, submit_program, police_room, program):
    previous = submit_program(program)
    submit_program(program)
    response = client.post(reverse("core:check_program"), {
        "mission_id": police_room.mission_id, "room_id": police_room.pk,
        "finish_playback": previous["playback_id"],
    }, content_type="application/json")
    assert response.status_code == 400
