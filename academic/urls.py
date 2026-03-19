from django.urls import path

from . import views

app_name = "academic"

urlpatterns = [
    path("departments/", views.DepartmentListView.as_view(), name="department_list"),
    path("departments/create/", views.DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="department_update"),
    path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),
    path("announcements/", views.AnnouncementListView.as_view(), name="announcement_list"),
    path("announcements/create/", views.AnnouncementCreateView.as_view(), name="announcement_create"),
    path("announcements/<int:pk>/edit/", views.AnnouncementUpdateView.as_view(), name="announcement_update"),
    path("announcements/<int:pk>/delete/", views.AnnouncementDeleteView.as_view(), name="announcement_delete"),
]
