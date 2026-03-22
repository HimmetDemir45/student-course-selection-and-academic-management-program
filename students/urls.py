from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentIndexView.as_view(), name="index"),
    path("transcript/", views.TranscriptView.as_view(), name="transcript"),
]
