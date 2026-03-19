from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor", "target_type", "target_id", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("actor__username", "actor__email", "target_type", "target_id")
    ordering = ("-created_at",)
