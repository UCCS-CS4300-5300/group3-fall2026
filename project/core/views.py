from django.shortcuts import render
from .models import Mission

def practice(request):
    '''
    Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit.",
        instructions="Use for loops, if statements, and while loops to reach the exit. Avoid hazards and the zombie horde behind you!")
    '''
    # Newest mission, so one made by `python manage.py generate_mission` shows up here
    mission = Mission.objects.order_by("-id").first()
    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    return render(request, "core/practice.html",{
        "title": mission.title,
        "instructions": mission.instructions,
        "description": mission.description,
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
