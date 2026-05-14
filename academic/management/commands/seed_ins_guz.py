"""
İnşaat Mühendisliği GÜZ 2025-2026 haftalık ders programını seed eder.

Kaynak: ofinsaat_w8T0S.pdf — KTÜ OF Teknoloji Fakültesi İnşaat Mühendisliği Bölümü
[2025-2026] Güz Yarıyılı Lisans Ders Programı.
I. Yarıyıl (yıl 1), III. Yarıyıl (yıl 2), V. Yarıyıl (yıl 3).

Idempotent — tekrar çalıştırılabilir.
Kullanım:
    python manage.py seed_ins_guz
"""
from __future__ import annotations

import unicodedata
from datetime import date, time

from django.core.management.base import BaseCommand
from django.db import transaction

from academic.models import (
    CourseSection,
    CurriculumItem,
    Department,
    Program,
    SectionTimeSlot,
    Semester,
)
from accounts.models import User
from courses.models import Classroom, Course, CourseOffering
from instructors.models import InstructorProfile


# (weekday, start_h, end_h, year_level, course_name, instructor_full, room_hint)
SCHEDULE: list[tuple[int, int, int, int, str, str, str]] = [
    # ───────── PAZARTESİ ─────────
    (0, 10, 12, 1, "Genel Kimya",            "Prof. Dr. İrfan ACAR",           "D1"),
    (0, 13, 15, 1, "Matematik I",             "Öğr. Gör. Dr. Şenol DEMİR",     "D1"),
    (0, 15, 17, 1, "Fizik I",                 "Prof. Dr. İsmail POLAT",         "D1"),
    (0,  9, 11, 3, "Diferansiyel Denklemler", "Doç. Dr. Esma ULUTAŞ",          "D5"),
    (0, 13, 15, 3, "Mukavemet I",             "Prof. Dr. Umut TOPAL",           "D2"),
    (0, 10, 12, 5, "Betonarme",               "Doç. Dr. H. Tahsin ÖZTÜRK",     "D4"),
    # ───────── SALI ─────────
    (1, 10, 12, 1, "Matematik I",             "Öğr. Gör. Dr. Şenol DEMİR",     "D1"),
    (1, 13, 15, 1, "Fizik I",                 "Prof. Dr. İsmail POLAT",         "D1"),
    (1, 10, 12, 3, "Mesleki İngilizce",       "Dr. Öğr. Üyesi Hacer YEŞİLÇİÇEK","D2"),
    (1, 13, 15, 3, "Malzeme Bilimi",          "Doç. Dr. Nurullah ÖKSÜZER",      "D2"),
    (1, 10, 12, 5, "Yapı Dinamiği",           "Dr. Öğr. Üyesi Ebru K. OKUR",   "D5"),
    (1, 13, 15, 5, "Zemin Mekaniği I",        "Dr. Öğr. Üyesi Ümit ÇALIK",     "D4"),
    # ───────── ÇARŞAMBA ─────────
    (2, 10, 12, 1, "İngilizce I",             "Öğr. Gör. Bekir Sıtkı ÖZGEN",   "D1"),
    (2, 13, 15, 1, "İnşaat Müh. Giriş",       "Dr. Öğr. Üyesi Banu YILMAZ",    "D1"),
    (2, 13, 15, 3, "Bilgisayar Programlama",  "Doç. Dr. H. Tahsin ÖZTÜRK",     "DOKAP"),
    (2, 13, 15, 3, "Çevre Teknolojileri",     "Dr. Öğr. Üyesi Nurcan ÖZTÜRK",  "D2"),
    (2, 10, 12, 5, "Akışkanlar Mekaniği",     "Dr. Öğr. Üyesi O. Tuğrul BAKİ", "D4"),
    (2, 13, 15, 5, "Karayolu Mühendisliği",   "Dr. Öğr. Üyesi Hacer YEŞİLÇİÇEK","D4"),
    (2, 15, 17, 5, "İnşaat Makineleri",       "Dr. Öğr. Üyesi Ümit ÇALIK",     "D5"),
    # ───────── PERŞEMBE ─────────
    (3, 10, 12, 1, "Mühendislik Çizimi",      "Dr. Öğr. Üyesi Ali Fuat GENÇ",  "DOKAP"),
    (3, 13, 15, 1, "Kimya",                   "Prof. Dr. İrfan ACAR",           "D1"),
    (3, 15, 17, 1, "Mühendislik Çizimi",      "Dr. Öğr. Üyesi Ali Fuat GENÇ",  "DOKAP"),
    (3,  9, 11, 3, "Ölçme Bilgisi",           "Dr. Öğr. Üyesi Fatih KADI",     "D2"),
    (3, 13, 15, 3, "Dinamik",                 "Prof. Dr. Umut TOPAL",           "D2"),
    (3,  9, 11, 5, "Yapı Statiği I",          "Dr. Öğr. Üyesi Muhammet YURDAKUL","D4"),
    (3, 13, 15, 5, "Yol Üst Yapısı",          "Prof. Dr. Erol İSKENDER",        "D5"),
    (3, 15, 17, 5, "Beton Teknolojileri",     "Doç. Dr. Nurullah ÖKSÜZER",      "D5"),
    # ───────── CUMA ─────────
    (4, 10, 12, 5, "Tüneller",                "Dr. Öğr. Üyesi Ali Fuat GENÇ",  "D4"),
    (4, 13, 15, 1, "Atatürk İlke İnkılap Tarihi I", "Öğr. Gör. Aziz AŞAN",   "U"),
    (4, 13, 15, 3, "Zemin Mekaniği I",        "Dr. Öğr. Üyesi Ümit ÇALIK",     "GeoteknikLab"),
    (4, 15, 17, 1, "Türk Dili I",             "Öğr. Gör. Alper KILIÇOĞLU",     "U"),
    # ───────── CUMARTESİ ─────────
    (5, 13, 15, 3, "Genel Sosyoloji",         "Dr. Öğr. Üyesi Ersoy Özmen ALKAN","U"),
]

SHARED_PREFIXES = ("USEC",)
UZEM_NAME_KEYWORDS = (
    "atatürk",
    "türk dili",
    "genel sosyoloji",
    "i̇ngilizce",
    "ingilizce",
    "iş sağlığı",
)

ROOM_MAP: dict[str, tuple[str, str] | None] = {
    "D1": ("OF-TF", "D1"), "D2": ("OF-TF", "D2"), "D3": ("OF-TF", "D3"),
    "D4": ("OF-TF", "D4"), "D5": ("OF-TF", "D5"),
    "DOKAP": ("DOKAP", "Bilg.Lab"),
    "GeoteknikLab": ("INS", "GeoteknikLab"),
    "Lab": ("INS", "Lab"),
    "U": None,
}


def _normalize_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()

def _parse_instructor(full: str) -> tuple[str, str, str]:
    parts = full.strip().split()
    last_idx = len(parts) - 1
    surname = parts[last_idx]
    i, title_parts = 0, []
    while i < last_idx and "." in parts[i]:
        title_parts.append(parts[i]); i += 1
    return " ".join(title_parts), " ".join(parts[i:last_idx]), surname

def _instructor_username(first: str, last: str) -> str:
    ft = _normalize_ascii(first).split()[0] if first else "x"
    lt = _normalize_ascii(last).replace(" ", "")
    return f"inst_{ft}_{lt}"[:150]

def _is_shared(name: str) -> bool:
    head = name.split("-", 1)[0].strip()
    if any(head.startswith(p) for p in SHARED_PREFIXES):
        return True
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
    """Department hem code hem name unique olduğundan duplicate-name çakışmasına dayanıklı arama."""
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
    help = "İnşaat Mühendisliği GÜZ 2025-2026 haftalık programını seed eder."

    @transaction.atomic
    def handle(self, *args, **opts):
        fall, _ = Semester.objects.get_or_create(
            academic_year="2025-2026",
            term=Semester.Term.FALL,
            defaults={
                "name": "2025-2026 Güz",
                "start_date": date(2025, 9, 15),
                "end_date": date(2026, 1, 31),
                "add_drop_start": date(2025, 9, 15),
                "add_drop_end": date(2025, 10, 10),
                "is_active": True,
            },
        )

        ins_dept = _get_or_create_department("INS", "İnşaat Mühendisliği")
        uzem_dept = _get_or_create_department("UZEM", "Uzaktan Eğitim / Ortak Dersler")
        program = _get_or_create_program("INS-LIS", "İnşaat Mühendisliği Lisans", ins_dept)

        instructor_map: dict[str, InstructorProfile] = {}
        course_map: dict[str, Course] = {}
        code_counter = {"INS": 0, "UZEM": 0}

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
                defaults={"department": ins_dept, "title": title or "Öğr.Üyesi",
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
            dept = uzem_dept if shared else ins_dept
            course = Course.objects.filter(name=course_name).first()
            if course is None:
                code_counter[dept.code] = code_counter.get(dept.code, 0) + 1
                code = f"{dept.code}-GS{code_counter[dept.code]:03d}"
                while Course.objects.filter(code=code).exists():
                    code_counter[dept.code] += 1
                    code = f"{dept.code}-GS{code_counter[dept.code]:03d}"
                course = Course.objects.create(
                    department=dept, program=None if shared else program,
                    code=code, name=course_name, credits=4,
                )
            course_map[course_name] = course
            CurriculumItem.objects.get_or_create(
                program=program, course=course,
                defaults={"year_level": year_level, "term": "fall"},
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
                    course=course, semester=fall, section="A",
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
            f"\n[OK] İnşaat GÜZ seed tamamlandı. "
            f"Dersler: {len(course_map)}, Hocalar: {len(instructor_map)}"
        ))
