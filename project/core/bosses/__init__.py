"""Select boss rules while keeping room checks and completion rules shared."""

from ..lessons import load_boss_room
from . import conditionals, variables


# =========================================================================
# Resolve configured lessons and catalogue entries to the same boss modules
# =========================================================================
BOSS_MODULES = {
    variables.BOSS_ID: variables,
    "corner_store_boss_zombie": variables,
    conditionals.BOSS_ID: conditionals,
}


def find_room_boss(mission, room):
    """Return the room's implemented boss module, or None for an ordinary room."""
    if room is None or room.next_room_id is not None:
        return None

    if mission.boss_lesson_id and room.lesson_id == mission.boss_lesson_id:
        return BOSS_MODULES.get(mission.boss_lesson_id)

    catalogue_entry = load_boss_room(mission.pk, room.pk)
    return BOSS_MODULES.get(catalogue_entry.get("lesson_id"))


# ==========================================================================
# Request a subset of pooled blocks without defining blocks inside each boss
# ==========================================================================
def describe_workspace_requirements(boss, lesson=None):
    config = {
        "requested_blocks": ["screen_punch", "screen_zombie", "controls_if"],
        "limits": {},
        "case_labels": [],
        "allow_if_mutation": True,
        "submission_format": "punch",
        "playback": "continuous",
    }

    if boss is not None:
        config.update(boss.request_workspace_blocks())
    elif lesson is not None:
        config.update(requested_blocks=lesson.get_blocks(), submission_format="assignments")

    return config
