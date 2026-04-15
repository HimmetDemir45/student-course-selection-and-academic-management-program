"""
Phase 6: security (CSRF), RBAC boundaries, enrollment HTTP flows, transcript/GPA.
Brute-force unit coverage remains in core.test_phase4.BruteforceTests.
"""

from decimal import Decimal

from django.http import HttpResponseForbidden
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from academic.models import SectionTimeSlot
from accounts.models import User
from core.test_phase4 import Phase4FactoriesMixin
from courses.models import CoursePrerequisite
from enrollments.models import Enrollment

# Template render instrumentation can break on some Python preview builds; keep tests lean.
_DEBUG_OFF = {"DEBUG": False}


def _csrf_failure_plain(request, reason=""):
    return HttpResponseForbidden("CSRF validation failed")


@override_settings(**_DEBUG_OFF, CSRF_FAILURE_VIEW=_csrf_failure_plain)
class CsrfAndLoginSecurityTests(TestCase):
    def test_login_post_without_csrf_token_is_forbidden_when_enforced(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("accounts:login"),
            {"login": "x", "password": "y"},
        )
        self.assertEqual(response.status_code, 403)


@override_settings(**_DEBUG_OFF)
class RbacBoundaryTests(Phase4FactoriesMixin, TestCase):
    def test_admin_redirected_from_student_only_test_page(self):
        admin_user = self._user("rbac_admin", User.Role.ADMIN, is_staff=True)
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse("core:student_test"))
        self.assertEqual(response.status_code, 302)

    def test_student_dashboard_is_accessible_without_admin_audit_nav(self):
        """Phase 14: öğrenci panosuna erişir; denetim URL'si sayfada yok."""
        st = self._student("RBAC1")
        client = Client()
        client.force_login(st.user)
        response = client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("/audit-logs/", response.content.decode("utf-8"))

    def test_instructor_reaches_instructor_test_endpoint(self):
        ins = self._instructor("RBACI")
        client = Client()
        client.force_login(ins.user)
        response = client.get(reverse("core:instructor_test"))
        self.assertEqual(response.status_code, 200)


@override_settings(**_DEBUG_OFF)
class EnrollmentHttpEdgeTests(Phase4FactoriesMixin, TestCase):
    def test_enroll_post_rejected_when_prerequisite_missing(self):
        inst = self._instructor()
        c1 = self._course("P610", "Prereq")
        c2 = self._course("P620", "Advanced")
        CoursePrerequisite.objects.create(course=c2, prerequisite=c1)
        off = self._offering(c2, instructor=inst)
        sec = self._section(off)
        st = self._student("P6S1")

        client = Client()
        client.force_login(st.user)
        before = Enrollment.objects.filter(student=st).count()
        client.post(reverse("enrollments:enroll"), {"section_id": sec.pk})
        self.assertEqual(Enrollment.objects.filter(student=st).count(), before)

    def test_enroll_post_rejected_on_schedule_conflict(self):
        inst = self._instructor()
        c1 = self._course("S610", "A")
        c2 = self._course("S620", "B")
        o1 = self._offering(c1, instructor=inst, section="A")
        o2 = self._offering(c2, instructor=inst, section="B")
        s1 = self._section(o1)
        s2 = self._section(o2)
        SectionTimeSlot.objects.create(
            section=s1,
            weekday=SectionTimeSlot.Weekday.TUESDAY,
            start_time="09:00",
            end_time="10:00",
        )
        SectionTimeSlot.objects.create(
            section=s2,
            weekday=SectionTimeSlot.Weekday.TUESDAY,
            start_time="09:30",
            end_time="10:30",
        )
        st = self._student("P6S2")
        Enrollment.objects.create(student=st, section=s1, status=Enrollment.Status.ENROLLED)

        client = Client()
        client.force_login(st.user)
        before = Enrollment.objects.filter(student=st).count()
        client.post(reverse("enrollments:enroll"), {"section_id": s2.pk})
        self.assertEqual(Enrollment.objects.filter(student=st).count(), before)

    def test_enroll_post_rejected_when_section_full(self):
        inst = self._instructor()
        c = self._course("C610", "Full")
        off = self._offering(c, instructor=inst, quota=1)
        sec = self._section(off)
        st_taken = self._student("P6FULLA")
        st_try = self._student("P6FULLB")
        Enrollment.objects.create(student=st_taken, section=sec, status=Enrollment.Status.ENROLLED)

        client = Client()
        client.force_login(st_try.user)
        before = Enrollment.objects.filter(student=st_try).count()
        client.post(reverse("enrollments:enroll"), {"section_id": sec.pk})
        self.assertEqual(Enrollment.objects.filter(student=st_try).count(), before)


@override_settings(**_DEBUG_OFF)
class TranscriptPageTests(Phase4FactoriesMixin, TestCase):
    def test_transcript_view_computes_gpa_in_context(self):
        from academic.models import Grade

        inst = self._instructor()
        ca = self._course("TR610", "TrA", credits=3)
        oa = self._offering(ca, instructor=inst)
        sa = self._section(oa)
        st = self._student("TRST1")
        en = Enrollment.objects.create(
            student=st, section=sa, status=Enrollment.Status.COMPLETED
        )
        Grade.objects.create(enrollment=en, letter_grade="A")

        from students.views import TranscriptView

        request = RequestFactory().get(reverse("students:transcript"))
        request.user = st.user
        view = TranscriptView()
        view.setup(request)
        ctx = view.get_context_data()
        self.assertEqual(ctx["gpa"], Decimal("4.00"))
        self.assertEqual(ctx["gpa_credits"], 3)
