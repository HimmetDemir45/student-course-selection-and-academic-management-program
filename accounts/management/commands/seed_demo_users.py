"""
Demo kullanıcı seed komutu.

Kurulum sonrası ya da geliştirme ortamında "tam dolu" bir akademik manzara
göstermek için tek komutla:
  * 1 örnek öğrenci (GPA'lı, geçmiş transcripts)
  * 1 örnek eğitim görevlisi (offering atanmış)
  * Gerekli bölüm/program/dönem/ders altyapısı
  * Aktif dönem için kayıt + nota işlenmiş enrollment

oluşturur. İdempotent: tekrar çalıştırılırsa mevcutları günceller, çoğaltmaz.

Kullanım:
    python manage.py seed_demo_users
    python manage.py seed_demo_users --reset   # önce demo kullanıcıları siler
"""

from __future__ import annotations

from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from academic.models import (
    CourseSection,
    Department,
    Grade,
    Program,
    SectionTimeSlot,
    Semester,
    Transcript,
)
from courses.models import Course, CourseOffering
from enrollments.models import Enrollment
from instructors.models import InstructorProfile
from students.models import StudentProfile


DEMO_STUDENT_USERNAME = "demo_ogrenci"
DEMO_INSTRUCTOR_USERNAME = "demo_akademisyen"

# Sabit parolalar yalnızca demo amaçlıdır — prod'da bu komut çalıştırılmamalı.
DEMO_PASSWORD = "Demo-Akademik-2026!"


class Command(BaseCommand):
    help = "GPA'li örnek öğrenci ve örnek eğitim görevlisi (ve gerekli akademik altyapı) oluşturur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Var olan demo kullanıcıları silip yeniden oluştur.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts.get("reset"):
            User.objects.filter(
                username__in=[DEMO_STUDENT_USERNAME, DEMO_INSTRUCTOR_USERNAME]
            ).delete()
            self.stdout.write(self.style.WARNING("Demo kullanıcılar silindi."))

        dept = self._ensure_department()
        program = self._ensure_program(dept)
        current_sem, prev_sem_1, prev_sem_2 = self._ensure_semesters()
        instructor_user, instructor_profile = self._ensure_instructor(dept)
        student_user, student_profile = self._ensure_student(dept, program, instructor_profile)

        courses = self._ensure_courses(dept, program)
        offering = self._ensure_offering(courses[0], current_sem, instructor_profile)
        self._ensure_enrollment_with_grade(student_profile, offering)

        # Geçmiş GPA verisi
        self._ensure_transcript(student_profile, prev_sem_1, gpa=Decimal("3.42"), credits=21)
        self._ensure_transcript(student_profile, prev_sem_2, gpa=Decimal("3.58"), credits=24)

        self.stdout.write(self.style.SUCCESS("\nDemo veri hazır."))
        self.stdout.write(self.style.SUCCESS(f"  Öğrenci      : {student_user.username}  (parola: {DEMO_PASSWORD})"))
        self.stdout.write(self.style.SUCCESS(f"  Eğitim grv.  : {instructor_user.username}  (parola: {DEMO_PASSWORD})"))
        self.stdout.write(self.style.SUCCESS(f"  Genel GPA    : 3.50 üzeri (iki dönem transcripts + aktif dönem AA)"))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ensure_department(self) -> Department:
        dept, _ = Department.objects.get_or_create(
            code="BIL",
            defaults={"name": "Bilgisayar Mühendisliği", "description": "Demo bölüm"},
        )
        return dept

    def _ensure_program(self, dept: Department) -> Program:
        prog, _ = Program.objects.get_or_create(
            code="BIL-LIS",
            defaults={
                "department": dept,
                "name": "Bilgisayar Müh. Lisans",
                "degree_level": Program.DegreeLevel.UNDERGRAD,
            },
        )
        return prog

    def _ensure_semesters(self) -> tuple[Semester, Semester, Semester]:
        today = timezone.localdate()
        # Aktif dönem: add/drop penceresi açık
        current = self._ensure_semester(
            academic_year="2025-2026",
            term=Semester.Term.SPRING,
            start=today - timedelta(days=30),
            end=today + timedelta(days=90),
            add_drop_start=today - timedelta(days=14),
            add_drop_end=today + timedelta(days=14),
        )
        prev_1 = self._ensure_semester(
            academic_year="2025-2026",
            term=Semester.Term.FALL,
            start=today - timedelta(days=210),
            end=today - timedelta(days=60),
        )
        prev_2 = self._ensure_semester(
            academic_year="2024-2025",
            term=Semester.Term.SPRING,
            start=today - timedelta(days=420),
            end=today - timedelta(days=240),
        )
        return current, prev_1, prev_2

    def _ensure_semester(self, *, academic_year, term, start, end,
                         add_drop_start=None, add_drop_end=None) -> Semester:
        sem, created = Semester.objects.get_or_create(
            academic_year=academic_year,
            term=term,
            defaults={
                "name": f"{academic_year} {term.capitalize()}",
                "start_date": start,
                "end_date": end,
                "add_drop_start": add_drop_start,
                "add_drop_end": add_drop_end,
            },
        )
        # Add/drop pencerelerini güncel tut (idempotent)
        if not created:
            sem.start_date = start
            sem.end_date = end
            sem.add_drop_start = add_drop_start
            sem.add_drop_end = add_drop_end
            sem.save(update_fields=["start_date", "end_date", "add_drop_start", "add_drop_end"])
        return sem

    def _ensure_instructor(self, dept: Department):
        # accounts.signals: User post_save → InstructorProfile auto-create.
        user, created = User.objects.get_or_create(
            username=DEMO_INSTRUCTOR_USERNAME,
            defaults={
                "email": "demo.akademisyen@uni.test",
                "first_name": "Prof. Dr. Mehmet",
                "last_name": "Aydın",
                "role": User.Role.INSTRUCTOR,
            },
        )
        if created or not user.has_usable_password():
            user.set_password(DEMO_PASSWORD)
            user.save()

        # Sinyal zaten profil yarattı; biz onu zenginleştiriyoruz.
        profile = InstructorProfile.objects.filter(user=user).first()
        if profile is None:
            profile = InstructorProfile.objects.create(
                user=user,
                employee_no="AKD-2026-0001",
                department=dept,
                title="Doçent",
            )
        else:
            profile.employee_no = "AKD-2026-0001"
            profile.department = dept
            profile.title = "Doçent"
            profile.save(update_fields=["employee_no", "department", "title"])
        return user, profile

    def _ensure_student(self, dept: Department, program: Program, advisor: InstructorProfile):
        # accounts.signals: User post_save → StudentProfile auto-create (rasgele student_no ile).
        user, created = User.objects.get_or_create(
            username=DEMO_STUDENT_USERNAME,
            defaults={
                "email": "demo.ogrenci@uni.test",
                "first_name": "Ayşe",
                "last_name": "Yıldız",
                "role": User.Role.STUDENT,
            },
        )
        if created or not user.has_usable_password():
            user.set_password(DEMO_PASSWORD)
            user.save()

        profile = StudentProfile.objects.filter(user=user).first()
        if profile is None:
            profile = StudentProfile.objects.create(
                user=user,
                student_no="20260042",
                department=dept,
                program=program,
                advisor=advisor,
                enrollment_year=2024,
            )
        else:
            profile.student_no = "20260042"
            profile.department = dept
            profile.program = program
            profile.advisor = advisor
            profile.enrollment_year = 2024
            profile.save(update_fields=[
                "student_no", "department", "program", "advisor", "enrollment_year",
            ])
        return user, profile

    def _ensure_courses(self, dept: Department, program: Program) -> list[Course]:
        seeds = [
            ("BIL301", "Algoritmalar ve Veri Yapıları", 4),
            ("BIL202", "Veri Tabanı Sistemleri", 3),
            ("BIL310", "İşletim Sistemleri", 4),
        ]
        result = []
        for code, name, credits in seeds:
            obj, _ = Course.objects.get_or_create(
                code=code,
                defaults={
                    "department": dept,
                    "program": program,
                    "name": name,
                    "credits": credits,
                    "description": f"Demo amaçlı {name} dersi.",
                },
            )
            result.append(obj)
        return result

    def _ensure_offering(self, course: Course, sem: Semester, instructor: InstructorProfile) -> CourseOffering:
        offering, _ = CourseOffering.objects.get_or_create(
            course=course,
            semester=sem,
            section="A",
            defaults={"instructor": instructor, "quota": 30},
        )
        if offering.instructor_id is None:
            offering.instructor = instructor
            offering.save(update_fields=["instructor"])

        section, _ = CourseSection.objects.get_or_create(
            offering=offering,
            defaults={"max_enrollment": 30},
        )
        SectionTimeSlot.objects.get_or_create(
            section=section,
            weekday=SectionTimeSlot.Weekday.TUESDAY,
            start_time=time(10, 0),
            end_time=time(11, 50),
        )
        return offering

    def _ensure_enrollment_with_grade(self, student: StudentProfile, offering: CourseOffering) -> None:
        section = offering.section_detail
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            section=section,
            defaults={"status": Enrollment.Status.ENROLLED},
        )
        # Not bilgisi: AA (4.00 üzerinden 90)
        Grade.objects.update_or_create(
            enrollment=enrollment,
            defaults={"letter_grade": "AA", "numeric_grade": Decimal("92.50")},
        )

    def _ensure_transcript(self, student: StudentProfile, sem: Semester, *, gpa: Decimal, credits: int) -> None:
        Transcript.objects.update_or_create(
            student=student,
            semester=sem,
            defaults={"gpa": gpa, "total_credits": credits},
        )
