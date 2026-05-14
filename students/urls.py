"""
`students` URL rotaları: öğrenci alanı, transkript, müfredat, devamsızlık, seçmeli, mezuniyet, admin liste.
"""
from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentIndexView.as_view(), name="index"),
    path("transcript/", views.TranscriptView.as_view(), name="transcript"),
    path("graduation/", views.GraduationProgressView.as_view(), name="graduation"),
    path("elective-pools/", views.ElectivePoolStudentView.as_view(), name="elective_pools"),
    path("curriculum/", views.CurriculumPlanView.as_view(), name="curriculum"),
    path("devamsizlik/", views.StudentAttendanceView.as_view(), name="attendance"),
    path("admin/", views.StudentAdminListView.as_view(), name="admin_list"),
    path("admin/<int:pk>/edit/", views.StudentAdminEditView.as_view(), name="admin_edit"),
]
