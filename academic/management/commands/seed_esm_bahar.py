"""
Enerji Sistemleri Mühendisliği BAHAR 2025-2026 haftalık ders programını seed eder.

Kaynak: ofenerji_lUNRu.pdf — Enerji Sistemleri Mühendisliği Bölümü
2025/2026 Eğitim-Öğretim Yılı BAHAR Yarıyılı Ders Programı.
I. Sınıf, II. Sınıf, III. Sınıf, IV. Sınıf.

Idempotent — tekrar çalıştırılabilir.
Kullanım:
    python manage.py seed_esm_bahar
"""
from __future__ import annotations

import unicodedata
from datetime import date, time

from django.core.management.base import BaseCommand
from django.db import transaction

from academic.models import (
    CourseSection, CurriculumItem, Department, Program, SectionTimeSlot, Semester,
)
from accounts.models import User
from courses.models import Classroom, Course, CourseOffering
from instructors.models import InstructorProfile


# (weekday, start_h, end_h, year_level, course_name, instructor_full, room_hint)
SCHEDULE: list[tuple[int, int, int, int, str, str, str]] = [
    # ───────── PAZARTESİ ─────────
    (0, 10, 12, 1, "Matematik-II",                         "Öğr. Gör. Dr. Şenol DEMİR",    "INS-D1"),
    (0, 13, 15, 1, "Fizik-II",                             "Prof. Dr. İsmail POLAT",        "ESM-D1"),
    (0,  9, 11, 2, "Mühendislikte Sayısal Yöntemler",      "Doç. Dr. Esma ULUTAŞ",          "ESM-D2"),
    (0, 13, 15, 2, "Mühendislik Termodinamiği",            "Dr. Öğr. Üyesi Coşkun BAYRAM",  "ESM-D2"),
    (0,  9, 11, 3, "Nükleer Enerji",                       "Prof. Dr. İrfan ACAR",          "ESM-D3"),
    (0, 13, 15, 3, "Lojik Devreler",                       "Dr. Öğr. Üyesi Erhan SESLİ",   "DOKAP"),
    # ───────── SALI ─────────
    (1,  9, 11, 1, "Bilgisayar Programlama",               "Dr. Öğr. Üyesi Hamed SHAMSİ",  "DOKAP"),
    (1, 13, 15, 1, "Matematik-II",                         "Öğr. Gör. Dr. Şenol DEMİR",    "INS-D1"),
    (1, 15, 17, 1, "Fizik-II",                             "Prof. Dr. İsmail POLAT",        "ESM-D1"),
    (1, 10, 12, 2, "Mühendislik Termodinamiği",            "Dr. Öğr. Üyesi Coşkun BAYRAM",  "ESM-D2"),
    (1, 13, 15, 2, "Sunum ve Sunuş Teknikleri",            "Doç. Dr. Nurullah ÖKSÜZER",     "KonSalon"),
    (1,  9, 11, 3, "Hidroelektrik Santraller",              "Dr. Öğr. Üyesi Haluk KELEŞ",   "ESM-D3"),
    (1, 15, 17, 3, "Lojik Devreler",                       "Dr. Öğr. Üyesi Erhan SESLİ",   "DOKAP"),
    (1, 10, 12, 4, "Enerji Mevzuatı",                      "Prof. Dr. Burcu SAVAŞKAN",      "ESM-D1"),
    (1, 13, 15, 4, "Rüzgar ve Güneş Enerji Sistemleri",    "Prof. Dr. İsmail POLAT",        "ESM-D1"),
    # ───────── ÇARŞAMBA ─────────
    (2,  9, 11, 1, "Mühendislik Çizimi-II",                "Dr. Öğr. Üyesi Coşkun BAYRAM",  "DOKAP"),
    (2, 10, 12, 2, "Araştırma Yöntem ve Teknikleri",       "Prof. Dr. Burcu SAVAŞKAN",      "ESM-D2"),
    (2, 13, 15, 2, "İngilizce Konuşma",                    "Öğr. Gör. Bekir Sıtkı ÖZGEN",  "ESM-D1"),
    (2,  9, 11, 3, "Elektrik Makineleri-II",               "Dr. Öğr. Üyesi Ömür AKYAZI",   "ESM-D3"),
    (2, 10, 12, 4, "Doğal Gaz Tesisatı",                   "Dr. Öğr. Üyesi Haluk KELEŞ",   "ESM-D1"),
    (2, 13, 15, 4, "Enerji Laboratuvarı",                   "Prof. Dr. İsmail POLAT",        "EnerjLab"),
    (2, 13, 15, 1, "İş Sağlığı ve Güvenliği-II",           "Dr. Tekmile CÜREBAL",           "KonSalon"),
    (2, 15, 17, 1, "İngilizce-II",                         "Öğr. Gör. Bekir Sıtkı ÖZGEN",  "ESM-D1"),
    # ───────── PERŞEMBE ─────────
    (3,  9, 11, 2, "Devre Analizi-I",                      "Dr. Öğr. Üyesi Hamed SHAMSİ",  "ESM-D2"),
    (3, 13, 15, 1, "Lineer Cebir",                         "Dr. Öğr. Üyesi Muhammet YAZICI","ESM-D1"),
    (3, 13, 15, 2, "Mühendislik Matematiği",               "Doç. Dr. Esma ULUTAŞ",          "ESM-D2"),
    (3, 10, 12, 3, "Güç Sistemlerine Giriş",               "Dr. Öğr. Üyesi Ömür AKYAZI",   "ESM-D3"),
    (3, 13, 15, 3, "Isıtma, Havalandırma ve İklimlendirme","Dr. Özlem FAZLIOĞLU",           "ESM-D5"),
    (3, 10, 12, 4, "Kombine Isı ve Güç Santralleri",       "Dr. Öğr. Üyesi Haluk KELEŞ",   "ESM-D1"),
    (3, 13, 15, 4, "Elektrik Tesislerinde Güvenlik",       "Dr. Öğr. Üyesi Ömür AKYAZI",   "ESM-D3"),
    # ───────── CUMA ─────────
    (4,  8,  9, 1, "Atatürk İlkeleri ve İnkılap Tarihi-II","Öğr. Gör. Aziz AŞAN",          "U"),
    (4, 10, 11, 1, "Türk Dili-II",                         "Öğr. Gör. Alper KILIÇOĞLU",    "U"),
    (4,  9, 11, 3, "Enerji İletim Hatları",                "Dr. Öğr. Üyesi Ömür AKYAZI",   "ESM-D3"),
    (4, 13, 15, 3, "Güç Sistemlerine Giriş",               "Dr. Öğr. Üyesi Ömür AKYAZI",   "ESM-D3"),
    # USEC dersleri (Çarşamba/Pazartesi akşam — UZEM)
    (0, 20, 21, 2, "Girişimcilik",                         "Öğr. Gör. Alper KILIÇOĞLU",    "U"),
    (2, 20, 21, 2, "Proje Yönetimi",                       "Öğr. Gör. Aziz AŞAN",          "U"),
    (0, 18, 19, 4, "İş Sağlığı ve Güvenliği",              "Dr. Tekmile CÜREBAL",           "U"),
    (0, 19, 20, 4, "Kariyer Planlama",                     "Prof. Dr. Hülya KALAYCIOĞLU",   "U"),
]

UZEM_NAME_KEYWORDS = (
    "atatürk",
    "türk dili",
    "i̇ngilizce-ii",
    "ingilizce-ii",
    "iş sağlığı ve güvenliği-ii",
    "girişimcilik",
    "proje yönetimi",
    "kariyer planlama",
    "iş sağlığı ve güvenliği",
)

ROOM_MAP: dict[str, tuple[str, str] | None] = {
    "ESM-D1": ("ESM", "D1"), "ESM-D2": ("ESM", "D2"), "ESM-D3": ("ESM", "D3"),
    "ESM-D4": ("ESM", "D4"), "ESM-D5": ("ESM", "D5"),
    "INS-D1": ("OF-TF", "D1"),
    "DOKAP": ("DOKAP", "Bilg.Lab"),
    "KonSalon": ("OF-TF", "KonSalon"),
    "EnerjLab": ("ESM", "EnerjLab"),
    "Lab": ("ESM", "Lab"),
    "U": None,
}


def _normalize_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()

def _parse_instructor(full: str) -> tuple[str, str, str]:
    parts = full.strip().split()
    last_idx = len(parts) - 1
    surname = parts[last_idx]
    i, tp = 0, []
    while i < last_idx and "." in parts[i]:
        tp.append(parts[i]); i += 1
    return " ".join(tp), " ".join(parts[i:last_idx]), surname

def _instructor_username(first: str, last: str) -> str:
    ft = _normalize_ascii(first).split()[0] if first else "x"
    lt = _normalize_ascii(last).replace(" ", "")
    return f"inst_{ft}_{lt}"[:150]

def _is_shared(name: str) -> bool:
    lower = _normalize_ascii(name)
    return any(kw in lower for kw in (_normalize_ascii(k) for k in UZEM_NAME_KEYWORDS))

def _get_classroom(hint: str) -> Classroom | None:
    mapping = ROOM_MAP.get(hint)
    if not mapping:
        return None
    building, room_number = mapping
    obj, _ = Classroom.objects.get_or_create(
        building=building, room_number=room_number, defaults={"capacity": 60}
    )
    return obj


def _get_or_create_department(code: str, name: str) -> Department:
    dept = Department.objects.filter(code=code).first()
    if dept:
        return dept
    dept = Department.objects.filter(name=name).first()
    if dept:
        return dept
    return Department.objects.create(code=code, name=name)


def _get_or_create_program(code: str, name: str, department: Department) -> Program:
    """Program: code unique, (department, name) da unique. Üçlü arama."""
    prog = Program.objects.filter(code=code).first()
    if prog:
        return prog
    prog = Program.objects.filter(department=department, name=name).first()
    if prog:
        return prog
    return Program.objects.create(code=code, name=name, department=department)


class Command(BaseCommand):
    help = "Enerji Sistemleri Mühendisliği BAHAR 2025-2026 haftalık programını seed eder."

    @transaction.atomic
    def handle(self, *args, **opts):
        spring, _ = Semester.objects.get_or_create(
            academic_year="2025-2026",
            term=Semester.Term.SPRING,
            defaults={
                "name": "2025-2026 Bahar",
                "start_date": date(2026, 2, 10),
                "end_date": date(2026, 6, 30),
                "add_drop_start": date(2026, 2, 10),
                "add_drop_end": date(2026, 3, 7),
                "is_active": False,
            },
        )

        esm_dept = _get_or_create_department("ESM", "Enerji Sistemleri Mühendisliği")
        uzem_dept = _get_or_create_department("UZEM", "Uzaktan Eğitim / Ortak Dersler")
        program = _get_or_create_program("ESM-LIS", "Enerji Sistemleri Mühendisliği Lisans", esm_dept)

        instructor_map: dict[str, InstructorProfile] = {}
        course_map: dict[str, Course] = {}
        code_counter = {"ESM": 0, "UZEM": 0}

        for row in SCHEDULE:
            _, _, _, _, _, inst_full, _ = row
            if inst_full in instructor_map:
                continue
            title, first, last = _parse_instructor(inst_full)
            username = _instructor_username(first, last)
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last,
                          "email": f"{username}@uni.edu.tr", "role": User.Role.INSTRUCTOR},
            )
            if u_created or not user.has_usable_password():
                user.set_password("DemoPass2026!"); user.save()
            emp = f"E{abs(hash(username)) % 10**8:08d}"
            profile, p_created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={"department": esm_dept, "title": title or "Öğr.Üyesi",
                          "is_approved": True, "employee_no": emp},
            )
            if not profile.is_approved:
                profile.is_approved = True; profile.save(update_fields=["is_approved"])
            instructor_map[inst_full] = profile
            self.stdout.write(f"{'YENI' if p_created else 'OK  '} {user.get_full_name()}")

        for row in SCHEDULE:
            _, _, _, year_level, course_name, _, _ = row
            if course_name in course_map:
                continue
            shared = _is_shared(course_name)
            dept = uzem_dept if shared else esm_dept
            course = Course.objects.filter(name=course_name).first()
            if course is None:
                code_counter[dept.code] = code_counter.get(dept.code, 0) + 1
                code = f"{dept.code}-BS{code_counter[dept.code]:03d}"
                while Course.objects.filter(code=code).exists():
                    code_counter[dept.code] += 1
                    code = f"{dept.code}-BS{code_counter[dept.code]:03d}"
                course = Course.objects.create(
                    department=dept, program=None if shared else program,
                    code=code, name=course_name, credits=4,
                )
            course_map[course_name] = course
            CurriculumItem.objects.get_or_create(
                program=program, course=course,
                defaults={"year_level": year_level, "term": "spring"},
            )

        offering_cache: dict[tuple[int, int], CourseOffering] = {}
        for row in SCHEDULE:
            weekday, start_h, end_h, _, course_name, inst_full, room_hint = row
            course = course_map[course_name]
            instructor = instructor_map[inst_full]
            classroom = _get_classroom(room_hint)
            key = (course.pk, instructor.pk)

            if key not in offering_cache:
                offering, _ = CourseOffering.objects.get_or_create(
                    course=course, semester=spring, section="A",
                    defaults={"instructor": instructor, "classroom": classroom,
                              "quota": 60, "is_active": True},
                )
                upd = []
                if offering.instructor_id != instructor.pk:
                    offering.instructor = instructor; upd.append("instructor")
                if offering.classroom_id != (classroom.pk if classroom else None):
                    offering.classroom = classroom; upd.append("classroom")
                if not offering.is_active:
                    offering.is_active = True; upd.append("is_active")
                if upd:
                    offering.save(update_fields=upd)
                offering_cache[key] = offering

            section, _ = CourseSection.objects.get_or_create(
                offering=offering_cache[key], defaults={"is_active": True}
            )
            if not section.is_active:
                section.is_active = True; section.save(update_fields=["is_active"])
            SectionTimeSlot.objects.get_or_create(
                section=section, weekday=weekday,
                start_time=time(start_h, 0), end_time=time(end_h, 0),
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] Enerji Sistemleri BAHAR seed tamamlandı. "
            f"Dersler: {len(course_map)}, Hocalar: {len(instructor_map)}"
        ))
