from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Mission, Node

COMPLETED_KEY = "completed_missions"


def completed_mission_ids(request):
    return set(request.session.get(COMPLETED_KEY, []))


def mark_completed(request, mission):
    completed = completed_mission_ids(request)
    if mission.id not in completed:
        request.session[COMPLETED_KEY] = sorted(completed | {mission.id})


def get_node(mission_id, node_id):
    mission = get_object_or_404(Mission, pk=mission_id, is_active=True)
    node = get_object_or_404(Node.objects.prefetch_related("choices"), pk=node_id, mission=mission)
    return mission, node


def mission_list(request):
    return render(request, "missions/mission_list.html", {
        "missions": Mission.objects.filter(is_active=True),
        "completed": completed_mission_ids(request),
    })


def mission_start(request, mission_id):
    mission = get_object_or_404(Mission, pk=mission_id, is_active=True)
    if mission.start_node_id is None:
        raise Http404("Mission has no start node.")
    return redirect("missions:node", mission_id=mission.id, node_id=mission.start_node_id)


def node_page(request, mission_id, node_id):
    mission, node = get_node(mission_id, node_id)
    choices = list(node.choices.all())
    if not choices:
        mark_completed(request, mission)
    return render(request, "missions/node.html", {
        "mission": mission,
        "node": node,
        "choices": choices,
    })


def api_mission_list(request):
    completed = completed_mission_ids(request)
    return JsonResponse({"missions": [
        {
            "id": mission.id,
            "title": mission.title,
            "summary": mission.summary,
            "start_node": mission.start_node_id,
            "completed": mission.id in completed,
        }
        for mission in Mission.objects.filter(is_active=True)
    ]})


def api_node(request, mission_id, node_id):
    _, node = get_node(mission_id, node_id)
    return JsonResponse(node.to_dict())
