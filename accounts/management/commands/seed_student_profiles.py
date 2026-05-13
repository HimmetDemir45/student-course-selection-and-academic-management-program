"""
Öğrenci profilleri ve transkript seed komutu.

5 farklı öğrenci oluştur, her biri:
- Farklı bölüm/program (YZM, ESM, OINS)
- Farklı sınıf seviyesi (1., 2., 3. yıl)
- Belirli GPA değeri ile geçmiş dönem transkriptleri
- Danışman atanmış

Kullanım:
    python manage.py seed_student_profiles
    python manage.py seed_student_profiles --reset   # önce siler
"""

from __future__ import annotations

import os
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from academic.models import (
    CurriculumItem,
    Department,
    Grade,
    Program,
    Semester,
)
from courses.models import Course, CourseOffering
from enrollments.models import Enrollment
from instructors.models import InstructorProfile
from students.models import StudentProfile


# Öğrenci verileri: (ad, soyad, kullanıcı_adı, bölüm_code, program_code, yıl, hedef_gpa, student_no)
STUDENTS_DATA = [
    ("Himmet", "Demir", "himmet_demir", "YZM", "YZM-LIS", 2, Decimal("3.2"), "457261"),
    ("Gürkan", "Kaya", "gurkan_kaya", "YZM", "YZM-LIS", 1, Decimal("2.5"), "457262"),
    ("Yunus", "Özkan", "yunus_ozkan", "YZM", "YZM-LIS", 3, Decimal("2.7"), "457263"),
    ("Doğukan", "Konaş", "dogukan_konas", "ESM", "ESM-LIS", 2, Decimal("2.2"), "457264"),
    ("Muhammet Çağan", "Güven", "muhammet_guven", "OINS", "OINS-LIS", 2, Decimal("2.3"), "457265"),
]

# Not skalası (Türk sistemi)
GRADE_SCALE = {
    "AA": Decimal("4.0"),
    "BA": Decimal("3.5"),
    "BB": Decimal("3.0"),
    "CB": Decimal("2.5"),
    "CC": Decimal("2.0"),
    "DC": Decimal("1.5"),
    "DD": Decimal("1.0"),
    "FF": Decimal("0.0"),
}

GRADE_LETTERS = ["AA", "BA", "BB", "CB", "CC", "DC", "DD", "FF"]


def _make_grade_map(target_gpa: Decimal, curriculum_items: list) -> dict:
    """
    Hedef GPA'ya ulaşmak için ders notlarını dağıt.
    İki bitişik not arasında kredi ağırlığına göre dağıtır.
    """
    if not curriculum_items:
        return {}

    # En yakın iki notu bul
    gpa_values = sorted(GRADE_SCALE.values(), reverse=True)
    upper_idx = 0
    for i, g in enumerate(gpa_values):
        if g <= target_gpa:
            upper_idx = i
            break

    upper_gpa = gpa_values[upper_idx] if upper_idx < len(gpa_values) else gpa_values[-1]
    lower_gpa = gpa_values[upper_idx + 1] if upper_idx + 1 < len(gpa_values) else gpa_values[-1]

    # İki nota karşılık gelen harf notları
    upper_letter = [k for k, v in GRADE_SCALE.items() if v == upper_gpa][0]
    lower_letter = [k for k, v in GRADE_SCALE.items() if v == lower_gpa][0]

    # Kredi dağılımı hesapla
    total_credits = sum(item.course.credits or 0 for item in curriculum_items)
    if total_credits == 0:
        return {item.pk: upper_letter for item in curriculum_items}

    # Hedef GPA'ya ulaşmak için gereken ratio
    if upper_gpa == lower_gpa:
        ratio = Decimal("1.0")
    else:
        ratio = (target_gpa - lower_gpa) / (upper_gpa - lower_gpa)
        ratio = max(Decimal("0"), min(Decimal("1"), ratio))

    upper_credits = int(ratio * total_credits)
    lower_credits = total_credits - upper_credits

    # Her derse not ata
    grade_map = {}
    current_upper = 0
    for item in curriculum_items:
        credits = item.course.credits or 0
        if current_upper < upper_credits:
            if current_upper + credits <= upper_credits:
                grade_map[item.pk] = upper_letter
                current_upper += credits
            else:
                grade_map[item.pk] = lower_letter
        else:
            grade_map[item.pk] = lower_letter

    return grade_map


def create_or_update_student(first_name: str, last_name: str, username: str,
                             dept_code: str, prog_code: str, year: int,
                             target_gpa: Decimal, student_no: str) -> StudentProfile:
    """Öğrenci profili oluştur veya güncelle."""

    # Kullanıcı oluştur
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{username}@akademik.local",
            "role": User.Role.STUDENT,
            "is_active": True,
        }
    )

    # Departman ve program bul
    try:
        department = Department.objects.get(code=dept_code)
    except Department.DoesNotExist:
        print(f"[!] Bolum {dept_code} bulunmadi")
        return None

    try:
        program = Program.objects.get(code=prog_code)
    except Program.DoesNotExist:
        print(f"[!] Program {prog_code} bulunmadi")
        return None

    # Danışman bul (seed_demo_users'dan demo akademisyen)
    try:
        advisor = InstructorProfile.objects.get(user__username="demo_akademisyen")
    except InstructorProfile.DoesNotExist:
        advisor = None

    # Öğrenci profili oluştur/güncelle
    profile, created = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            "student_no": student_no,
            "department": department,
            "program": program,
            "enrollment_year": 2026 - year + 1,
            "advisor": advisor,
            "is_approved": True,
        }
    )

    if not created:
        profile.department = department
        profile.program = program
        profile.enrollment_year = 2026 - year + 1
        profile.advisor = advisor
        profile.save()

    print(f"{'OK' if created else 'UPD'} {first_name} {last_name} ({username}) - {program.code} Yil {year}, GPA {target_gpa}")

    return profile


@transaction.atomic
def seed_enrollments_for_student(profile: StudentProfile, year: int, target_gpa: Decimal) -> None:
    """Öğrenci için geçmiş dönemed enrollments ve notları oluştur."""

    if not profile or not profile.program:
        return

    # Geçmiş dönemleri bul
    past_semesters = [
        ("2023-2024", "fall"),
        ("2023-2024", "spring"),
        ("2024-2025", "fall"),
    ]

    for acad_year, term in past_semesters:
        try:
            semester = Semester.objects.get(academic_year=acad_year, term=term)
        except Semester.DoesNotExist:
            continue

        # Bu dönem ve yıl için müfredat derslerini bul
        curriculum_items = list(
            CurriculumItem.objects.filter(
                program=profile.program,
                year_level=year,
                term=term,
            ).select_related("course")
        )

        if not curriculum_items:
            continue

        # Not dağılımını hesapla
        grade_map = _make_grade_map(target_gpa, curriculum_items)

        # Her dersin offering'ini bul ve enrollment oluştur
        for item in curriculum_items:
            try:
                offering = CourseOffering.objects.get(
                    course=item.course,
                    semester=semester,
                    is_active=True,
                )
            except CourseOffering.DoesNotExist:
                continue

            section = offering.section_detail

            # Enrollment oluştur (COMPLETED status ile)
            enrollment, created = Enrollment.objects.get_or_create(
                student=profile,
                section=section,
                defaults={"status": Enrollment.Status.COMPLETED},
            )

            # Not ata
            if item.pk in grade_map:
                letter_grade = grade_map[item.pk]
                Grade.objects.update_or_create(
                    enrollment=enrollment,
                    defaults={
                        "letter_grade": letter_grade,
                        "numeric_grade": Decimal(str(GRADE_SCALE[letter_grade])),
                    }
                )

            # Enrollment status'ü COMPLETED yap
            if enrollment.status != Enrollment.Status.COMPLETED:
                enrollment.status = Enrollment.Status.COMPLETED
                enrollment.save(update_fields=["status"])


class Command(BaseCommand):
    help = "Öğrenci profilleri ve transkript verileri seed'le"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Mevcut öğrenci profillerini sil ve yeniden oluştur",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            StudentProfile.objects.filter(
                user__username__in=[s[2] for s in STUDENTS_DATA]
            ).delete()
            self.stdout.write(self.style.WARNING("[x] Mevcut ogrenciler silindi."))

        self.stdout.write(self.style.SUCCESS("\n[*] Ogrenci Profilleri Seed'leniyor...\n"))

        for first, last, username, dept, prog, year, gpa, student_no in STUDENTS_DATA:
            profile = create_or_update_student(first, last, username, dept, prog, year, gpa, student_no)
            if profile:
                seed_enrollments_for_student(profile, year, gpa)

        self.stdout.write(self.style.SUCCESS("\n[OK] Tamamlandi!\n"))
        self.stdout.write(self.style.SUCCESS(f"Toplam {len(STUDENTS_DATA)} ogrenci profili hazirlanmis.\n"))
