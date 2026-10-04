import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .block_checker import check_program
from .models import Mission, Puzzle

def practice(request):
    '''
    Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit.",
        instructions="Use for loops, if statements, and while loops to reach the exit. Avoid hazards and the zombie horde behind you!")
    '''
    # Newest mission, so one made by `python manage.py generate_mission` shows up here
    mission = Mission.objects.order_by("-id").first()
    if mission is None:
        return render(request, "core/practice.html", {"mission": None})

    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    return render(request, "core/practice.html",{
        "mission": mission,
        "solution": puzzle.solution if puzzle else "",
        "tests": puzzle.tests if puzzle else [],
        },
    )

@require_POST
def check_blocks(request, mission_id):
    '''
    Checks the student's blocks against the AI's intended code for a mission.
    Expects JSON {"program": "..."}: the workspace as text, one block per line, indented for nesting.
    '''
    puzzle = get_object_or_404(Puzzle, mission_id=mission_id)
    try:
        program = json.loads(request.body)["program"]
        if not isinstance(program, str):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": 'Send JSON like {"program": "move forward"}'}, status=400)
    return JsonResponse(check_program(puzzle.solution, puzzle.tests, program))

def map_page(request):
    return render(request, "core/map.html", {
        # Unknown behavior? Changed during refactor, "items" never shows up in map.html
        # StarterItem database was replaced with Mission database
        # "items": Mission.objects.filter(is_active=True).order_by("title"),
        "level": 1,
    })
