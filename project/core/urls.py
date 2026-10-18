from django.urls import path
from . import views
app_name="core"
urlpatterns = [
    path("", views.main_menu, name="main-menu"),
    path("screen/", views.screen, name="screen"),
    path("old-map/", views.old_map_page, name="old-map"),
    path("check/", views.check_program, name="check_program"),
]
