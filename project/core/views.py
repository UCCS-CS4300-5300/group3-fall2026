from django.shortcuts import render
from .models import StarterItem

def practice(request):
    return render(request, "core/practice.html")

def map_page(request):
    return render(request, "core/map.html", {
        "items": StarterItem.objects.filter(is_active=True).order_by("title"),
        "level": 1,
    })
