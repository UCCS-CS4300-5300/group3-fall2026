import json
from pathlib import Path

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .code_runner import run_python
from .lessons import create_lesson_from_id
from .rooms import advance_from_current_room, load_room, open_mission
from .models import Mission, RoomDefinition
from .zombie_checker import was_zombie_punched

def main_menu(request):
    return render(request, "core/main-menu.html", {
        "missions": Mission.objects.filter(first_room__isnull=False).order_by("id"),
    })

EXERCISES_PATH = Path(__file__).parent / "exercises" / "exercises.json"
# Only what the popup shows, so solutions never reach the page source.
EXERCISE_FIELDS = ("id", "title", "object", "task", "expected_output", "hint", "starting_code")


def _exercises_for(exercise_set_id):
    if not exercise_set_id:
        return []
    with EXERCISES_PATH.open(encoding="utf-8") as file:
        sets = {entry["lesson_id"]: entry for entry in json.load(file)}
    exercises = sets.get(exercise_set_id, {}).get("exercises", [])
    return [{field: exercise.get(field, "") for field in EXERCISE_FIELDS} for exercise in exercises]


def _clean_output(text):
    """Ignore trailing spaces and blank lines when comparing printed output."""
    return "\n".join(line.rstrip() for line in text.splitlines()).strip("\n")


@require_POST
def run_exercise(request):
    """Run one exercise's code in a child process and compare its output with the expected output."""
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Request body must be JSON."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

    mission_id, room_id = data.get("mission_id"), data.get("room_id")
    exercise_id, code = data.get("exercise_id"), data.get("code")
    if (type(mission_id) is not int or type(room_id) is not int
            or not isinstance(exercise_id, str) or not isinstance(code, str)):
        return JsonResponse({"error": "Send mission_id, room_id, exercise_id and code."}, status=400)

    room = get_object_or_404(RoomDefinition, pk=room_id, mission_id=mission_id)
    # Look the exercise up on the server so the browser can't send its own expected output.
    exercise = next((e for e in _exercises_for(room.exercise_set_id) if e["id"] == exercise_id), None)
    if exercise is None:
        return JsonResponse({"error": "That exercise isn't in this room."}, status=404)

    result = run_python(code)
    passed = not result["error"] and (
        _clean_output(result["output"]) == _clean_output(exercise["expected_output"])
    )
    return JsonResponse({**result, "passed": passed})

@never_cache
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
            "exercises": [],
            "mission": None,
        })

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
        "exercises": _exercises_for(room_definition.exercise_set_id) if room_definition else [],
        },
    )

@require_POST
def next_room(request, mission_id):
    try:
        source_room_id = int(request.POST.get("room_id", ""))
    except ValueError:
        return HttpResponseBadRequest("Invalid room ID.")
    with transaction.atomic():
        mission = get_object_or_404(Mission.objects.select_for_update(), pk=mission_id)
        
        if source_room_id != mission.current_room_id:
            return HttpResponseBadRequest("This room is no longer current. Reload the screen.")
        room_state = get_object_or_404(mission.room_states, room_id=source_room_id)
        
        try:
            destination = advance_from_current_room(mission=mission, current_room_state=room_state)
        except ValueError as error:
            messages.error(request, str(error))
            return redirect(f"{reverse('core:screen')}?mission={mission.pk}")
    
    if destination == "main-menu":
        return redirect("core:main-menu")
    return redirect(f"{reverse('core:screen')}?mission={mission.pk}")

@require_POST
def exit_mission(request, mission_id):
    get_object_or_404(Mission, pk=mission_id)
    return redirect("core:main-menu")

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
