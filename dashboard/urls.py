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
]
