from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils import timezone

from core.services import enrollment_rules
from core.services.audit import (
    EVENT_ENROLLMENT_STATUS,
    audit_enrollment_event,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser



ALLOWED = {
    "pending": ("enrolled", "dropped"),
    "enrolled": ("dropped", "withdrawn", "completed"),
    "dropped": ("pending",),   # bekleme listesinden terfi veya yeniden kayıt
    "withdrawn": (),
    "completed": ("dropped",),  # yanlış girilmiş notun geri alınması için
    "waitlisted": ("pending", "dropped"),
}


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in ALLOWED.get(from_status, ())


def transition_enrollment_status(
    enrollment,
    new_status: str,
    *,
    actor: AbstractBaseUser | None = None,
    request=None,
    at: date | None = None,
) -> None:
    from enrollments.models import Enrollment

    at = at or timezone.localdate()
    old = enrollment.status
    if old == new_status:
        return
    if not can_transition(old, new_status):
        raise ValidationError(f"Durum gecisi izin verilmiyor: {old} -> {new_status}")
    # Drop window yalnızca ENROLLED→DROPPED için geçerli; COMPLETED'dan
    # geri alma (hata düzeltme) ve PENDING→DROPPED (red) bu kontrolün dışında.
    if new_status == Enrollment.Status.DROPPED and old == Enrollment.Status.ENROLLED:
        enrollment_rules.validate_drop_window(enrollment, new_status, at)
    # Danışman onayı (PENDING→ENROLLED) anında kapasite kontrolü yap
    if new_status == Enrollment.Status.ENROLLED and old == Enrollment.Status.PENDING:
        enrollment_rules.validate_capacity(enrollment)
    enrollment.status = new_status
    enrollment.save()
    if actor is not None and getattr(actor, "is_authenticated", False):
        audit_enrollment_event(
            EVENT_ENROLLMENT_STATUS,
            actor=actor,
            enrollment=enrollment,
            request=request,
            extra={"old_status": old, "new_status": new_status},
        )

    # Kapasite serbest kalan geçişler → ilk WAITLISTED'i PENDING'e terfi et.
    freed = new_status in (
        Enrollment.Status.DROPPED,
        Enrollment.Status.WITHDRAWN,
    ) and old in (
        Enrollment.Status.ENROLLED,
        Enrollment.Status.PENDING,
    )
    if freed:
        promote_first_waitlist(enrollment.section_id, actor=actor, request=request)


def promote_first_waitlist(section_id: int, *, actor=None, request=None) -> bool:
    """
    Bir section'da kapasite serbest kaldığında ilk WAITLISTED kaydı PENDING'e
    çeker. Kapasite hâlâ doluysa hiçbir şey yapmaz. Bulup terfi ettirdiyse True.
    """
    from academic.models import CourseSection
    from enrollments.models import Enrollment
    from django.db import transaction

    with transaction.atomic():
        next_enr = (
            Enrollment.objects.select_for_update(of=("self",))
            .filter(section_id=section_id, status=Enrollment.Status.WAITLISTED)
            .order_by("created_at")
            .first()
        )
        if next_enr is None:
            return False
        section = CourseSection.objects.select_related("offering").get(pk=section_id)
        cap = enrollment_rules._effective_capacity(section)
        used = enrollment_rules.count_active_enrollments(section_id, exclude_enrollment_id=None)
        if used >= cap:
            return False  # hâlâ dolu
        next_enr.status = Enrollment.Status.PENDING
        # Bypass full_clean — kapasite kontrolü zaten yapıldı, drop window
        # gerekmez (PENDING'e geçiş için).
        super(Enrollment, next_enr).save(update_fields=["status", "updated_at"])
        if actor is not None and getattr(actor, "is_authenticated", False):
            audit_enrollment_event(
                EVENT_ENROLLMENT_STATUS,
                actor=actor,
                enrollment=next_enr,
                request=request,
                extra={"old_status": "waitlisted", "new_status": "pending", "auto": True},
            )
    return True
