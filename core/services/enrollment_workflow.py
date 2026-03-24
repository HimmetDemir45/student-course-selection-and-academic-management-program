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
    "dropped": (),
    "withdrawn": (),
    "completed": (),
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
    if new_status == Enrollment.Status.DROPPED:
        enrollment_rules.validate_drop_window(enrollment, new_status, at)
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
