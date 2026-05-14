"""
Denetim olayı (AuditEvent) modeli: kim/ne zaman/ne yaptı kaydını tutar (event_type, actor, target, metadata, request_id).
"""
from django.db import models
from django.conf import settings

from core.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    event_type = models.CharField(max_length=50, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actor_audit_logs",
    )
    target_type = models.CharField(max_length=100, blank=True, db_index=True)
    target_id = models.CharField(max_length=64, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("event_type", "created_at"), name="idx_audit_event_created"),
        ]

    def __str__(self):
        username = self.actor.username if self.actor else "anonymous"
        return f"{self.event_type} - {username}"
