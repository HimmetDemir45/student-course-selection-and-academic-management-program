from django.urls import path

from . import views

app_name = "academic"

urlpatterns = [
    path("departments/", views.DepartmentListView.as_view(), name="department_list"),
    path("departments/create/", views.DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="department_update"),
    path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),
    path("departments/<int:pk>/toggle/", views.department_toggle_active, name="department_toggle_active"),
    path("announcements/", views.AnnouncementListView.as_view(), name="announcement_list"),
    path("announcements/create/", views.AnnouncementCreateView.as_view(), name="announcement_create"),
    path("announcements/<int:pk>/edit/", views.AnnouncementUpdateView.as_view(), name="announcement_update"),
    path("announcements/<int:pk>/delete/", views.AnnouncementDeleteView.as_view(), name="announcement_delete"),
    path("announcements/<int:pk>/toggle/", views.announcement_toggle_active, name="announcement_toggle_active"),
    path(
        "instructor/enrollments/",
        views.InstructorEnrollmentListView.as_view(),
        name="instructor_enrollments",
    ),
    path(
        "instructor/grades/<int:enrollment_id>/",
        views.GradeEntryView.as_view(),
        name="grade_entry",
    ),
]
