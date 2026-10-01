from django.shortcuts import render
from .models import Mission

def practice(request):
    return render(request, "core/practice.html")

def map_page(request):
    return render(request, "core/map.html", {
        # Unknown behavior? Changed during refactor, "items" never shows up in map.html
        # StarterItem database was replaced with Mission database
        "items": Mission.objects.filter(is_active=True).order_by("title"),
        "level": 1,
    })
