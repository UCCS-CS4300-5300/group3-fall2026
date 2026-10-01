import pytest
from django.urls import reverse
from .models import Mission

@pytest.mark.django_db
def test_home(client):
 r=client.get(reverse("core:home")); assert r.status_code==200; assert b"Code Blocks" in r.content