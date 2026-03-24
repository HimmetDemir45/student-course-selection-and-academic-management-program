from django.db import models

from core.models import TimeStampedModel
from core.services.enrollment_rules import validate_enrollment_save


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ENROLLED = "enrolled", "Enrolled"
        DROPPED = "dropped", "Dropped"
        WITHDRAWN = "withdrawn", "Withdrawn"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    section = models.ForeignKey(
        "academic.CourseSection",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "section"),
                name="uniq_enrollment_student_section",
            )
        ]
        indexes = [
            models.Index(fields=("student", "status"), name="idx_enrollment_student_status"),
            models.Index(fields=("section", "status"), name="idx_enrollment_section_status"),
        ]

    def __str__(self):
        return f"{self.student.student_no} - {self.section}"

    def clean(self):
        validate_enrollment_save(self)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
