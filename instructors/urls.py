from django.urls import path

from . import views

app_name = "instructors"

urlpatterns = [
    path("", views.InstructorHomeView.as_view(), name="index"),
]
