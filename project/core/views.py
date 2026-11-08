import json
import random
from pathlib import Path

from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .lessons import create_lesson_from_id, load_boss_room, load_exercise_set, load_movement_settings
from .bosses.thoughts import format_boss_thoughts
from .bosses import find_room_boss, describe_workspace_requirements
from .bosses.program_results import describe_run_result
from .static.core.png_movement.png_move import load_room_floor
from .code_runner import run_python
from .rooms import advance_from_current_room, load_room, open_mission, record_verified_completion
from .models import Mission, Puzzle, RoomDefinition
from .zombie_checker import was_zombie_punched
from .tutorial_ai import ask_tutor_with_document, load_room_tutorial

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


JUMPSCARE_ROOM_NUMBERS = (2, 3)


def _jumpscare_session_key(mission):
    return f"jumpscare_room:{mission.pk}"


def _room_number(mission, room):
    """Return the room's 1-based position in the mission's room chain."""
    number, current = 1, mission.first_room
    while current is not None and current.pk != room.pk:
        current, number = current.next_room, number + 1
    return number


def _jumpscare_for(request, mission, room):
    """Return the scare video URL and debug exercise if this room is the run's jumpscare room."""
    # Room 2 or 3 is picked once per run, so reloading the page doesn't move the scare.
    chosen = request.session.setdefault(_jumpscare_session_key(mission), random.choice(JUMPSCARE_ROOM_NUMBERS))
    if _room_number(mission, room) != chosen:
        return None
    video = f"videos/jump-scare_videos/{mission.title.title().replace(' ', '_')}_scare.mp4"
    exercises = _exercises_for(mission.jumpscare_exercise_set_id)
    if not finders.find(video) or not exercises:
        return None
    return {"video": static(video), "exercise": exercises[0]}


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
    # The building's jumpscare exercise can be run from any of its rooms.
    set_ids = (room.exercise_set_id, room.mission.jumpscare_exercise_set_id)
    exercise = next((e for set_id in set_ids for e in _exercises_for(set_id) if e["id"] == exercise_id), None)
    if exercise is None:
        return JsonResponse({"error": "That exercise isn't in this room."}, status=404)

    result = run_python(code)
    passed = not result["error"] and (
        _clean_output(result["output"]) == _clean_output(exercise["expected_output"])
    )
    return JsonResponse({**result, "passed": passed})

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
            "is_boss_room": False,
        })

    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    room_definition = None
    room_state = None

    if mission.first_room_id is not None:
        room_definition, room_state = open_mission(mission_id=mission.pk)
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
    # =========================================================================
    # Request the room's pooled blocks and initial values from its rules module
    # =========================================================================
    is_boss_room = room_definition is not None and room_definition.next_room_id is None
    boss = find_room_boss(mission, room_definition)
    workspace_config = describe_workspace_requirements(boss, lesson)
    initial_variables = {}
    if boss is not None:
        initial_variables = boss.get_initial_variables()
    elif lesson is not None:
        initial_variables = lesson.get_initial_zombie_variables()

    movement_enabled = is_boss_room
    return render(request, "core/screen.html",{
        "mission": mission,
        "is_boss_room": is_boss_room,
        "workspace_config": workspace_config,
        "block_limits": workspace_config["limits"],
        "boss_defeated": is_boss_room and room_state.completed,
        "boss_thoughts": format_boss_thoughts(load_boss_room(mission.pk, room_definition.pk).get("thoughts", [])) if is_boss_room else [],
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
        "available_blocks": workspace_config["requested_blocks"] if boss or lesson else None,
        "lesson_initial_variables": initial_variables,
        "tutorial_documents": tutorial_documents,
        "workspace_state": workspace_state,
        "solution": puzzle.solution if puzzle else "",
        "tests": puzzle.tests if puzzle else [],
        "exercises": _exercises_for(room_definition.exercise_set_id) if room_definition else [],
        "jumpscare": _jumpscare_for(request, mission, room_definition) if room_definition else None,
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
        # The next run of this building picks room 2 or 3 again.
        request.session.pop(_jumpscare_session_key(mission), None)
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

# ========================================================================
# Route program formats through shared room checks and result descriptions
# ========================================================================
@require_POST
def check_program(request):
    try:
        data = json.loads(request.body)
    except (ValueError, RecursionError):
        return JsonResponse({"error": "Request body must be JSON."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Request body must be a JSON object."}, status=400)

    if any(key in data for key in ("workspace", "boss_workspace", "assignments")):
        return _check_current_room_submission(data)

    program = data.get("program")
    if not isinstance(program, str):
        return JsonResponse({"error": 'Send {"program": "..."}.'}, status=400)

    return JsonResponse(describe_run_result(was_zombie_punched(program)))


# =========================================================================
# Verify room ownership, run its selected rules, and persist a verified win
# =========================================================================
@transaction.atomic
def _check_current_room_submission(data):
    mission_id, room_id = data.get("mission_id"), data.get("room_id")
    if type(mission_id) is not int or type(room_id) is not int:
        return JsonResponse({"error": "Send the mission and room IDs with the program."}, status=400)

    mission = get_object_or_404(Mission.objects.select_for_update(), pk=mission_id)
    room = get_object_or_404(mission.rooms, pk=room_id)
    if mission.current_room_id != room_id:
        return JsonResponse({"error": "This room is no longer current. Reload the screen."}, status=400)

    try:
        _, room_state = load_room(mission=mission, room_id=room_id)
        requirements = room_state.encounter_state.get("requirements", {})
        boss = find_room_boss(mission, room)

        if boss is not None:
            result = boss.evaluate_submission(data, requirements)
        else:
            lesson = create_lesson_from_id(room.lesson_id)
            if lesson is None or "assignments" not in data:
                raise ValueError("This room has no rules for that program format.")
            result = lesson.apply_assignments_to_zombie_variables(
                data["assignments"], requirements=requirements,
            )

        record_verified_completion(room_state, result)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse(describe_run_result(result))


@require_POST
def ask_tutorial(request):
    "This answers student questions using a tutorial document"
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse(
                {"error": "Request body must be a JSON object."},
                status = 400,
            )
    if not isinstance(data, dict):
        return JsonResponse(
                {"error": "Request body must be a JSON object."},
                status = 400,
        )

    room_id = data.get("room_id")
    question = data.get("question")

    if type(room_id) is not int or not isinstance(question, str):
        return JsonResponse(
                {"error": "Room ID must be an integer and question must be a string."},
                status = 400
            )
    question = question.strip()

    if not question:
        return JsonResponse(
                {"error": "Please enter a question."},
                status = 400,
        )

    if len(question) > 1000:
        return JsonResponse(
                {"error": "Question must be 1000 characters or fewer."},
                status = 400,
            )

    room = RoomDefinition.objects.filter(pk=room_id).select_related("mission").first()

    if room is None:
        return JsonResponse(
            {"error": "Room not found."},
            status=404,
        )

    mission = room.mission


    if room.pk != mission.current_room_id and not mission.tutorials_unlocked:
        return JsonResponse(
            {"error": "This tutorial is locked."},
            status=403,
        )

    try:
        document = load_room_tutorial(room)
    except ValueError:
        return JsonResponse(
            {"error": "Invalid tutorial document path."},
            status=400,
        )
    except FileNotFoundError:
        return JsonResponse(
            {"error": "This tutorial document is not available yet."},
            status=404,
        )

    try:
        answer = ask_tutor_with_document(document, question)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("AI tutorial request failed.")
        return JsonResponse(
            {"error": "The AI tutor is currently unavailable."},
            status=503,
        )

    return JsonResponse({"answer": answer})
