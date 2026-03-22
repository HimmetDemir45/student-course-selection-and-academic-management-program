from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db.models import QuerySet

from enrollments.models import Enrollment

LETTER_POINTS: dict[str, Decimal] = {
    "A": Decimal("4.0"),
    "B": Decimal("3.0"),
    "C": Decimal("2.0"),
    "D": Decimal("1.0"),
    "F": Decimal("0.0"),
}


def letter_grade_to_points(letter: str) -> Decimal | None:
    if not letter:
        return None
    key = letter.strip().upper()[:1]
    return LETTER_POINTS.get(key)


def compute_weighted_gpa(
    rows: Iterable[tuple[Decimal, int]],
) -> tuple[Decimal, int]:
    """
    rows: (grade_points, credit_hours) for completed courses with valid grades.
    Returns (gpa, total_credits_used) — empty input -> (Decimal('0'), 0).
    """
    total_points = Decimal("0")
    total_credits = 0
    for points, credits in rows:
        if credits <= 0:
            continue
        total_points += points * credits
        total_credits += credits
    if total_credits == 0:
        return Decimal("0.00"), 0
    gpa = (total_points / Decimal(total_credits)).quantize(Decimal("0.01"))
    return gpa, total_credits


def gpa_from_completed_enrollments(qs: QuerySet) -> tuple[Decimal, int]:
    """
    qs: Enrollment queryset with select_related('section__offering__course', 'academic_grade').
    Only COMPLETED with a resolvable letter grade count toward GPA.
    """
    rows: list[tuple[Decimal, int]] = []
    for enr in qs:
        if enr.status != Enrollment.Status.COMPLETED:
            continue
        grade = getattr(enr, "academic_grade", None)
        if grade is None:
            continue
        pts = letter_grade_to_points(grade.letter_grade or "")
        if pts is None and grade.numeric_grade is not None:
            # Map numeric 0–100 roughly to 4.0 scale (simple linear cap)
            n = min(max(grade.numeric_grade, Decimal("0")), Decimal("100"))
            pts = (n / Decimal("25")).quantize(Decimal("0.01"))
            if pts > Decimal("4.0"):
                pts = Decimal("4.0")
        if pts is None:
            continue
        credits = int(enr.section.offering.course.credits)
        rows.append((pts, credits))
    return compute_weighted_gpa(rows)
