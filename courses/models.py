from django.db import models
from django.db.models import F, Q

from core.models import TimeStampedActiveModel, TimeStampedModel


class Course(TimeStampedActiveModel):
    class CourseType(models.TextChoices):
        MANDATORY = "mandatory", "Zorunlu"
        ELECTIVE = "elective", "Seçmeli"
        FREE_ELECTIVE = "free_elective", "Serbest Seçmeli"

    department = models.ForeignKey(
        "academic.Department",
        on_delete=models.PROTECT,
        related_name="courses",
    )
    program = models.ForeignKey(
        "academic.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
    )
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    credits = models.PositiveSmallIntegerField(default=3)
    course_type = models.CharField(
        max_length=20,
        choices=CourseType.choices,
        default=CourseType.MANDATORY,
        db_index=True,
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} - {self.name}"


class ElectivePool(TimeStampedActiveModel):
    """
    Seçmeli ders havuzu: programın öğrencilerin belirli sayıda ders seçmesi
    gereken tematik ders grubu. Örn. "Teknik Seçmeli I — 2 ders seçiniz".
    """
    program = models.ForeignKey(
        "academic.Program",
        on_delete=models.CASCADE,
        related_name="elective_pools",
    )
    name = models.CharField(max_length=150, db_index=True)
    description = models.TextField(
        blank=True,
        help_text="Öğrencilere gösterilecek açıklama.",
    )
    required_count = models.PositiveSmallIntegerField(
        default=1,
        help_text="Öğrencinin bu havuzdan seçmesi gereken ders sayısı.",
    )
    courses = models.ManyToManyField(
        "courses.Course",
        blank=True,
        related_name="elective_pools",
    )

    class Meta:
        ordering = ("program__code", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("program", "name"),
                name="uniq_elective_pool_program_name",
            )
        ]

    def __str__(self):
        return f"{self.program.code} — {self.name}"


class CoursePrerequisite(TimeStampedModel):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="prerequisite_links",
    )
    prerequisite = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="required_for_links",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("course", "prerequisite"),
                name="uniq_course_prerequisite",
            ),
            models.CheckConstraint(
                check=~Q(course=F("prerequisite")),
                name="check_course_not_self_prereq",
            ),
        ]
        ordering = ("course__code",)

    def __str__(self):
        return f"{self.course.code} <- {self.prerequisite.code}"


class Classroom(TimeStampedActiveModel):
    building = models.CharField(max_length=100, db_index=True)
    room_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()

    class Meta:
        ordering = ("building", "room_number")
        constraints = [
            models.UniqueConstraint(
                fields=("building", "room_number"),
                name="uniq_classroom_building_room",
            )
        ]

    def __str__(self):
        return f"{self.building} {self.room_number}"


class CourseOffering(TimeStampedActiveModel):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.PROTECT,
        related_name="offerings",
    )
    semester = models.ForeignKey(
        "academic.Semester",
        on_delete=models.PROTECT,
        related_name="offerings",
    )
    instructor = models.ForeignKey(
        "instructors.InstructorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offerings",
    )
    classroom = models.ForeignKey(
        "courses.Classroom",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offerings",
    )
    section = models.CharField(max_length=10)
    quota = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ("-semester__academic_year", "course__code", "section")
        constraints = [
            models.UniqueConstraint(
                fields=("course", "semester", "section"),
                name="uniq_offering_course_semester_section",
            )
        ]
        indexes = [
            models.Index(fields=("semester", "is_active"), name="idx_offering_sem_active"),
            models.Index(fields=("instructor",), name="idx_offering_instructor"),
        ]

    def __str__(self):
        return f"{self.course.code} / {self.semester} / {self.section}"
