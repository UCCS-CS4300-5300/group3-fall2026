"""Keep recorded playback outcomes provisional until their timing is resolved."""

from time import time
from uuid import uuid4


# ============================================================================
# Save the verified program result without granting completion before playback
# ============================================================================
def prepare_playback_attempt(room_state, result, duration_ms):
    token = uuid4().hex
    room_state.encounter_state["playback_attempt"] = {
        "id": token,
        "started_at": time(),
        "duration_ms": duration_ms,
        "result": result,
        "finished": False,
    }
    room_state.save(update_fields=["encounter_state"])
    response = dict(result)
    response["playback_id"] = token
    return response


# ===========================================================================
# Resolve only the current attempt and never accept a client-provided victory
# ===========================================================================
def finish_playback_attempt(room_state, boss, token, missed_block=None):
    attempt = room_state.encounter_state.get("playback_attempt")
    if not isinstance(token, str) or not attempt or attempt["id"] != token:
        raise ValueError("This playback attempt is no longer current. Run the program again.")
    if attempt["finished"]:
        return attempt["result"]

    result = attempt["result"]
    ending_turn = result["state"]["turn"]
    missed_event = None

    if missed_block is not None:
        if not isinstance(missed_block, str):
            raise ValueError("Invalid missed-action ID.")
        missed_event = next((
            event for event in result["events"]
            if event["block_id"] == missed_block and event.get("requires_timing") is True
        ), None)
        if missed_event is None:
            raise ValueError("That block has no timed action window.")
        ending_turn = missed_event["after"]["turn"]

    required_ms = attempt["duration_ms"] * ending_turn / result["state"]["action_units"]
    if (time() - attempt["started_at"]) * 1000 < required_ms:
        raise ValueError("The action timeline has not finished yet.")

    if missed_event is not None:
        result = boss.resolve_missed_action(result, missed_event)

    attempt["result"] = result
    attempt["finished"] = True
    room_state.save(update_fields=["encounter_state"])
    return result
