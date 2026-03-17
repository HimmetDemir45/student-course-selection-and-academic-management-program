from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    EVENT_CHOICES = (
        ("register", "Register"),
        ("login", "Login"),
        ("logout", "Logout"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        username = self.user.username if self.user else "anonymous"
        return f"{self.event_type} - {username}"
