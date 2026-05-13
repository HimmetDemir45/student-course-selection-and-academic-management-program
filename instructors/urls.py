from django.urls import path

from . import views

app_name = "instructors"

urlpatterns = [
    path("", views.InstructorHomeView.as_view(), name="index"),
    path("admin/", views.InstructorAdminListView.as_view(), name="admin_list"),
    path("admin/<int:pk>/edit/", views.InstructorAdminEditView.as_view(), name="admin_edit"),
]
