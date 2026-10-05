import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Mission
from .zombie_checker import was_zombie_punched

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

def map_page(request):
    return render(request, "core/map.html", {
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
