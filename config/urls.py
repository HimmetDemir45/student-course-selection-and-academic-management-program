from django.contrib import admin
from django.urls import include, path

from core import views as core_views

urlpatterns = [
    path("health/live/", core_views.health_live, name="health_live"),
    path("health/ready/", core_views.health_ready, name="health_ready"),
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

handler403 = "core.views.handler403"
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
