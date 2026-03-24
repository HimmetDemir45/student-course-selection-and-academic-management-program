"""
Atomic enrollment with row lock on CourseSection to reduce capacity race oversubscription.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import transaction

from academic.models import CourseSection
from enrollments.models import Enrollment

if TYPE_CHECKING:
    from students.models import StudentProfile


def _parse_section_pk(raw) -> int | None:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def enroll_student_in_section_atomic(student_profile: StudentProfile, section_id_raw) -> Enrollment:
    """
    Locks the CourseSection row (select_for_update) then validates and saves enrollment.
    Raises CourseSection.DoesNotExist, ValidationError, IntegrityError (duplicate student+section).
    """
    pk = _parse_section_pk(section_id_raw)
    if pk is None:
        raise ValidationError("Gecersiz section secimi.")

    with transaction.atomic():
        section = (
            CourseSection.objects.select_for_update(of=("self",))
            .select_related(
                "offering",
                "offering__course",
                "offering__semester",
                "offering__instructor",
            )
            .get(pk=pk, is_active=True, offering__is_active=True)
        )
        enr = Enrollment(
            student=student_profile,
            section=section,
            status=Enrollment.Status.ENROLLED,
        )
        enr.save()
        return enr


def enroll_student_integrity_message() -> str:
    return "Bu derse zaten kayitlisiniz veya kayit istegi cakisiyor. Sayfayi yenileyip kontrol edin."
