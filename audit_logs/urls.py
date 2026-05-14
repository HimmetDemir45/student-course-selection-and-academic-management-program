"""
`audit_logs` URL rotaları (admin için olay listesi).
"""
from django.urls import path

from . import views

app_name = "audit_logs"

urlpatterns = [
    path("", views.AuditLogListView.as_view(), name="index"),
]
