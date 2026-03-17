from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("students/", include("students.urls")),
    path("instructors/", include("instructors.urls")),
    path("courses/", include("courses.urls")),
    path("enrollments/", include("enrollments.urls")),
    path("academic/", include("academic.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("audit-logs/", include("audit_logs.urls")),
]
