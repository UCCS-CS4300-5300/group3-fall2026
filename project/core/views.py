from django.shortcuts import render
from .models import Mission

def practice(request):
    '''
    Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit.",
        instructions="Use for loops, if statements, and while loops to reach the exit. Avoid hazards and the zombie horde behind you!")
    '''
    mission = Mission.objects.first()
    return render(request, "core/practice.html",{
        "title": mission.title,
        "instructions": mission.instructions,
        "description": mission.description,
        },
    )

def map_page(request):
    return render(request, "core/map.html", {
        # Unknown behavior? Changed during refactor, "items" never shows up in map.html
        # StarterItem database was replaced with Mission database
        # "items": Mission.objects.filter(is_active=True).order_by("title"),
        "level": 1,
    })
