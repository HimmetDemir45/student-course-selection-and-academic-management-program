from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from academic.models import Department, Grade, Program, Semester, Transcript
from core.services.gpa import gpa_from_completed_enrollments
from courses.models import Course, CourseOffering
from enrollments.models import Enrollment
from students.models import StudentProfile

pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.smoke]


def _quantize_2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _build_student(dep: Department, program: Program) -> StudentProfile:
    user = get_user_model().objects.create_user(
        username="gpa_stu",
        email="gpa_stu@test.local",
        password="pass12345",
        role="student",
    )
    sp = StudentProfile.objects.get(user=user)
    sp.student_no = "GPA001"
    sp.department = dep
    sp.program = program
    sp.save()
    return sp


def test_grade_to_gpa_to_transcript_golden_dataset_integrity():
    today = timezone.localdate()

    dep = Department.objects.create(name="Fen", code="FEN-GPA")
    program = Program.objects.create(department=dep, name="Matematik", code="MAT-GPA")
    semester = Semester.objects.create(
        name="2026 Bahar",
        academic_year="2025-2026",
        term=Semester.Term.SPRING,
        start_date=today - timedelta(days=10),
        end_date=today + timedelta(days=120),
        add_drop_start=today - timedelta(days=5),
        add_drop_end=today + timedelta(days=15),
    )
    student = _build_student(dep, program)

    # Golden dataset: (A,3cr), (B,4cr), (C,2cr) => (4*3 + 3*4 + 2*2)/9 = 3.11
    c1 = Course.objects.create(department=dep, code="GPA101", name="A Course", credits=3)
    c2 = Course.objects.create(department=dep, code="GPA102", name="B Course", credits=4)
    c3 = Course.objects.create(department=dep, code="GPA103", name="C Course", credits=2)

    o1 = CourseOffering.objects.create(course=c1, semester=semester, section="A", quota=30)
    o2 = CourseOffering.objects.create(course=c2, semester=semester, section="A", quota=30)
    o3 = CourseOffering.objects.create(course=c3, semester=semester, section="A", quota=30)

    e1 = Enrollment.objects.create(student=student, section=o1.section_detail, status=Enrollment.Status.COMPLETED)
    e2 = Enrollment.objects.create(student=student, section=o2.section_detail, status=Enrollment.Status.COMPLETED)
    e3 = Enrollment.objects.create(student=student, section=o3.section_detail, status=Enrollment.Status.COMPLETED)

    Grade.objects.create(enrollment=e1, letter_grade="A")
    Grade.objects.create(enrollment=e2, letter_grade="B")
    Grade.objects.create(enrollment=e3, letter_grade="C")

    qs = Enrollment.objects.filter(student=student).select_related("section__offering__course", "academic_grade")
    gpa, credits = gpa_from_completed_enrollments(qs)

    expected_gpa = _quantize_2((Decimal("4.0") * 3 + Decimal("3.0") * 4 + Decimal("2.0") * 2) / Decimal("9"))
    assert credits == 9
    assert gpa == expected_gpa
    assert gpa == Decimal("3.11")

    transcript = Transcript.objects.create(
        student=student,
        semester=semester,
        gpa=gpa,
        total_credits=credits,
    )
    transcript.refresh_from_db()

    assert transcript.gpa == Decimal("3.11")
    assert transcript.total_credits == 9
