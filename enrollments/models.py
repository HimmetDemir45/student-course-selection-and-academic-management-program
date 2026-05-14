"""
Enrollment modeli: öğrenci-şube ilişkisi, durum (PENDING/ENROLLED/...), danışman onay alanları (instructor_approved, instructor_comment).
"""
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel
from core.services.enrollment_rules import validate_enrollment_save


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ENROLLED = "enrolled", "Enrolled"
        DROPPED = "dropped", "Dropped"
        WITHDRAWN = "withdrawn", "Withdrawn"
        COMPLETED = "completed", "Completed"
        WAITLISTED = "waitlisted", "Bekleme listesi"

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

    # Eğitim görevlisi alternatif ders önerisi
    reassignment_suggested_course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reassignment_suggestions",
    )
    reassignment_note = models.TextField(blank=True)

    # Eğitim görevlisi onayı (instructor approval)
    instructor_approved = models.BooleanField(default=False)
    instructor_approved_by = models.ForeignKey(
        "instructors.InstructorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_enrollments",
    )
    instructor_approved_at = models.DateTimeField(null=True, blank=True)
    instructor_comment = models.TextField(blank=True, help_text="Eğitim görevlisinin notu")

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
