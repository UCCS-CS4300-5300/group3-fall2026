import json

from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Mission, Puzzle, RoomDefinition
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
        return render(request, "core/screen.html", {"mission": None, "workspace_state": {}})

    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    room_definition = None
    if mission.first_room_id is not None:
        room_definition, _ = open_mission(mission_id=mission.pk)
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
    return render(request, "core/screen.html",{
        "mission": mission,
        "room": room_definition,
        "tutorial_documents": tutorial_documents,
        "workspace_state": puzzle.workspace_state.get(
            _workspace_key(room_definition.pk if room_definition else None), {},
        ) if puzzle else {},
        "solution": puzzle.solution if puzzle else "",
        "tests": puzzle.tests if puzzle else [],
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

@csrf_exempt 
@require_POST
def check_program(request):
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Request body must be JSON."}, status=400)
    program = data.get("program") if isinstance(data, dict) else None
    if not isinstance(program, str):
        return JsonResponse({"error": 'Send {"program": "..."}.'}, status=400)
    return JsonResponse(was_zombie_punched(program))
