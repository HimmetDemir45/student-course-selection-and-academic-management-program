from django.views.generic import ListView

from core.permissions import AdminRequiredMixin

from .models import AuditLog


class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "audit_logs/list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        return AuditLog.objects.select_related("actor").order_by("-created_at")
