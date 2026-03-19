from django.db import models

from core.models import TimeStampedModel


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ENROLLED = "enrolled", "Enrolled"
        DROPPED = "dropped", "Dropped"
        COMPLETED = "completed", "Completed"

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    offering = models.ForeignKey(
        "courses.CourseOffering",
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
                fields=("student", "offering"),
                name="uniq_enrollment_student_offering",
            )
        ]
        indexes = [
            models.Index(fields=("student", "status"), name="idx_enrollment_student_status"),
        ]

    def __str__(self):
        return f"{self.student.student_no} - {self.offering}"


class Grade(TimeStampedModel):
    enrollment = models.OneToOneField(
        "enrollments.Enrollment",
        on_delete=models.CASCADE,
        related_name="grade",
    )
    letter_grade = models.CharField(max_length=2, blank=True)
    numeric_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.enrollment} - {self.letter_grade or '-'}"
