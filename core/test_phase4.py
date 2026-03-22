from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from academic.models import (
    CourseSection,
    Department,
    Program,
    SectionTimeSlot,
    Semester,
)
from accounts.models import User
from audit_logs.models import AuditLog
from core.services.enrollment_rules import is_within_add_drop
from core.services.enrollment_workflow import (
    can_transition,
    transition_enrollment_status,
)
from core.services.gpa import compute_weighted_gpa, gpa_from_completed_enrollments
from courses.models import Course, CourseOffering, CoursePrerequisite
from enrollments.models import Enrollment
from instructors.models import InstructorProfile
from students.models import StudentProfile

UserModel = get_user_model()


class Phase4FactoriesMixin:
    def setUp(self):
        cache.clear()
        self.today = timezone.localdate()
        self.department = Department.objects.create(name="Muhendislik", code="MUH")
        self.program = Program.objects.create(
            department=self.department,
            name="BLM",
            code="BLM",
        )
        self.semester = Semester.objects.create(
            name="2025-2026 Guz",
            academic_year="2025-2026",
            term=Semester.Term.FALL,
            start_date=self.today - timedelta(days=30),
            end_date=self.today + timedelta(days=120),
            add_drop_start=self.today - timedelta(days=1),
            add_drop_end=self.today + timedelta(days=14),
        )

    def _user(self, username, role, **extra):
        return UserModel.objects.create_user(
            username=username,
            email=f"{username}@test.edu",
            password="pass12345",
            role=role,
            **extra,
        )

    def _student(self, no="S001"):
        u = self._user(f"stu_{no}", User.Role.STUDENT)
        return StudentProfile.objects.create(
            user=u,
            student_no=no,
            department=self.department,
            program=self.program,
        )

    def _instructor(self, no="I001"):
        u = self._user(f"ins_{no}", User.Role.INSTRUCTOR)
        return InstructorProfile.objects.create(
            user=u,
            employee_no=no,
            department=self.department,
        )

    def _course(self, code, name, credits=3):
        return Course.objects.create(
            department=self.department,
            code=code,
            name=name,
            credits=credits,
        )

    def _offering(self, course, instructor=None, section="A", quota=30):
        return CourseOffering.objects.create(
            course=course,
            semester=self.semester,
            instructor=instructor,
            section=section,
            quota=quota,
        )

    def _section(self, offering):
        return CourseSection.objects.get(offering=offering)


class CapacityTests(Phase4FactoriesMixin, TestCase):
    def test_capacity_validation_blocks_full_section(self):
        inst = self._instructor()
        c = self._course("CS100", "Intro")
        off = self._offering(c, instructor=inst, quota=1)
        sec = self._section(off)
        s1 = self._student("S1")
        s2 = self._student("S2")
        Enrollment.objects.create(student=s1, section=sec, status=Enrollment.Status.ENROLLED)
        with self.assertRaises(ValidationError):
            Enrollment(
                student=s2, section=sec, status=Enrollment.Status.ENROLLED
            ).save()


class PrerequisiteTests(Phase4FactoriesMixin, TestCase):
    def test_prerequisite_validation_missing_course(self):
        inst = self._instructor()
        c1 = self._course("MATH100", "Calc")
        c2 = self._course("MATH200", "Calc2")
        CoursePrerequisite.objects.create(course=c2, prerequisite=c1)
        off2 = self._offering(c2, instructor=inst)
        sec2 = self._section(off2)
        st = self._student()
        with self.assertRaises(ValidationError):
            Enrollment(
                student=st, section=sec2, status=Enrollment.Status.ENROLLED
            ).save()


class ScheduleTests(Phase4FactoriesMixin, TestCase):
    def test_schedule_conflict_detection(self):
        inst = self._instructor()
        c1 = self._course("CS101", "A")
        c2 = self._course("CS102", "B")
        o1 = self._offering(c1, instructor=inst, section="A")
        o2 = self._offering(c2, instructor=inst, section="B")
        s1 = self._section(o1)
        s2 = self._section(o2)
        SectionTimeSlot.objects.create(
            section=s1,
            weekday=SectionTimeSlot.Weekday.MONDAY,
            start_time="10:00",
            end_time="11:00",
        )
        SectionTimeSlot.objects.create(
            section=s2,
            weekday=SectionTimeSlot.Weekday.MONDAY,
            start_time="10:30",
            end_time="11:30",
        )
        st = self._student()
        Enrollment.objects.create(student=st, section=s1, status=Enrollment.Status.ENROLLED)
        e2 = Enrollment(student=st, section=s2, status=Enrollment.Status.ENROLLED)
        with self.assertRaises(ValidationError):
            e2.save()


class AddDropWindowTests(Phase4FactoriesMixin, TestCase):
    def test_add_drop_window_enforced(self):
        sem = self.semester
        sem.add_drop_start = self.today - timedelta(days=20)
        sem.add_drop_end = self.today - timedelta(days=5)
        sem.save()
        self.assertFalse(is_within_add_drop(sem, self.today))
        inst = self._instructor()
        c = self._course("X101", "X")
        off = self._offering(c, instructor=inst)
        sec = self._section(off)
        st = self._student()
        with self.assertRaises(ValidationError):
            Enrollment(
                student=st, section=sec, status=Enrollment.Status.ENROLLED
            ).save()


class WorkflowAuditTests(Phase4FactoriesMixin, TestCase):
    def test_enrollment_status_transitions_and_audit(self):
        inst = self._instructor()
        c = self._course("Z101", "Z")
        off = self._offering(c, instructor=inst, quota=5)
        sec = self._section(off)
        st = self._student()
        admin = self._user("adm1", User.Role.ADMIN, is_staff=True)
        e = Enrollment.objects.create(
            student=st, section=sec, status=Enrollment.Status.ENROLLED
        )
        before = AuditLog.objects.count()
        self.assertTrue(can_transition(e.status, Enrollment.Status.DROPPED))
        transition_enrollment_status(
            e,
            Enrollment.Status.DROPPED,
            actor=admin,
            request=None,
        )
        e.refresh_from_db()
        self.assertEqual(e.status, Enrollment.Status.DROPPED)
        self.assertGreater(AuditLog.objects.count(), before)


class InstructorGradeTests(Phase4FactoriesMixin, TestCase):
    def test_instructor_grade_entry_permission(self):
        i1 = self._instructor("I1")
        i2 = self._instructor("I2")
        c = self._course("G101", "G")
        off = self._offering(c, instructor=i1)
        sec = self._section(off)
        st = self._student()
        e = Enrollment.objects.create(
            student=st, section=sec, status=Enrollment.Status.ENROLLED
        )
        client = Client()
        client.force_login(i2.user)
        url = reverse("academic:grade_entry", kwargs={"enrollment_id": e.pk})
        r = client.get(url)
        self.assertEqual(r.status_code, 403)


class GpaTests(Phase4FactoriesMixin, TestCase):
    def test_gpa_calculation_accuracy_and_empty_records(self):
        gpa, cred = compute_weighted_gpa([])
        self.assertEqual(gpa, Decimal("0.00"))
        self.assertEqual(cred, 0)

        inst = self._instructor()
        ca = self._course("GA", "A", credits=3)
        cb = self._course("GB", "B", credits=3)
        oa = self._offering(ca, instructor=inst)
        ob = self._offering(cb, instructor=inst, section="B")
        sa = self._section(oa)
        sb = self._section(ob)
        st = self._student()
        ea = Enrollment.objects.create(
            student=st, section=sa, status=Enrollment.Status.COMPLETED
        )
        eb = Enrollment.objects.create(
            student=st, section=sb, status=Enrollment.Status.COMPLETED
        )
        from academic.models import Grade

        Grade.objects.create(enrollment=ea, letter_grade="A")
        Grade.objects.create(enrollment=eb, letter_grade="B")
        qs = Enrollment.objects.filter(student=st).select_related(
            "section__offering__course", "academic_grade"
        )
        gpa, total_c = gpa_from_completed_enrollments(qs)
        self.assertEqual(total_c, 6)
        self.assertEqual(gpa, Decimal("3.50"))


class RoleAccessTests(Phase4FactoriesMixin, TestCase):
    def test_role_based_access_controls_per_endpoint(self):
        st = self._student()
        client = Client()
        client.force_login(st.user)
        url = reverse("academic:instructor_enrollments")
        r = client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith("/"))


@override_settings(
    LOGIN_THROTTLE_MAX_FAILURES=3,
    LOGIN_THROTTLE_LOCKOUT_SECONDS=300,
)
class BruteforceTests(TestCase):
    def test_bruteforce_throttling_on_login(self):
        from accounts.login_throttle import (
            is_login_locked,
            register_login_failure,
        )

        cache.clear()
        rf = RequestFactory()
        req = rf.post("/accounts/login/", {"login": "victim", "password": "x"})
        req.META["REMOTE_ADDR"] = "203.0.113.9"
        self.assertFalse(is_login_locked(req, "victim"))
        for _ in range(3):
            register_login_failure(req, "victim")
        self.assertTrue(is_login_locked(req, "victim"))
