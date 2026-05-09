"""Öğrenci / öğretim üyesi profillerinin kullanıcı kaydı ve rol ile uyumlu oluşturulması."""

from __future__ import annotations

from django.utils import timezone

from accounts.models import User
from instructors.models import InstructorProfile
from students.models import StudentProfile


def _allocate_unique_number(prefix: str, user_pk: int, exists) -> str:
    core = str(user_pk)
    candidate = f"{prefix}{core}"
    if len(candidate) > 20:
        candidate = core[-20:]
    n = 0
    while exists(candidate):
        n += 1
        tail = f"-{n}"
        trimmed = f"{prefix}{core}"
        if len(trimmed) + len(tail) > 20:
            trimmed = trimmed[: max(1, 20 - len(tail))]
        candidate = (trimmed + tail)[:20]
    return candidate


def allocate_unique_student_no(user: User) -> str:
    return _allocate_unique_number(
        "S",
        user.pk,
        lambda cand: StudentProfile.objects.filter(student_no=cand).exists(),
    )


def allocate_unique_employee_no(user: User) -> str:
    return _allocate_unique_number(
        "E",
        user.pk,
        lambda cand: InstructorProfile.objects.filter(employee_no=cand).exists(),
    )


def ensure_student_profile(user: User) -> StudentProfile:
    try:
        return user.student_profile
    except StudentProfile.DoesNotExist:
        pass
    student_no = allocate_unique_student_no(user)
    return StudentProfile.objects.create(
        user=user,
        student_no=student_no,
        enrollment_year=timezone.now().year,
    )


def ensure_instructor_profile(user: User) -> InstructorProfile:
    try:
        return user.instructor_profile
    except InstructorProfile.DoesNotExist:
        pass
    employee_no = allocate_unique_employee_no(user)
    return InstructorProfile.objects.create(user=user, employee_no=employee_no)


def provision_role_profiles(user: User) -> None:
    role = (user.role or User.Role.STUDENT).strip()
    if role == User.Role.STUDENT:
        ensure_student_profile(user)
    elif role == User.Role.INSTRUCTOR:
        ensure_instructor_profile(user)
