import json

from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .lessons import create_lesson_from_id
from .models import Mission, Puzzle
from .rooms import advance_from_current_room, open_mission
from .zombie_checker import was_zombie_punched

def main_menu(request):
    return render(request, "core/main-menu.html", {
        "missions": Mission.objects.filter(first_room__isnull=False).order_by("id"),
    })


def screen(request):
    mission_id = request.GET.get("mission")
    if mission_id is not None:
        try:
            mission_id = int(mission_id)
        except ValueError:
            return HttpResponseBadRequest("Invalid mission ID.")
        mission = get_object_or_404(Mission, pk=mission_id)
    else:
        mission = Mission.objects.order_by("-id").first()
    if mission is None:
        return render(request, "core/screen.html", {
            "mission": None, "workspace_state": {}, "available_blocks": None,
        })

    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    room_definition = None
    if mission.first_room_id is not None:
        room_definition, _ = open_mission(mission_id=mission.pk)
    return render(request, "core/screen.html",{
        "mission": mission,
        "room": room_definition,
        "available_blocks": _get_room_lesson_blockly_types(room_definition),
        "workspace_state": puzzle.workspace_state.get(
            _workspace_key(room_definition.pk if room_definition else None), {},
        ) if puzzle else {},
        "solution": puzzle.solution if puzzle else "",
        "tests": puzzle.tests if puzzle else [],
        },
    )


def _get_room_lesson_blockly_types(room):
    """Return Blockly type IDs from the room's selected lesson, or None for defaults.

    None keeps the original toolbox; an empty list intentionally offers no blocks.
    """
    lesson = create_lesson_from_id(room.lesson_id) if room else None
    return lesson.get_blocks() if lesson else None


def _submitted_workspace(request):
    serialized = request.POST.get("workspace_json")
    if not serialized:
        return None
    try:
        workspace_state = json.loads(serialized)
    except ValueError as error:
        raise ValueError("Invalid Blockly workspace JSON.") from error
    if not isinstance(workspace_state, dict):
        raise ValueError("Blockly workspace must be a JSON object.")
    return workspace_state


def _workspace_key(room_id):
    return str(room_id) if room_id is not None else "mission"


def _save_workspace(mission, workspace_state):
    if workspace_state is not None:
        puzzle, _ = Puzzle.objects.get_or_create(mission=mission)
        puzzle.workspace_state[_workspace_key(mission.current_room_id)] = workspace_state
        puzzle.save(update_fields=["workspace_state"])


@require_POST
def next_room(request, mission_id):
    try:
        source_room_id = int(request.POST.get("room_id", ""))
    except ValueError:
        return HttpResponseBadRequest("Invalid room ID.")
    try:
        workspace_state = _submitted_workspace(request)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    with transaction.atomic():
        mission = get_object_or_404(Mission.objects.select_for_update(), pk=mission_id)
        if source_room_id != mission.current_room_id:
            return HttpResponseBadRequest("This room is no longer current. Reload the screen.")
        room_state = get_object_or_404(mission.room_states, room_id=source_room_id)
        try:
            _save_workspace(mission, workspace_state)
            destination = advance_from_current_room(mission=mission, current_room_state=room_state)
        except ValueError as error:
            return HttpResponseBadRequest(str(error))
    if destination == "main-menu":
        return redirect("core:main-menu")
    return redirect(f"{reverse('core:screen')}?mission={mission.pk}")

@require_POST
def exit_mission(request, mission_id):
    try:
        workspace_state = _submitted_workspace(request)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    with transaction.atomic():
        mission = get_object_or_404(Mission.objects.select_for_update(), pk=mission_id)
        _save_workspace(mission, workspace_state)
    return redirect("core:main-menu")


def old_map_page(request):
    return render(request, "core/old-map.html", {
        # Unknown behavior? Changed during refactor, "items" never shows up in map.html
        # StarterItem database was replaced with Mission database
        # "items": Mission.objects.filter(is_active=True).order_by("title"),
        "level": 1,
    })

@require_POST
def check_program(request):
    """Accept a JSON POST containing room assignments or punch program text.

    {mission_id, room_id, assignments} returns calculated {variables, actions}.
    {program: indented_text} returns the punch checker's {punched, reason}.
    Invalid JSON or instructions return a 400 response with an error message.
    """
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Request body must be JSON."}, status=400)
    if isinstance(data, dict) and "assignments" in data:
        return _room_assignments_to_json_response(data)
    program = data.get("program") if isinstance(data, dict) else None
    if not isinstance(program, str):
        return JsonResponse({"error": 'Send {"program": "..."}.'}, status=400)
    return JsonResponse(was_zombie_punched(program))


def _room_assignments_to_json_response(data):
    """Use {mission_id, room_id, assignments} to return the lesson's calculated state.

    Verify room ownership and that the room is currently open, then run its lesson.
    Return {variables, actions} as JSON, or a 400 error for invalid instructions.
    Missing mission/room records produce a 404; no progress or values are saved.
    """
    mission_id, room_id = data.get("mission_id"), data.get("room_id")
    if type(mission_id) is not int or type(room_id) is not int:
        return JsonResponse({"error": "Send the mission and room IDs with assignments."}, status=400)
    mission = get_object_or_404(Mission, pk=mission_id)
    room = get_object_or_404(mission.rooms, pk=room_id)
    if mission.current_room_id != room_id:
        return JsonResponse({"error": "This room is no longer current. Reload the screen."}, status=400)
    try:
        lesson = create_lesson_from_id(room.lesson_id)
        if lesson is None:
            raise ValueError("This room has no lesson to run.")
        result = lesson.apply_assignments_to_zombie_variables(data.get("assignments"))
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(result)
