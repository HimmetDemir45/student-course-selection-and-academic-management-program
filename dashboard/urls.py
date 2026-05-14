"""
`dashboard` URL rotaları: pano, kurucu kuyruğu, kullanıcı onayları, istatistikler.
"""
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardIndexView.as_view(), name="index"),
    path("admin-talepleri/", views.AdminRequestQueueView.as_view(), name="admin_requests"),
    path(
        "admin-talepleri/<int:pk>/onayla/",
        views.AdminRequestApproveView.as_view(),
        name="admin_request_approve",
    ),
    path(
        "admin-talepleri/<int:pk>/reddet/",
        views.AdminRequestRejectView.as_view(),
        name="admin_request_reject",
    ),
    path("kullanici-onaylari/", views.UserApprovalQueueView.as_view(), name="user_approvals"),
    path("kullanici-onaylari/ogrenci/<int:pk>/", views.ApproveStudentView.as_view(), name="approve_student"),
    path("kullanici-onaylari/akademisyen/<int:pk>/", views.ApproveInstructorView.as_view(), name="approve_instructor"),
    path("istatistik/", views.StatisticsView.as_view(), name="statistics"),
    path("donemler/", views.SemesterManagementView.as_view(), name="semester_management"),
    path("donemler/yeni/", views.SemesterCreateView.as_view(), name="semester_create"),
    path("donemler/<int:pk>/duzenle/", views.SemesterEditView.as_view(), name="semester_edit"),
    path("donemler/<int:pk>/ac-kapat/", views.toggle_semester_active, name="semester_toggle_active"),
    path("ogrenciler/atama/", views.StudentAssignmentListView.as_view(), name="student_assignment_list"),
    path("ogrenciler/yeni/", views.StudentCreateView.as_view(), name="student_create"),
    path("ogrenciler/<int:pk>/atama/", views.StudentAssignmentEditView.as_view(), name="student_assignment_edit"),
]
