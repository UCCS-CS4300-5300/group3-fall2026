import json

from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Mission, Puzzle, QuizAttempt, QuizPuzzle
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

    is_quiz = bool(puzzle and puzzle.puzzle_type == "quiz")
    quiz_available = False
    quiz_question = None
    quiz_question_number = 0
    quiz_question_count = 0
    quiz_complete = False

    if is_quiz:
        quiz = getattr(puzzle, "quiz", None)

        if quiz:
            quiz_available = True
            questions = list(quiz.questions.order_by("pk"))
            quiz_question_count = len(questions)

            if questions:
                attempt, _ = QuizAttempt.objects.get_or_create(
                    quiz=quiz,
                    defaults={"question_number": 0},
                )
                quiz_question_number = attempt.question_number

                if 0 <= quiz_question_number < len(questions):
                    question = questions[quiz_question_number]
                    quiz_question = {
                        "id": question.pk,
                        "text": question.question,
                        "options": list(enumerate(question.options)),
                    }
                else:
                    quiz_complete = (quiz_question_number >= len(questions))

    return render(request, "core/screen.html",{
        "mission": mission,
        "room": room_definition,
        "is_quiz": is_quiz,
        "quiz_question": quiz_question,
        "quiz_available": quiz_available,
        "quiz_question_count": quiz_question_count,
        "quiz_question_number": quiz_question_number,
        "quiz_complete": quiz_complete,
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

@require_POST
def submit_quiz_answer(request, mission_id):
    puzzle = get_object_or_404(Puzzle, mission=mission_id, puzzle_type="quiz")
    quiz = get_object_or_404(QuizPuzzle, puzzle=puzzle)
    questions = list(quiz.questions.order_by("pk"))
    attempt, _ = QuizAttempt.objects.get_or_create(quiz=quiz, defaults={"question_number": 0})

    if not 0 <= attempt.question_number < len(questions):
        return HttpResponseBadRequest("This quiz has no current question.")

    current_question = questions[attempt.question_number]

    try:
        submitted_question_id = int(request.POST.get("question_id", ""))
        answer_index = int(request.POST.get("answer", ""))
    except ValueError:
        return HttpResponseBadRequest("Choose an answer before submitting.")

    if submitted_question_id != current_question.pk:
        return HttpResponseBadRequest("The quiz has changed. Reload the screen and try again.")

    if not isinstance(current_question.options, list):
        return HttpResponseBadRequest("This question's options are invalid.")

    if not 0 <= answer_index < len(current_question.options):
        return HttpResponseBadRequest("Choose a valid answer.")

    if answer_index == current_question.answer_index:
        attempt.question_number += 1
        attempt.save(update_fields=["question_number"])
        messages.success(request, "You have entered the correct answer.")
    else:
        messages.error(request, "You have entered the wrong answer, please try again.")

    return redirect(f"{reverse('core:screen')}?mission={mission_id}")