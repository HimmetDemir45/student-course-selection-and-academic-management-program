"""
İnşaat Mühendisliği BAHAR 2025-2026 haftalık ders programını seed eder.

Kaynak: ofinsaat_LZ6CH.pdf — İnşaat Mühendisliği Bölümü 2025/2026 Eğitim-Öğretim Yılı
BAHAR Yarıyılı Ders Programı.
II. Yarıyıl (yıl 1), IV. Yarıyıl (yıl 2), VI. Yarıyıl (yıl 3), VIII. Yarıyıl (yıl 4).

Idempotent — tekrar çalıştırılabilir.
Kullanım:
    python manage.py seed_ins_bahar
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
    (0,  8, 10, 1, "Fizik II",                       "Prof. Dr. İsmail POLAT",           "D1"),
    (0, 10, 12, 1, "Matematik II",                   "Öğr. Gör. Dr. Şenol DEMİR",        "D1"),
    (0, 13, 15, 1, "Statik",                          "Prof. Dr. Umut TOPAL",             "D1"),
    (0, 10, 12, 2, "Hidroloji",                       "Dr. Öğr. Üyesi Banu YILMAZ",       "D2"),
    (0, 13, 15, 2, "Mühendislik Matematiği",          "Doç. Dr. Esma ULUTAŞ",             "D5"),
    (0, 10, 12, 3, "Köprüler",                        "Dr. Öğr. Üyesi Ebru K. OKUR",      "D5"),
    (0, 13, 15, 3, "Zemin Mekaniği II",               "Dr. Öğr. Üyesi Ümit ÇALIK",        "D4"),
    (0, 13, 15, 4, "Deprem Mühendisliği Giriş",       "Dr. Öğr. Üyesi Ebru K. OKUR",      "D5"),
    (0, 10, 12, 4, "Bet. Proj. Bil. Yrd. Çöz.",       "Dr. Öğr. Üyesi Muhammet YURDAKUL", "DOKAP"),
    # ───────── SALI ─────────
    (1, 10, 12, 1, "Fizik II",                        "Prof. Dr. İsmail POLAT",           "D1"),
    (1, 13, 15, 1, "Matematik II",                    "Öğr. Gör. Dr. Şenol DEMİR",        "D1"),
    (1, 10, 12, 2, "Sayısal Analiz",                  "Doç. Dr. Esma ULUTAŞ",             "D2"),
    (1, 13, 15, 2, "Sunum ve Sunuş Teknikleri",       "Doç. Dr. Nurullah ÖKSÜZER",        "KonSalon"),
    (1, 10, 12, 3, "Su Yapıları",                     "Dr. Öğr. Üyesi O. Tuğrul BAKİ",   "D4"),
    (1, 13, 15, 3, "Hidrolik",                        "Dr. Öğr. Üyesi Nurcan ÖZTÜRK",    "D3"),
    (1, 10, 12, 4, "Su Yapıları",                     "Dr. Öğr. Üyesi O. Tuğrul BAKİ",   "D4"),
    (1, 13, 15, 4, "Ulaşım Politikaları",             "Prof. Dr. Erol İSKENDER",          "D5"),
    # ───────── ÇARŞAMBA ─────────
    (2, 10, 12, 1, "İngilizce II",                    "Öğr. Gör. Bekir Sıtkı ÖZGEN",      "D1"),
    (2, 13, 15, 1, "Olasılık ve İstatistik",          "Dr. Öğr. Üyesi H. SHAMSİ",        "D1"),
    (2, 10, 12, 2, "Mimarlık Bilgisi",                "Dr. Öğr. Üyesi Hacer YEŞİLÇİÇEK", "D2"),
    (2, 13, 15, 2, "Girişimcilik",                    "Dr. Öğr. Üyesi Hacer YEŞİLÇİÇEK", "D2"),
    (2,  9, 11, 3, "Yapı Statiği II",                 "Dr. Öğr. Üyesi Muhammet YURDAKUL", "D3"),
    (2, 13, 15, 3, "Yapı Mühendisliği Bil. Uyg.",     "Dr. Öğr. Üyesi Ali Fuat GENÇ",    "DOKAP"),
    (2, 13, 15, 4, "Temel Mühendisliği",              "Dr. Öğr. Üyesi Ümit ÇALIK",        "D4"),
    # ───────── PERŞEMBE ─────────
    (3,  9, 11, 2, "Yapı Malzemesi",                  "Doç. Dr. Nurullah ÖKSÜZER",        "D2"),
    (3, 10, 12, 3, "İş Sağlığı ve Güvenliği",         "Dr. Öğr. Üyesi Banu YILMAZ",       "D3"),
    (3, 13, 15, 1, "İnşaat Jeolojisi",                "Dr. Öğr. Üyesi Ümit ÇALIK",        "D1"),
    (3, 13, 15, 2, "Mukavemet II",                    "Prof. Dr. Umut TOPAL",             "D2"),
    (3, 13, 15, 3, "Karayolu Proje",                  "Prof. Dr. Erol İSKENDER",          "D5"),
    (3, 13, 15, 4, "Çelik Yapılar",                   "Dr. Öğr. Üyesi Ali Fuat GENÇ",    "D4"),
    # ───────── CUMA ─────────
    (4,  8, 10, 1, "Türk Dili II",                    "Öğr. Gör. Alper KILIÇOĞLU",        "U"),
    (4, 10, 12, 1, "Atatürk İlke İnkılap Tarihi II",  "Öğr. Gör. Aziz AŞAN",             "U"),
    (4,  9, 11, 3, "Betonarme Proje",                 "Doç. Dr. H. Tahsin ÖZTÜRK",        "D3"),
    (4, 10, 12, 4, "Su Yapıları",                     "Dr. Öğr. Üyesi O. Tuğrul BAKİ",   "D4"),
    (4, 13, 15, 3, "Zemin Mekaniği II",               "Dr. Öğr. Üyesi Ümit ÇALIK",        "GeoteknikLab"),
    (4, 13, 15, 4, "Betonarme Özel Konular",          "Doç. Dr. H. Tahsin ÖZTÜRK",        "D4"),
]

# USEC dersleri ayrı seed ile yönetilir; burada sadece bölüme özgü paylaşımlı dersler
UZEM_NAME_KEYWORDS = (
    "türk dili",
    "atatürk",
    "i̇ngilizce",
    "ingilizce",
    "iş sağlığı",
)

ROOM_MAP: dict[str, tuple[str, str] | None] = {
    "D1": ("OF-TF", "D1"), "D2": ("OF-TF", "D2"), "D3": ("OF-TF", "D3"),
    "D4": ("OF-TF", "D4"), "D5": ("OF-TF", "D5"),
    "DOKAP": ("DOKAP", "Bilg.Lab"),
    "GeoteknikLab": ("INS", "GeoteknikLab"),
    "KonSalon": ("OF-TF", "KonSalon"),
    "Lab": ("INS", "Lab"),
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


class Command(BaseCommand):
    help = "İnşaat Mühendisliği BAHAR 2025-2026 haftalık programını seed eder."

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

        ins_dept, _ = Department.objects.get_or_create(
            code="INS", defaults={"name": "İnşaat Mühendisliği"}
        )
        uzem_dept, _ = Department.objects.get_or_create(
            code="UZEM", defaults={"name": "Uzaktan Eğitim / Ortak Dersler"}
        )
        program, _ = Program.objects.get_or_create(
            code="INS-LIS",
            defaults={"department": ins_dept, "name": "İnşaat Mühendisliği Lisans"},
        )

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
            f"\n[OK] İnşaat BAHAR seed tamamlandı. "
            f"Dersler: {len(course_map)}, Hocalar: {len(instructor_map)}"
        ))
