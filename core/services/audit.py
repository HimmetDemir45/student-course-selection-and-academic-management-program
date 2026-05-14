"""
Audit log servis sarmalayıcısı — event_type sabitleri ve audit_enrollment_event yardımcıları.
"""
from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from audit_logs.services import log_event

EVENT_ENROLLMENT_CREATED = "enrollment_created"
EVENT_ENROLLMENT_UPDATED = "enrollment_updated"
EVENT_ENROLLMENT_STATUS = "enrollment_status_changed"
EVENT_GRADE_ENTRY = "grade_entry"
EVENT_LOGIN = "login"
EVENT_LOGOUT = "logout"


def _request_meta(request: HttpRequest | None) -> dict[str, Any]:
    if not request:
        return {}
    return {
        "ip": request.META.get("REMOTE_ADDR", ""),
        "path": request.path,
    }


def audit_enrollment_event(
    event_type: str,
    *,
    actor,
    enrollment,
    request: HttpRequest | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    meta: dict[str, Any] = {
        "student_id": enrollment.student_id,
        "section_id": enrollment.section_id,
        "status": enrollment.status,
        "offering_id": enrollment.section.offering_id,
    }
    meta.update(_request_meta(request))
    if extra:
        meta.update(extra)
    log_event(
        event_type=event_type,
        actor=actor,
        target_type="enrollments.Enrollment",
        target_id=str(enrollment.pk),
        metadata=meta,
        request=request,
    )


def audit_grade_event(
    *,
    actor,
    enrollment,
    grade_snapshot: dict[str, Any],
    request: HttpRequest | None = None,
) -> None:
    meta = {
        "enrollment_id": enrollment.pk,
        "student_id": enrollment.student_id,
        "grade": grade_snapshot,
    }
    meta.update(_request_meta(request))
    log_event(
        event_type=EVENT_GRADE_ENTRY,
        actor=actor,
        target_type="academic.Grade",
        target_id=str(enrollment.pk),
        metadata=meta,
        request=request,
    )
