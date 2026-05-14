"""
InstructorProfile modeli: employee_no, title, department, is_approved, **is_advisor** (danışman yetkisi).
"""
from django.db import models

from core.models import TimeStampedActiveModel


class InstructorProfile(TimeStampedActiveModel):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    employee_no = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.ForeignKey(
        "academic.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instructors",
    )
    title = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(
        default=False,
        help_text="Yönetici onayı verildi mi? Onaysız akademisyenler ders işlemi yapamaz.",
    )
    is_advisor = models.BooleanField(
        default=False,
        help_text="Danışman yetkisi var mı? Sadece danışmanlar öğrenci ders onayı yapabilir.",
    )

    class Meta:
        ordering = ("employee_no",)

    def __str__(self):
        return f"{self.employee_no} - {self.user.get_full_name() or self.user.username}"
