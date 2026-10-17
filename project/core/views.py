import json

from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Mission
from .rooms import advance_from_current_room, open_mission, reset_mission
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
        return render(request, "core/screen.html", {"mission": None})

    # Missions made by hand may not have a puzzle yet
    puzzle = getattr(mission, "puzzle", None)
    room_definition = None
    if mission.first_room_id is not None:
        room_definition, _ = open_mission(mission_id=mission.pk)
    return render(request, "core/screen.html",{
        "mission": mission,
        "room": room_definition,
        "solution": puzzle.solution if puzzle else "",
        "tests": puzzle.tests if puzzle else [],
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
            return HttpResponseBadRequest(str(error))
    if destination == "main-menu":
        return redirect("core:main-menu")
    return redirect(f"{reverse('core:screen')}?mission={mission.pk}")

@require_POST
def exit_mission(request, mission_id):
    mission = get_object_or_404(Mission, pk=mission_id)
    reset_mission(mission=mission)
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
