import json
from pathlib import Path

from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .lessons import create_lesson_from_id, load_exercise_set, load_movement_settings
from .static.core.png_movement.png_move import load_room_floor
from .rooms import advance_from_current_room, load_room, open_mission
from .models import Mission, Puzzle, RoomDefinition
from .zombie_checker import was_zombie_punched

def main_menu(request):
    return render(request, "core/main-menu.html", {
        "missions": Mission.objects.filter(first_room__isnull=False).order_by("id"),
    })

# Only what the popup shows, so solutions never reach the page source.
EXERCISE_FIELDS = ("id", "title", "object", "task", "expected_output", "hint", "starting_code")


def _exercises_for(exercise_set_id):
    if not exercise_set_id:
        return []
    exercises = load_exercise_set(exercise_set_id).get("exercises", [])
    return [{field: exercise.get(field, "") for field in EXERCISE_FIELDS} for exercise in exercises]

@never_cache
def screen(request):
    # Version the module URL so rebuilt Blockly code replaces a cached bundle.
    screen_script_path = finders.find("core/screen/dist/screen.js")
    screen_script_version = Path(screen_script_path).stat().st_mtime_ns if screen_script_path else 0
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
            "exercises": [],
            "mission": None, "workspace_state": {}, "available_blocks": None,
            "screen_script_version": screen_script_version,
            "lesson_initial_variables": {},
            "floor_config": None,
            "movement_config": {"enabled": False},
        })

    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    room_definition = None

    if mission.first_room_id is not None:
        room_definition, _ = open_mission(mission_id=mission.pk)
    lesson = create_lesson_from_id(room_definition.lesson_id) if room_definition else None
    tutorial_documents = []
    if room_definition is not None:
        tutorial_documents.append({
            "room_id": room_definition.pk,
            "mission_title": mission.title,
            "path": room_definition.tutorial_document_path,
            "current": True,
        })
    other_documents = RoomDefinition.objects.exclude(
        mission=mission,
    ).filter(mission__tutorials_unlocked=True).exclude(
        tutorial_document_path="",
    ).select_related("mission").order_by(
        "mission__title", "room_id",
    )
    seen_document_paths = {document["path"] for document in tutorial_documents}
    for document in other_documents:
        if document.tutorial_document_path in seen_document_paths:
            continue
        seen_document_paths.add(document.tutorial_document_path)
        tutorial_documents.append({
            "room_id": document.pk,
            "mission_title": document.mission.title,
            "path": document.tutorial_document_path,
            "current": False,
        })
    workspace_state = puzzle.workspace_state.get(
        _workspace_key(room_definition.pk if room_definition else None), {},
    ) if puzzle else {}
    # Jumpscare rooms start with broken blocks until the player saves their own.
    if not workspace_state and lesson is not None:
        workspace_state = getattr(lesson, "starting_workspace", {})
    movement_enabled = room_definition is not None and room_definition.next_room_id is None
    return render(request, "core/screen.html",{
        "mission": mission,
        "screen_script_version": screen_script_version,
        "room": room_definition,
        "floor_config": load_room_floor(
            mission.pk, room_definition.pk, room_definition.background_asset_path,
            # Final rooms keep the existing boss data lookup.
        ) if movement_enabled else None,
        "movement_config": {
            "enabled": movement_enabled, **load_movement_settings(),
        },
        "lesson": lesson,
        "available_blocks": lesson.get_blocks() if lesson else None,
        "lesson_initial_variables": lesson.get_initial_zombie_variables() if lesson else {},
        "tutorial_documents": tutorial_documents,
        "workspace_state": workspace_state,
        "solution": puzzle.solution if puzzle else "",
        "tests": puzzle.tests if puzzle else [],
        "exercises": _exercises_for(room_definition.exercise_set_id) if room_definition else [],
        },
    )

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
            messages.error(request, str(error))
            return redirect(f"{reverse('core:screen')}?mission={mission.pk}")
    
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
    """Check JSON assignments or punch text and return lesson state or a punch result."""
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


@transaction.atomic
def _room_assignments_to_json_response(data):
    """Validate the current mission room, run assignments, save success, and return lesson state as JSON."""
    mission_id, room_id = data.get("mission_id"), data.get("room_id")

    if type(mission_id) is not int or type(room_id) is not int:
        return JsonResponse({"error": "Send the mission and room IDs with assignments."}, status=400)
    mission = get_object_or_404(Mission.objects.select_for_update(), pk=mission_id)
    room = get_object_or_404(mission.rooms, pk=room_id)
    
    if mission.current_room_id != room_id:
        return JsonResponse({"error": "This room is no longer current. Reload the screen."}, status=400)
    try:
        lesson = create_lesson_from_id(room.lesson_id)
        if lesson is None:
            raise ValueError("This room has no lesson to run.")
        _, room_state = load_room(mission=mission, room_id=room_id)
        result = lesson.apply_assignments_to_zombie_variables(
            data.get("assignments"), requirements=room_state.encounter_state["requirements"],
        )
        if result["passed"] and not room_state.completed:
            room_state.completed = True
            room_state.save(update_fields=["completed"])
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(result)
