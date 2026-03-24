"""
Capacity race: select_for_update + transaction.atomic (MySQL CI).
SQLite dev tests skip row-level lock semantics.
"""

from __future__ import annotations

import threading
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.test import TransactionTestCase

from core.services.enrollment_atomic import enroll_student_in_section_atomic
from core.test_phase4 import Phase4FactoriesMixin
from enrollments.models import Enrollment


@skipUnless(connection.vendor == "mysql", "Row locks validated on MySQL (CI)")
class EnrollmentCapacityConcurrencyTests(Phase4FactoriesMixin, TransactionTestCase):
    def test_two_students_last_seat_only_one_enrolls(self):
        inst = self._instructor()
        c = self._course("C800", "CapRace")
        off = self._offering(c, instructor=inst, quota=1)
        sec = self._section(off)
        s1 = self._student("CR1")
        s2 = self._student("CR2")

        barrier = threading.Barrier(2)
        errors: list[tuple[int, str]] = []

        def attempt(student_pk: int) -> None:
            connection.close()
            from students.models import StudentProfile

            try:
                barrier.wait()
                with transaction.atomic():
                    sp = StudentProfile.objects.get(pk=student_pk)
                    enroll_student_in_section_atomic(sp, sec.pk)
            except Exception as exc:
                errors.append((student_pk, f"{type(exc).__name__}:{exc}"))

        t1 = threading.Thread(target=attempt, args=(s1.pk,))
        t2 = threading.Thread(target=attempt, args=(s2.pk,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        enrolled = Enrollment.objects.filter(
            section=sec,
            status__in=(Enrollment.Status.ENROLLED, Enrollment.Status.PENDING),
        ).count()
        self.assertEqual(enrolled, 1, msg=f"errors={errors}")
        self.assertEqual(len(errors), 1, msg=errors)
        self.assertIn("ValidationError", errors[0][1])

    def test_atomic_enroll_respects_capacity_single_thread(self):
        inst = self._instructor()
        c = self._course("C801", "CapSingle")
        off = self._offering(c, instructor=inst, quota=1)
        sec = self._section(off)
        s1 = self._student("CS1")
        s2 = self._student("CS2")
        enroll_student_in_section_atomic(s1, sec.pk)
        with self.assertRaises(ValidationError):
            enroll_student_in_section_atomic(s2, sec.pk)
