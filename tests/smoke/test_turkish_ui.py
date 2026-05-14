"""
Türkçe UI smoke testleri — kritik sayfaların Türkçe metinleri içerdiği doğrulaması.
"""
import pytest
from django.test import Client
from django.urls import reverse

pytestmark = [pytest.mark.django_db, pytest.mark.smoke]


def test_home_shows_turkish_heading():
    resp = Client().get(reverse("core:home"))
    assert resp.status_code == 200
    content = resp.content.decode("utf-8")
    assert "Öğrenci ders seçimi" in content or "Akademik" in content
