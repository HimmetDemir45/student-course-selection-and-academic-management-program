"""Smoke test: seed_demo_users komutu beklenen kayıtları üretiyor mu?"""

import pytest
from decimal import Decimal
from django.core.management import call_command

from accounts.models import User
from academic.models import Grade, Transcript
from enrollments.models import Enrollment
from instructors.models import InstructorProfile
from students.models import StudentProfile

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_seed_demo_users_creates_full_demo_dataset():
    call_command("seed_demo_users")

    student = User.objects.get(username="demo_ogrenci")
    instructor = User.objects.get(username="demo_akademisyen")
    assert student.role == User.Role.STUDENT
    assert instructor.role == User.Role.INSTRUCTOR

    sp = StudentProfile.objects.get(user=student)
    assert sp.student_no == "20260042"
    assert sp.advisor is not None

    ip = InstructorProfile.objects.get(user=instructor)
    assert sp.advisor_id == ip.pk

    # GPA verisi: en az 2 geçmiş transcript ve >= 3.40 ortalama
    transcripts = Transcript.objects.filter(student=sp).order_by("-semester__academic_year")
    assert transcripts.count() >= 2
    avg_gpa = sum(t.gpa for t in transcripts) / transcripts.count()
    assert avg_gpa > Decimal("3.30")

    # Aktif dönem enrollment + Grade
    enrollment = Enrollment.objects.filter(student=sp).first()
    assert enrollment is not None
    grade = Grade.objects.get(enrollment=enrollment)
    assert grade.letter_grade == "AA"
    assert grade.numeric_grade >= Decimal("90.00")


def test_seed_demo_users_is_idempotent():
    call_command("seed_demo_users")
    call_command("seed_demo_users")  # ikinci kez — çoğaltmamalı
    assert User.objects.filter(username="demo_ogrenci").count() == 1
    assert User.objects.filter(username="demo_akademisyen").count() == 1
    assert StudentProfile.objects.filter(student_no="20260042").count() == 1
