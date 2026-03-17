from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("test/student/", views.student_test_page, name="student_test"),
    path("test/instructor/", views.instructor_test_page, name="instructor_test"),
]
