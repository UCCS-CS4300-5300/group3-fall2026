from django.urls import path
from . import views
app_name="core"
urlpatterns=[path("",views.practice,name="home"),path("map/",views.map_page,name="map")]
