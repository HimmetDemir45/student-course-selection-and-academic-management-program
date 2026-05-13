from django.urls import path

from . import views

app_name = "academic"

urlpatterns = [
    path("curriculum/", views.CurriculumListView.as_view(), name="curriculum_list"),
    path("curriculum/create/", views.CurriculumItemCreateView.as_view(), name="curriculum_create"),
    path("curriculum/<int:pk>/edit/", views.CurriculumItemUpdateView.as_view(), name="curriculum_update"),
    path("curriculum/<int:pk>/delete/", views.CurriculumItemDeleteView.as_view(), name="curriculum_delete"),
    path("semesters/", views.SemesterListView.as_view(), name="semester_list"),
    path("semesters/create/", views.SemesterCreateView.as_view(), name="semester_create"),
    path("semesters/<int:pk>/edit/", views.SemesterUpdateView.as_view(), name="semester_update"),
    path("semesters/<int:pk>/toggle/", views.semester_toggle_active, name="semester_toggle_active"),
    path("programs/", views.ProgramListView.as_view(), name="program_list"),
    path("programs/create/", views.ProgramCreateView.as_view(), name="program_create"),
    path("programs/<int:pk>/edit/", views.ProgramUpdateView.as_view(), name="program_update"),
    path("programs/<int:pk>/delete/", views.ProgramDeleteView.as_view(), name="program_delete"),
    path("programs/<int:pk>/toggle/", views.program_toggle_active, name="program_toggle_active"),
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
        "danishman/",
        views.DanismanAdviseeListView.as_view(),
        name="danishman_advisees",
    ),
    path(
        "danishman/<int:student_pk>/",
        views.DanismanAdviseeDetailView.as_view(),
        name="danishman_advisee_detail",
    ),
    path(
        "danishman/<int:student_pk>/approve-all/",
        views.danishman_approve_all,
        name="danishman_approve_all",
    ),
    path(
        "instructor/grades/<int:enrollment_id>/",
        views.GradeEntryView.as_view(),
        name="grade_entry",
    ),
    path("devamsizlik/", views.AttendanceSectionListView.as_view(), name="attendance_sections"),
    path("devamsizlik/<int:section_pk>/yoklama/", views.AttendanceTakeView.as_view(), name="attendance_take"),
    # Zaman dilimleri
    path("offerings/<int:offering_pk>/timeslots/", views.SectionTimeSlotManageView.as_view(), name="timeslot_manage"),
    path("timeslots/<int:slot_pk>/delete/", views.timeslot_delete, name="timeslot_delete"),
    # Haftalık program
    path("haftalik-program/", views.WeeklyScheduleView.as_view(), name="weekly_schedule"),
]
