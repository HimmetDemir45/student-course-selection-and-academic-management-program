"""
Öğrenci profilleri ve transkript seed komutu.

seed_comprehensive + seed_real_data çalıştıktan SONRA çalıştırılmalı.

Kullanım:
    python manage.py seed_students_transcripts
    python manage.py seed_students_transcripts --yunus-username=yunus_ozkan --gurkan-username=gurkan_kaya
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from academic.models import (
    CourseSection,
    CurriculumItem,
    Department,
    Grade,
    Program,
    Semester,
    Transcript,
)
from accounts.models import User
from courses.models import Course, CourseOffering
from enrollments.models import Enrollment
from students.models import StudentProfile

# ─── Not / Puan tablosu ──────────────────────────────────────────────────────
GRADE_SCALE = [
    ("AA", Decimal("4.00")),
    ("BA", Decimal("3.50")),
    ("BB", Decimal("3.00")),
    ("CB", Decimal("2.50")),
    ("CC", Decimal("2.00")),
    ("DC", Decimal("1.50")),
    ("DD", Decimal("1.00")),
    ("FF", Decimal("0.00")),
]

GRADE_NUMERIC_MAP = {
    "AA": Decimal("95.00"),
    "BA": Decimal("87.00"),
    "BB": Decimal("80.00"),
    "CB": Decimal("73.00"),
    "CC": Decimal("65.00"),
    "DC": Decimal("57.00"),
    "DD": Decimal("52.00"),
    "FF": Decimal("30.00"),
}


def _points_to_letter(pts: Decimal) -> str:
    for letter, p in GRADE_SCALE:
        if pts >= p:
            return letter
    return "FF"


def _letter_to_points(letter: str) -> Decimal:
    for ltr, pts in GRADE_SCALE:
        if ltr == letter:
            return pts
    return Decimal("0.00")


def _assign_grades(course_credits: list, target_gpa: Decimal) -> dict:
    """
    course_credits: [(code, credits), ...]
    Hedef GPA'ya yakın harf notu dağılımı döndürür: {code: letter}
    Basit greedy yaklaşım: hepsini BB'den başlat, sonra kaydır.
    """
    total = sum(c for _, c in course_credits)
    if total == 0:
        return {}

    needed = target_gpa * total
    grades = {code: Decimal("3.00") for code, _ in course_credits}
    current = Decimal("3.00") * total
    tolerance = Decimal("0.1")

    sorted_courses = sorted(course_credits, key=lambda x: -x[1])

    if needed > current + tolerance:
        # GPA'yı artır: en büyük kredili derslerden başla
        for letter, pts in [("AA", Decimal("4.00")), ("BA", Decimal("3.50"))]:
            for code, cred in sorted_courses:
                if current >= needed - tolerance:
                    break
                if grades[code] < pts:
                    current += (pts - grades[code]) * cred
                    grades[code] = pts
            if current >= needed - tolerance:
                break
    elif needed < current - tolerance:
        # GPA'yı düşür: en büyük kredili derslerden başla
        for letter, pts in [("CC", Decimal("2.00")), ("CB", Decimal("2.50")), ("DC", Decimal("1.50")), ("DD", Decimal("1.00"))]:
            for code, cred in sorted_courses:
                if current <= needed + tolerance:
                    break
                if grades[code] > pts:
                    current += (pts - grades[code]) * cred
                    grades[code] = pts
            if current <= needed + tolerance:
                break

    return {code: _points_to_letter(pts) for code, pts in grades.items()}


def _calc_gpa(grades: dict, course_credits: list) -> Decimal:
    total_credits = sum(c for _, c in course_credits)
    if total_credits == 0:
        return Decimal("0.00")
    weighted = sum(_letter_to_points(grades.get(code, "BB")) * cred for code, cred in course_credits)
    return (weighted / total_credits).quantize(Decimal("0.01"))


def _get_or_create_semester(academic_year: str, term: str) -> Semester:
    term_enum = Semester.Term.FALL if term == "fall" else Semester.Term.SPRING
    year_start = int(academic_year[:4])

    if term == "fall":
        start_d = date(year_start, 9, 16)
        end_d = date(year_start + 1, 1, 31)
    else:
        start_d = date(year_start + 1, 2, 10)
        end_d = date(year_start + 1, 6, 30)

    sem, _ = Semester.objects.get_or_create(
        academic_year=academic_year,
        term=term_enum,
        defaults={
            "name": f"{academic_year} {'Güz' if term == 'fall' else 'Bahar'}",
            "start_date": start_d,
            "end_date": end_d,
            "is_active": False,
        },
    )
    return sem


def _get_or_create_section(course: Course, semester: Semester) -> CourseSection:
    offering, _ = CourseOffering.objects.get_or_create(
        course=course,
        semester=semester,
        section="A",
        defaults={"quota": 40, "is_active": False},
    )
    section, _ = CourseSection.objects.get_or_create(
        offering=offering,
        defaults={"max_enrollment": None},
    )
    return section


def _create_enrollment_completed(profile: StudentProfile, section: CourseSection) -> Enrollment:
    """COMPLETED enrollment oluştur — model validasyonunu bypass eder."""
    existing = Enrollment.objects.filter(student=profile, section=section).first()
    if existing:
        if existing.status != Enrollment.Status.COMPLETED:
            existing.status = Enrollment.Status.COMPLETED
            existing.instructor_approved = True
            # bypass full_clean
            super(Enrollment, existing).save(update_fields=["status", "instructor_approved"])
        return existing

    enrollment = Enrollment(
        student=profile,
        section=section,
        status=Enrollment.Status.COMPLETED,
        instructor_approved=True,
    )
    # Doğrudan model.save() çağrısını atlayarak kaydet (full_clean bypass)
    super(Enrollment, enrollment).save(force_insert=True)
    return enrollment


def _upsert_grade(enrollment: Enrollment, letter: str) -> Grade:
    grade, created = Grade.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            "letter_grade": letter,
            "numeric_grade": GRADE_NUMERIC_MAP.get(letter, Decimal("50.00")),
        },
    )
    if not created and grade.letter_grade != letter:
        grade.letter_grade = letter
        grade.numeric_grade = GRADE_NUMERIC_MAP.get(letter, Decimal("50.00"))
        grade.save(update_fields=["letter_grade", "numeric_grade"])
    return grade


# ─── ÖĞRENCİ TANIMLARI ───────────────────────────────────────────────────────

STUDENTS = [
    {
        "username": "himmet_demir",
        "first_name": "Himmet",
        "last_name": "Demir",
        "email": "himmet.demir@uni.edu.tr",
        "student_no": "457261",
        "dept_code": "YZM",
        "prog_code": "YZM-LIS",
        "class_year": 2,
        "target_gpa": Decimal("3.20"),
        "completed_semesters": [
            ("2024-2025", "fall", 1),
            ("2024-2025", "spring", 1),
        ],
        "existing_user": False,
    },
    {
        "username": None,
        "first_name": "Gürkan",
        "last_name": "Kaya",
        "email": None,
        "student_no": None,
        "dept_code": "YZM",
        "prog_code": "YZM-LIS",
        "class_year": 1,
        "target_gpa": Decimal("2.50"),
        "completed_semesters": [
            ("2024-2025", "fall", 1),
        ],
        "existing_user": True,
        "search_name": "gurkan",
        "arg_key": "gurkan",
    },
    {
        "username": None,
        "first_name": "Yunus",
        "last_name": "Özkan",
        "email": None,
        "student_no": None,
        "dept_code": "YZM",
        "prog_code": "YZM-LIS",
        "class_year": 3,
        "target_gpa": Decimal("2.70"),
        "completed_semesters": [
            ("2023-2024", "fall", 1),
            ("2023-2024", "spring", 1),
            ("2024-2025", "fall", 2),
            ("2024-2025", "spring", 2),
        ],
        "existing_user": True,
        "search_name": "yunus",
        "arg_key": "yunus",
    },
    {
        "username": "dogukan_konas",
        "first_name": "Doğukan",
        "last_name": "Konaş",
        "email": "dogukan.konas@uni.edu.tr",
        "student_no": None,
        "dept_code": "ESM",
        "prog_code": "ESM-LIS",
        "class_year": 2,
        "target_gpa": Decimal("2.20"),
        "completed_semesters": [
            ("2024-2025", "fall", 1),
            ("2024-2025", "spring", 1),
        ],
        "existing_user": False,
    },
    {
        "username": "muhammed_cagan_guven",
        "first_name": "Muhammet Çağan",
        "last_name": "Güven",
        "email": "cagan.guven@uni.edu.tr",
        "student_no": None,
        "dept_code": "OINS",
        "prog_code": "OINS-LIS",
        "class_year": 2,
        "target_gpa": Decimal("2.30"),
        "completed_semesters": [
            ("2024-2025", "fall", 1),
            ("2024-2025", "spring", 1),
        ],
        "existing_user": False,
    },
]


class Command(BaseCommand):
    help = "Öğrenci profilleri ve transkript seed"

    def add_arguments(self, parser):
        parser.add_argument("--yunus-username", default=None)
        parser.add_argument("--gurkan-username", default=None)

    @transaction.atomic
    def handle(self, *args, **options):
        yunus_username = options.get("yunus_username")
        gurkan_username = options.get("gurkan_username")

        for s_data in STUDENTS:
            name = f"{s_data['first_name']} {s_data['last_name']}"
            self.stdout.write(f"\n{'─'*50}\n{name}")

            profile = self._create_or_find_profile(s_data, yunus_username, gurkan_username)
            if profile is None:
                continue

            self._build_transcripts(profile, s_data)

        self.stdout.write(self.style.SUCCESS("\n[OK] seed_students_transcripts tamamlandı!\n"))

    def _create_or_find_profile(self, s_data, yunus_username, gurkan_username):
        dept = Department.objects.filter(code=s_data["dept_code"]).first()
        prog = Program.objects.filter(code=s_data["prog_code"]).first()
        if not dept or not prog:
            self.stdout.write(self.style.ERROR(f"  Dept/Program yok: {s_data['dept_code']}"))
            return None

        if s_data["existing_user"]:
            arg_key = s_data.get("arg_key", "")
            override_username = gurkan_username if arg_key == "gurkan" else yunus_username if arg_key == "yunus" else None
            search = s_data.get("search_name", "").lower()

            user = None
            if override_username:
                user = User.objects.filter(username=override_username).first()
            if not user:
                user = (
                    User.objects.filter(username__icontains=search).first()
                    or User.objects.filter(first_name__icontains=s_data["first_name"]).first()
                    or User.objects.filter(last_name__icontains=s_data["last_name"]).first()
                )
            if not user:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [!] Kullanıcı bulunamadı. "
                        f"--{arg_key}-username=<username> argümanı ekleyin."
                    )
                )
                return None
            self.stdout.write(f"  Mevcut kullanıcı: {user.username}")
        else:
            user, created = User.objects.get_or_create(
                username=s_data["username"],
                defaults={
                    "first_name": s_data["first_name"],
                    "last_name": s_data["last_name"],
                    "email": s_data["email"] or f"{s_data['username']}@uni.edu.tr",
                    "role": User.Role.STUDENT,
                },
            )
            if created:
                user.set_password("DemoPass2026!")
                user.save()
            self.stdout.write(f"  Kullanıcı: {user.username} ({'yeni' if created else 'mevcut'})")

        # StudentProfile
        student_no = s_data.get("student_no") or f"STU{user.pk:06d}"
        profile, p_created = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                "student_no": student_no,
                "department": dept,
                "program": prog,
                "enrollment_year": s_data["class_year"],
                "is_approved": True,
            },
        )
        if not p_created:
            profile.department = dept
            profile.program = prog
            profile.enrollment_year = s_data["class_year"]
            profile.is_approved = True
            profile.save(update_fields=["department", "program", "enrollment_year", "is_approved"])

        self.stdout.write(f"  Profil: {profile.student_no} ({'yeni' if p_created else 'güncellendi'})")
        return profile

    def _build_transcripts(self, profile: StudentProfile, s_data: dict):
        prog = profile.program
        target_gpa = s_data["target_gpa"]

        cum_credits = 0
        cum_weighted = Decimal("0.00")

        for acad_year, term, year_level in s_data["completed_semesters"]:
            semester = _get_or_create_semester(acad_year, term)

            items = list(
                CurriculumItem.objects.filter(
                    program=prog,
                    year_level=year_level,
                    term=term,
                ).select_related("course")
            )

            if not items:
                self.stdout.write(self.style.WARNING(
                    f"  [!] Curriculum boş: {acad_year} {term} yıl={year_level}"
                ))
                continue

            course_credits = [(ci.course.code, ci.course.credits) for ci in items]
            grades_map = _assign_grades(course_credits, target_gpa)

            pairs = []
            for ci in items:
                letter = grades_map.get(ci.course.code, "BB")
                section = _get_or_create_section(ci.course, semester)
                enrollment = _create_enrollment_completed(profile, section)
                grade = _upsert_grade(enrollment, letter)
                pairs.append((enrollment, grade))
                self.stdout.write(f"    {ci.course.code} ({ci.course.credits} AKTS) → {letter}")

            # Transkript
            total_cred = sum(c for _, c in course_credits)
            sem_gpa = _calc_gpa(grades_map, course_credits)

            Transcript.objects.update_or_create(
                student=profile,
                semester=semester,
                defaults={"gpa": sem_gpa, "total_credits": total_cred},
            )

            cum_credits += total_cred
            cum_weighted += sem_gpa * total_cred
            self.stdout.write(f"  Dönem GPA ({semester.name}): {sem_gpa} | {total_cred} AKTS")

        if cum_credits > 0:
            cum_gpa = (cum_weighted / cum_credits).quantize(Decimal("0.01"))
            self.stdout.write(self.style.SUCCESS(f"  → Kümülatif GPA: {cum_gpa} / {cum_credits} AKTS"))
