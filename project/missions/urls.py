from django.urls import path

from . import views

app_name = "missions"
urlpatterns = [
    path("missions/", views.mission_list, name="list"),
    path("missions/<int:mission_id>/", views.mission_start, name="start"),
    path("missions/<int:mission_id>/node/<int:node_id>/", views.node_page, name="node"),
    path("api/missions/", views.api_mission_list, name="api_list"),
    path("api/missions/<int:mission_id>/node/<int:node_id>/", views.api_node, name="api_node"),
]
