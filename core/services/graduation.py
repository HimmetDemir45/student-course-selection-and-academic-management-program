"""
Mezuniyet ilerleme hesaplama servisi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from students.models import StudentProfile


@dataclass
class CourseProgress:
    code: str
    name: str
    credits: int
    course_type: str
    completed: bool


@dataclass
class GraduationProgress:
    program_name: str
    credits_required: int
    credits_completed: int
    credits_pct: int

    mandatory_total: int
    mandatory_completed: int
    mandatory_missing: list[CourseProgress]

    elective_total: int
    elective_completed: int

    all_program_courses: list[CourseProgress]
    extra_completed: list[CourseProgress]  # GENEL / başka program dersleri


def calculate_graduation_progress(student: "StudentProfile") -> GraduationProgress | None:
    """
    Öğrencinin mezuniyet ilerlemesini hesaplar.
    Program atanmamışsa None döner.
    """
    from courses.models import Course
    from enrollments.models import Enrollment

    program = student.program
    if program is None:
        return None

    # "Tamamlanan" = COMPLETED durumunda VE F dışı (geçer) not almış.
    completed_qs = (
        Enrollment.objects.filter(
            student=student,
            status=Enrollment.Status.COMPLETED,
        )
        .exclude(academic_grade__letter_grade="")
        .exclude(academic_grade__letter_grade__istartswith="F")
        .select_related("section__offering__course")
        .values_list("section__offering__course__code", flat=True)
    )
    completed_codes = set(completed_qs)

    # Tamamlanan derslerin toplam kredisi (tekrar eden kayıtları önlemek için DISTINCT)
    completed_courses_qs = (
        Course.objects.filter(code__in=completed_codes)
    )
    credits_completed = sum(c.credits for c in completed_courses_qs)

    # Program dersleri
    program_courses = list(
        Course.objects.filter(program=program).order_by("code")
    )
    program_course_codes = {c.code for c in program_courses}

    all_program = []
    mandatory_missing = []
    mandatory_total = 0
    mandatory_completed_count = 0
    elective_total = 0
    elective_completed_count = 0

    for c in program_courses:
        done = c.code in completed_codes
        cp = CourseProgress(
            code=c.code,
            name=c.name,
            credits=c.credits,
            course_type=c.course_type,
            completed=done,
        )
        all_program.append(cp)

        if c.course_type == "mandatory":
            mandatory_total += 1
            if done:
                mandatory_completed_count += 1
            else:
                mandatory_missing.append(cp)
        else:
            elective_total += 1
            if done:
                elective_completed_count += 1

    # Programın dışında tamamlanan ekstra dersler (GENEL, farklı program)
    extra_codes = completed_codes - program_course_codes
    extra_completed = []
    if extra_codes:
        for c in Course.objects.filter(code__in=extra_codes).order_by("code"):
            extra_completed.append(CourseProgress(
                code=c.code,
                name=c.name,
                credits=c.credits,
                course_type=c.course_type,
                completed=True,
            ))

    credits_required = program.credits_required
    credits_pct = min(100, int(round(100 * credits_completed / credits_required))) if credits_required else 0

    return GraduationProgress(
        program_name=program.name,
        credits_required=credits_required,
        credits_completed=credits_completed,
        credits_pct=credits_pct,
        mandatory_total=mandatory_total,
        mandatory_completed=mandatory_completed_count,
        mandatory_missing=mandatory_missing,
        elective_total=elective_total,
        elective_completed=elective_completed_count,
        all_program_courses=all_program,
        extra_completed=extra_completed,
    )
