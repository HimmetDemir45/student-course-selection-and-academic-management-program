from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone

from academic.models import CourseSection, Department, Program, Semester
from courses.models import Course, CourseOffering
from enrollments.models import Enrollment
from students.models import StudentProfile

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.concurrency, pytest.mark.integration]


def _create_student(username: str, student_no: str, department: Department, program: Program):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@test.local",
        password="pass12345",
        role="student",
    )
    return StudentProfile.objects.create(
        user=user,
        student_no=student_no,
        department=department,
        program=program,
    )


def _attempt_enroll(student_id: int, section_id: int, q: Queue):
    close_old_connections()
    try:
        with transaction.atomic():
            enrollment = Enrollment(student_id=student_id, section_id=section_id, status=Enrollment.Status.ENROLLED)
            enrollment.save()
        q.put(("ok", enrollment.pk))
    except (ValidationError, IntegrityError) as exc:
        q.put(("fail", str(exc)))
    finally:
        close_old_connections()


def test_same_section_parallel_enrollment_does_not_exceed_capacity():
    today = timezone.localdate()
    dep = Department.objects.create(name="Muhendislik", code="MUH-CN")
    program = Program.objects.create(department=dep, name="BLM-CN", code="BLM-CN")
    semester = Semester.objects.create(
        name="2026 Bahar",
        academic_year="2025-2026",
        term=Semester.Term.SPRING,
        start_date=today - timedelta(days=5),
        end_date=today + timedelta(days=90),
        add_drop_start=today - timedelta(days=2),
        add_drop_end=today + timedelta(days=7),
    )
    course = Course.objects.create(department=dep, code="CSCN101", name="Concurrency", credits=3)
    offering = CourseOffering.objects.create(course=course, semester=semester, section="A", quota=1)
    section = CourseSection.objects.get(offering=offering)

    s1 = _create_student("cn_stu_1", "CN001", dep, program)
    s2 = _create_student("cn_stu_2", "CN002", dep, program)

    results = Queue()
    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_attempt_enroll, s1.id, section.id, results)
        f2 = pool.submit(_attempt_enroll, s2.id, section.id, results)
        f1.result()
        f2.result()

    statuses = [results.get_nowait()[0] for _ in range(2)]
    enrolled_count = Enrollment.objects.filter(
        section=section, status__in=[Enrollment.Status.ENROLLED, Enrollment.Status.PENDING]
    ).count()

    assert enrolled_count <= 1, "Kapasite 1 iken ayni section icin 1'den fazla aktif kayit olustu."
    assert statuses.count("ok") <= 1, "Race-condition sonucu birden fazla paralel kayit basarili oldu."
