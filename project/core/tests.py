import pytest
from django.urls import reverse
from .models import Mission

# Dr. Walcott's Initial Tests

@pytest.mark.django_db
def test_home(client):
 r=client.get(reverse("core:home")); assert r.status_code==200; assert b"Code Blocks" in r.content

# Mission Database Tests

@pytest.mark.django_db
def test_mission_has_title():
    mission = Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit."
    )

    assert mission.title == "Reach the Exit"

@pytest.mark.django_db
def test_mission_has_description():
    mission = Mission.objects.create(
        title="Reach the Exit",
        description="Guide the character to the exit."
    )

    assert mission.description == "Guide the character to the exit."