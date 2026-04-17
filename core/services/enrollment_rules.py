from __future__ import annotations

from datetime import date
from datetime import time
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils import timezone

if TYPE_CHECKING:
    from enrollments.models import Enrollment


def _effective_capacity(section) -> int:
    from academic.models import CourseSection

    if not isinstance(section, CourseSection):
        return 0
    if section.max_enrollment is not None:
        return int(section.max_enrollment)
    return int(section.offering.quota)


def is_within_add_drop(semester, at: date | None = None) -> bool:
    at = at or timezone.localdate()
    if semester.add_drop_start is None or semester.add_drop_end is None:
        return True
    return semester.add_drop_start <= at <= semester.add_drop_end


def count_active_enrollments(section_id: int, exclude_enrollment_id: int | None = None) -> int:
    """
    Hot path for capacity checks. Composite DB index on (section, status) keeps this COUNT fast
    as sections grow (see Enrollment.Meta.indexes).
    """
    from enrollments.models import Enrollment

    qs = Enrollment.objects.filter(
        section_id=section_id,
        status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
    )
    if exclude_enrollment_id:
        qs = qs.exclude(pk=exclude_enrollment_id)
    return qs.count()


def validate_capacity(enrollment: Enrollment) -> None:
    if enrollment.status not in (
        enrollment.Status.ENROLLED,
        enrollment.Status.PENDING,
    ):
        return
    cap = _effective_capacity(enrollment.section)
    used = count_active_enrollments(enrollment.section_id, enrollment.pk)
    if used >= cap:
        raise ValidationError("Bu section kapasitesi dolu.")


def student_has_completed_course(student_id: int, course_id: int) -> bool:
    from enrollments.models import Enrollment

    return Enrollment.objects.filter(
        student_id=student_id,
        section__offering__course_id=course_id,
        status=Enrollment.Status.COMPLETED,
    ).exists()


def validate_prerequisites(enrollment: Enrollment) -> None:
    if enrollment.status not in (
        enrollment.Status.ENROLLED,
        enrollment.Status.PENDING,
    ):
        return
    from courses.models import CoursePrerequisite

    course_id = enrollment.section.offering.course_id
    links = CoursePrerequisite.objects.filter(course_id=course_id).select_related(
        "prerequisite"
    )
    missing = []
    for link in links:
        if not student_has_completed_course(enrollment.student_id, link.prerequisite_id):
            missing.append(link.prerequisite.code)
    if missing:
        raise ValidationError(
            "Onkosul dersler tamamlanmamis: " + ", ".join(missing)
        )


def time_ranges_overlap(
    start_a: time, end_a: time, start_b: time, end_b: time
) -> bool:
    return start_a < end_b and start_b < end_a


def validate_schedule_conflict(enrollment: Enrollment) -> None:
    from academic.models import SectionTimeSlot
    from enrollments.models import Enrollment

    if enrollment.status not in (
        Enrollment.Status.ENROLLED,
        Enrollment.Status.PENDING,
    ):
        return

    slots = list(
        SectionTimeSlot.objects.filter(section_id=enrollment.section_id).values(
            "weekday", "start_time", "end_time"
        )
    )
    if not slots:
        return

    others = (
        Enrollment.objects.filter(
            student_id=enrollment.student_id,
            status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
        )
        .exclude(pk=enrollment.pk or 0)
        .values_list("section_id", flat=True)
    )
    other_section_ids = list(others)
    if not other_section_ids:
        return

    # Filter by section list; SectionTimeSlot(section, weekday) index reduces scan cost.
    other_slots = SectionTimeSlot.objects.filter(section_id__in=other_section_ids)
    for s in slots:
        for o in other_slots:
            if s["weekday"] != o.weekday:
                continue
            if time_ranges_overlap(
                s["start_time"], s["end_time"], o.start_time, o.end_time
            ):
                raise ValidationError(
                    "Zaman cakismasi: baska bir secili dersle saat ust uste biniyor."
                )


def validate_add_drop_for_new_enrollment(enrollment: Enrollment, at: date | None = None) -> None:
    if enrollment.status not in (
        enrollment.Status.ENROLLED,
        enrollment.Status.PENDING,
    ):
        return
    sem = enrollment.section.offering.semester
    if not is_within_add_drop(sem, at):
        raise ValidationError("Kayit ekleme donemi kapali.")


def validate_drop_window(enrollment: Enrollment, new_status: str, at: date | None = None) -> None:
    from enrollments.models import Enrollment

    if new_status != Enrollment.Status.DROPPED:
        return
    sem = enrollment.section.offering.semester
    if not is_within_add_drop(sem, at):
        raise ValidationError("Ders birakma penceresi kapali.")


def validate_enrollment_save(enrollment: Enrollment) -> None:
    """Called from Enrollment.clean() — full rule pass for active rows."""
    old_status = None
    if enrollment.pk:
        from enrollments.models import Enrollment as E

        prev = E.objects.filter(pk=enrollment.pk).values_list("status", flat=True).first()
        old_status = prev

    validate_capacity(enrollment)
    validate_prerequisites(enrollment)
    validate_schedule_conflict(enrollment)

    if enrollment.pk is None:
        validate_add_drop_for_new_enrollment(enrollment)
    elif (
        old_status != enrollment.status
        and enrollment.status == enrollment.Status.DROPPED
    ):
        validate_drop_window(enrollment, enrollment.Status.DROPPED)


def collect_enrollment_preview_messages(student_profile, section) -> dict:
    """
    Ders kaydı ekranı için salt okunur önizleme; DB'ye yazmaz.
    Rollback: enrollments/views.py ve şablondaki enrollment_preview kullanımını kaldırın.
    """
    from enrollments.models import Enrollment

    cap = _effective_capacity(section)
    used = count_active_enrollments(section.pk, exclude_enrollment_id=None)
    pct = int(round(100 * used / cap)) if cap else 0
    pct = min(100, max(0, pct))
    enr = Enrollment(
        student=student_profile,
        section=section,
        status=Enrollment.Status.ENROLLED,
    )
    blockers: list[str] = []
    for fn in (
        validate_capacity,
        validate_prerequisites,
        validate_schedule_conflict,
        validate_add_drop_for_new_enrollment,
    ):
        try:
            fn(enr)
        except ValidationError as exc:
            if getattr(exc, "messages", None):
                blockers.extend(list(exc.messages))
            else:
                blockers.append(str(exc))
    has_room = cap > 0 and used < cap
    blockers_display = [humanize_enrollment_blocker(m) for m in blockers]
    return {
        "capacity_used": used,
        "capacity_cap": cap,
        "capacity_pct": pct,
        "has_capacity": has_room,
        "blockers": blockers,
        "blockers_display": blockers_display,
        "eligible": (not blockers) and has_room,
    }


def humanize_enrollment_blocker(message: str) -> dict:
    """Önizleme metinleri — kullanıcı dilinde kısa etiket + açıklama (iş kuralı çıktısı değişmez)."""
    msg = (message or "").strip()
    lower = msg.lower()
    if "onkosul" in lower or "önkoşul" in msg:
        detail = msg.split(":", 1)[-1].strip() if ":" in msg else msg
        return {"kind": "prerequisite", "title": "Önkoşul", "detail": detail}
    if "zaman" in lower and "cakismasi" in lower:
        return {
            "kind": "conflict",
            "title": "Çakışma",
            "detail": "Bu şube, kayıtlı olduğunuz başka bir dersle aynı gün ve saatte üst üste biniyor.",
        }
    if "kapasitesi dolu" in lower or ("kapasite" in lower and "dolu" in lower):
        return {"kind": "capacity", "title": "Kontenjan", "detail": "Bu şubenin kontenjanı dolu."}
    if "kayit ekleme donemi kapali" in lower or "kayıt ekleme dönemi kapalı" in lower:
        return {
            "kind": "window",
            "title": "Ders kaydı penceresi",
            "detail": "Ders kaydı veya ders bırakma için tanımlı zaman aralığında değilsiniz.",
        }
    return {"kind": "other", "title": "Uyarı", "detail": msg}
