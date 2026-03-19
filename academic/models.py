from django.db import models
from django.conf import settings

from core.models import TimeStampedActiveModel, TimeStampedModel


class Department(TimeStampedActiveModel):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Program(TimeStampedActiveModel):
    class DegreeLevel(models.TextChoices):
        UNDERGRAD = "undergrad", "Undergraduate"
        GRAD = "grad", "Graduate"

    department = models.ForeignKey(
        "academic.Department",
        on_delete=models.PROTECT,
        related_name="programs",
    )
    name = models.CharField(max_length=150, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    degree_level = models.CharField(
        max_length=20,
        choices=DegreeLevel.choices,
        default=DegreeLevel.UNDERGRAD,
    )

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("department", "name"),
                name="uniq_program_department_name",
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Semester(TimeStampedActiveModel):
    class Term(models.TextChoices):
        FALL = "fall", "Fall"
        SPRING = "spring", "Spring"
        SUMMER = "summer", "Summer"

    name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=9, db_index=True)  # 2025-2026
    term = models.CharField(max_length=10, choices=Term.choices, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ("-academic_year", "term")
        constraints = [
            models.UniqueConstraint(
                fields=("academic_year", "term"),
                name="uniq_semester_year_term",
            )
        ]

    def __str__(self):
        return f"{self.academic_year} {self.term}"


class Transcript(TimeStampedModel):
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="transcripts",
    )
    semester = models.ForeignKey(
        "academic.Semester",
        on_delete=models.PROTECT,
        related_name="transcripts",
    )
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total_credits = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-semester__academic_year",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "semester"),
                name="uniq_transcript_student_semester",
            )
        ]
        indexes = [
            models.Index(fields=("student", "semester"), name="idx_transcript_student_sem"),
        ]

    def __str__(self):
        return f"{self.student.student_no} - {self.semester}"


class Announcement(TimeStampedActiveModel):
    class TargetRole(models.TextChoices):
        ALL = "all", "All"
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        ADMIN = "admin", "Admin"

    title = models.CharField(max_length=200, db_index=True)
    body = models.TextField()
    semester = models.ForeignKey(
        "academic.Semester",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )
    department = models.ForeignKey(
        "academic.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )
    target_role = models.CharField(
        max_length=20,
        choices=TargetRole.choices,
        default=TargetRole.ALL,
        db_index=True,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_announcements",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("is_active", "target_role"), name="idx_ann_active_role"),
        ]

    def __str__(self):
        return self.title
