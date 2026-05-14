"""
Core app URL rotaları: ana sayfa, sağlık uçları (/health/live/, /health/ready/).
"""
from django.conf import settings
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
]

# Rollback: asagidaki if blogunu kaldirarak test rotalarini her zaman urlpatterns'e ekleyin.
if settings.DEBUG or getattr(settings, "INCLUDE_CORE_DEV_TEST_ROUTES", False):
    urlpatterns += [
        path("test/student/", views.student_test_page, name="student_test"),
        path("test/instructor/", views.instructor_test_page, name="instructor_test"),
    ]
