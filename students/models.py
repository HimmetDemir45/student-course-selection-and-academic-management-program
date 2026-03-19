from django.db import models

from core.models import TimeStampedActiveModel


class StudentProfile(TimeStampedActiveModel):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_no = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.ForeignKey(
        "academic.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    program = models.ForeignKey(
        "academic.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    advisor = models.ForeignKey(
        "instructors.InstructorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advisees",
    )
    enrollment_year = models.PositiveSmallIntegerField(default=2026, db_index=True)

    class Meta:
        ordering = ("student_no",)

    def __str__(self):
        return f"{self.student_no} - {self.user.get_full_name() or self.user.username}"
