from django.urls import path

from . import views

app_name = "academic"

urlpatterns = [
    path("", views.index, name="index"),
]
