"""
Özel User modeli (role: student/instructor/admin) ve admin yetkilendirme talebi (AdminRequest) modelleri.
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Yönetici")
        STUDENT = "student", _("Öğrenci")
        INSTRUCTOR = "instructor", _("Öğretim üyesi")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(unique=True)
    is_founder_admin = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Kurucu yönetici: tek hesap; yalnızca bu kullanıcı admin taleplerini onaylayabilir."),
    )

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        super().save(*args, **kwargs)


class UserManager(DjangoUserManager):
    """Süper kullanıcıların varsayılan rolünün öğrenci kalmasını önler (otomatik öğrenci profili oluşturulmaz)."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email=email, password=password, **extra_fields)


User.add_to_class("objects", UserManager())


class AdminRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Beklemede")
        APPROVED = "approved", _("Onaylandı")
        REJECTED = "rejected", _("Reddedildi")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_admin_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "created_at"), name="idx_adminreq_status_created"),
        ]

    def __str__(self):
        return f"{self.user_id} {self.status}"
