"""
YZM Lisans BAHAR 2025-2026 haftalık ders programını seed eder.

Kaynak: ofyazilim_8TaeE.pdf — KTÜ OF Teknoloji Fakültesi Yazılım Mühendisliği Bölümü
2025-2026 Bahar Yarıyılı Lisans Ders Programı.

Idempotent — tekrar çalıştırılabilir.
Kullanım:
    python manage.py seed_yzm_bahar
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


# (weekday[0=Mon..5=Sat], start_h, end_h, year_level, course_name, instructor_full, room_hint)
SCHEDULE: list[tuple[int, int, int, int, str, str, str]] = [
    # ───────── PAZARTESİ ─────────
    (0,  9, 11, 1, "Programlama-II",                        "Öğr.Gör. İbrahim Uğur YILMAZ",      "Lab"),
    (0, 10, 12, 2, "Olasılık ve İstatistik",                "Öğr.Gör.Dr. Zeynep Şahin TİMAR",    "D2"),
    (0, 10, 12, 3, "Veri Tabanı Yönetim Sistemleri",        "Arş.Gör.Dr. Hakan AYDIN",            "D3"),
    (0, 10, 12, 4, "Yazılım Kalite Güvencesi",              "Öğr.Gör. Elif ARAS",                 "D4"),
    (0, 13, 15, 1, "Matematik-II",                          "Öğr.Gör.Dr. Şenol DEMİR",            "D1"),
    (0, 13, 15, 2, "Olasılık ve İstatistik",                "Öğr.Gör.Dr. Zeynep Şahin TİMAR",    "D2"),
    (0, 13, 15, 3, "Mobil Programlama",                     "Dr.Öğr.Üyesi Rıfat BENVENİSTE",     "D3"),
    (0, 13, 15, 4, "Meta-Sezgisel Optimizasyon",            "Dr.Öğr.Üyesi Sefa ARAS",             "D4"),
    (0, 15, 17, 2, "Bilimsel Araştırma Yöntemleri",         "Öğr.Gör.Dr. Zeynep Şahin TİMAR",    "D2"),
    (0, 15, 17, 4, "İşyeri Uygulaması",                     "Öğr.Gör. Elif ARAS",                 "D4"),
    # ───────── SALI ─────────
    (1,  8, 10, 4, "İşyeri Uygulaması",                     "Öğr.Gör. Elif ARAS",                 "D4"),
    (1,  9, 11, 2, "Ayrık Matematik",                       "Öğr.Gör. Ömer ÇAKIR",                "D2"),
    (1,  9, 11, 3, "Yapay Zekâ",                            "Dr.Öğr.Üyesi Sefa ARAS",             "D3"),
    (1, 10, 12, 1, "Matematik-II",                          "Öğr.Gör.Dr. Şenol DEMİR",            "D1"),
    (1, 10, 12, 4, "Derin Öğrenme",                         "Öğr.Gör. Elif ARAS",                 "D4"),
    (1, 13, 15, 1, "Veri Yapıları",                         "Öğr.Gör. Elif ARAS",                 "D1"),
    (1, 13, 15, 2, "Sunum ve Sunuş Teknikleri",             "Doç.Dr. Nurullah ÖKSÜZER",            "D2"),
    (1, 13, 15, 3, "Gömülü Sistemler",                      "Dr.Öğr.Üyesi Rıfat BENVENİSTE",     "D3"),
    (1, 15, 17, 1, "Fizik-II",                              "Prof.Dr. Burcu SAVAŞKAN",             "D1"),
    (1, 15, 17, 2, "İleri Web Uygulamaları",                "Öğr.Gör. İbrahim Uğur YILMAZ",      "D2"),
    (1, 15, 17, 3, "Optimizasyon Teorisi ve Uygulamaları",  "Dr.Öğr.Üyesi Emin TUĞCU",            "D5"),
    (1, 15, 17, 4, "İşyeri Uygulaması",                     "Öğr.Gör. Elif ARAS",                 "D4"),
    # ───────── ÇARŞAMBA ─────────
    (2,  8, 10, 1, "İngilizce-II",                          "Öğr.Gör. Özcan GÜRSOY",              "D1"),
    (2,  8, 10, 4, "Mesleki Deneyim-I",                     "Arş.Gör.Dr. Hakan AYDIN",            "D4"),
    (2, 10, 12, 1, "İş Sağlığı ve Güvenliği-II",            "Öğr.Gör. İbrahim Uğur YILMAZ",      "D1"),
    (2, 10, 12, 2, "Mikroişlemciler",                       "Dr.Öğr.Üyesi Rıfat BENVENİSTE",     "D2"),
    (2, 10, 12, 3, "Yazılım Sınama ve Doğrulama",           "Arş.Gör.Dr. Hakan AYDIN",            "D3"),
    (2, 10, 12, 4, "Siber Güvenlik ve Uygulamaları",        "Arş.Gör.Dr. Mustafa YAZICI",         "D4"),
    (2, 13, 15, 1, "Fizik-II",                              "Prof.Dr. Burcu SAVAŞKAN",             "D1"),
    (2, 13, 15, 2, "Mikroişlemciler",                       "Dr.Öğr.Üyesi Rıfat BENVENİSTE",     "Lab"),
    (2, 13, 15, 3, "Bilgisayar Ağları",                     "Arş.Gör.Dr. Hakan AYDIN",            "D3"),
    (2, 13, 15, 4, "Veri Madenciliği",                      "Arş.Gör.Dr. Mustafa YAZICI",         "D4"),
    (2, 15, 17, 1, "Yazılım Gereksinim Mühendisliği",       "Arş.Gör.Dr. Mustafa YAZICI",         "D1"),
    (2, 15, 17, 2, "Mikroişlemciler",                       "Dr.Öğr.Üyesi Rıfat BENVENİSTE",     "Lab"),
    (2, 15, 17, 3, "Bilgisayar Ağları",                     "Arş.Gör.Dr. Hakan AYDIN",            "Lab"),
    (2, 16, 17, 3, "Bilgisayar Ağları",                     "Arş.Gör.Dr. Hakan AYDIN",            "Lab"),
    (2, 19, 20, 2, "Bilim Tarihi",                          "Dr.Öğr.Üyesi Deniz ÇOLAK",           "U"),
    (2, 20, 21, 2, "Meslek Etiği",                          "Öğr.Gör.Dr. Canan YILMAZ",           "U"),
    # ───────── PERŞEMBE ─────────
    (3,  8, 10, 2, "İleri Web Uygulamaları",                "Öğr.Gör. İbrahim Uğur YILMAZ",      "Lab"),
    (3,  9, 11, 1, "Lineer Cebir",                          "Dr.Öğr.Üyesi Muhammed YAZICI",       "D1"),
    (3, 10, 12, 2, "İleri Web Uygulamaları",                "Öğr.Gör. İbrahim Uğur YILMAZ",      "Lab"),
    (3, 10, 12, 3, "Yazılım Sınama ve Doğrulama",           "Arş.Gör.Dr. Hakan AYDIN",            "Lab"),
    (3, 11, 12, 3, "Yazılım Sınama ve Doğrulama",           "Arş.Gör.Dr. Hakan AYDIN",            "Lab"),
    (3, 10, 12, 4, "Yazılım Geliştirme Standartları",       "Öğr.Gör.Dr. Zeynep Şahin TİMAR",    "D4"),
    (3, 13, 15, 2, "Mesleki İngilizce",                     "Öğr.Gör.Dr. Zeynep Şahin TİMAR",    "D2"),
    (3, 13, 15, 3, "Yapay Zekâ",                            "Dr.Öğr.Üyesi Sefa ARAS",             "Lab"),
    (3, 13, 15, 4, "Mesleki Deneyim-II",                    "Arş.Gör.Dr. Hakan AYDIN",            "D4"),
    (3, 15, 17, 1, "Programlama-II",                        "Öğr.Gör. İbrahim Uğur YILMAZ",      "Lab"),
    (3, 16, 17, 1, "Programlama-II",                        "Öğr.Gör. İbrahim Uğur YILMAZ",      "Lab"),
    (3, 19, 20, 2, "Kariyer Planlama",                      "Prof.Dr. Hülya KALAYCIOĞLU",          "U"),
    # ───────── CUMA ─────────
    (4,  8, 10, 1, "Türk Dili-II",                          "Öğr.Gör. Alper KILIÇOĞLU",           "U"),
    (4, 10, 12, 1, "Veri Yapıları",                         "Öğr.Gör. Elif ARAS",                 "Lab"),
    (4, 10, 11, 1, "Veri Yapıları",                         "Öğr.Gör. Elif ARAS",                 "Lab"),
    (4, 10, 12, 4, "Tasarım Projesi",                       "Öğr.Gör. Elif ARAS",                 "D4"),
    (4, 13, 15, 1, "Atatürk İlkeleri ve İnkılap Tarihi-II", "Öğr.Gör. Aziz AŞAN",                "U"),
    (4, 13, 15, 4, "Bitirme Çalışması",                     "Öğr.Gör. Elif ARAS",                 "D4"),
]

SHARED_PREFIXES = ("USEC", "TDB", "ATA", "YDB", "YDI", "AITB")
UZEM_NAME_KEYWORDS = (
    "ingilizce",
    "türk dili",
    "atatürk",
    "iş sağlığı",
    "kariyer planlama",
    "bilim tarihi",
    "meslek etiği",
    "mesleki deneyim",
    "i̇şyeri uygulaması",
    "işyeri uygulaması",
)

ROOM_MAP: dict[str, tuple[str, str] | None] = {
    "D1": ("OF-TF", "D1"), "D2": ("OF-TF", "D2"), "D3": ("OF-TF", "D3"),
    "D4": ("OF-TF", "D4"), "D5": ("OF-TF", "D5"),
    "Lab": ("OF-TF", "Lab"),
    "U": None,
}


def _normalize_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def _parse_instructor(full: str) -> tuple[str, str, str]:
    parts = full.strip().split()
    last_idx = len(parts) - 1
    surname = parts[last_idx]
    i = 0
    title_parts = []
    while i < last_idx and "." in parts[i]:
        title_parts.append(parts[i])
        i += 1
    title = " ".join(title_parts)
    first = " ".join(parts[i:last_idx]) if i < last_idx else ""
    return title, first, surname


def _instructor_username(first: str, last: str) -> str:
    ft = _normalize_ascii(first).split()[0] if first else "x"
    lt = _normalize_ascii(last).replace(" ", "")
    return f"inst_{ft}_{lt}"[:150]


def _course_code(name: str, dept_code: str, counter: dict) -> str:
    head = name.split("-", 1)[0].strip()
    if any(head.startswith(p) for p in SHARED_PREFIXES) and head[-1].isdigit():
        return head
    counter[dept_code] = counter.get(dept_code, 0) + 1
    return f"{dept_code}-BS{counter[dept_code]:03d}"


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


class Command(BaseCommand):
    help = "YZM Lisans BAHAR 2025-2026 haftalık programını seed eder."

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

        yzm_dept, _ = Department.objects.get_or_create(
            code="YZM", defaults={"name": "Yazılım Mühendisliği"}
        )
        uzem_dept, _ = Department.objects.get_or_create(
            code="UZEM", defaults={"name": "Uzaktan Eğitim / Ortak Dersler"}
        )
        program, _ = Program.objects.get_or_create(
            code="YZM-LIS",
            defaults={"department": yzm_dept, "name": "Yazılım Mühendisliği Lisans"},
        )

        instructor_map: dict[str, InstructorProfile] = {}
        course_map: dict[str, Course] = {}
        code_counter: dict[str, int] = {"YZM": 0, "UZEM": 0}

        for row in SCHEDULE:
            _, _, _, _, _, inst_full, _ = row
            if inst_full in instructor_map:
                continue
            title, first, last = _parse_instructor(inst_full)
            username = _instructor_username(first, last)
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first, "last_name": last,
                    "email": f"{username}@uni.edu.tr",
                    "role": User.Role.INSTRUCTOR,
                },
            )
            if u_created or not user.has_usable_password():
                user.set_password("DemoPass2026!")
                user.save()
            emp = f"E{abs(hash(username)) % 10**8:08d}"
            profile, p_created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={"department": yzm_dept, "title": title or "Öğr.Üyesi",
                          "is_approved": True, "employee_no": emp},
            )
            if not profile.is_approved:
                profile.is_approved = True
                profile.save(update_fields=["is_approved"])
            instructor_map[inst_full] = profile
            self.stdout.write(f"{'YENI' if p_created else 'OK  '} {user.get_full_name()}")

        for row in SCHEDULE:
            _, _, _, year_level, course_name, _, _ = row
            if course_name in course_map:
                continue
            shared = _is_shared(course_name)
            dept = uzem_dept if shared else yzm_dept
            head = course_name.split("-", 1)[0].strip()
            course = None
            if any(head.startswith(p) for p in SHARED_PREFIXES) and head[-1].isdigit():
                course = Course.objects.filter(code=head).first()
            if course is None:
                course = Course.objects.filter(name=course_name).first()
            if course is None:
                code = _course_code(course_name, dept.code, code_counter)
                while Course.objects.filter(code=code).exists():
                    code = _course_code(course_name, dept.code, code_counter)
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
                update_fields = []
                if offering.instructor_id != instructor.pk:
                    offering.instructor = instructor; update_fields.append("instructor")
                if offering.classroom_id != (classroom.pk if classroom else None):
                    offering.classroom = classroom; update_fields.append("classroom")
                if not offering.is_active:
                    offering.is_active = True; update_fields.append("is_active")
                if update_fields:
                    offering.save(update_fields=update_fields)
                offering_cache[key] = offering

            offering = offering_cache[key]
            section, _ = CourseSection.objects.get_or_create(
                offering=offering, defaults={"is_active": True}
            )
            if not section.is_active:
                section.is_active = True
                section.save(update_fields=["is_active"])
            SectionTimeSlot.objects.get_or_create(
                section=section, weekday=weekday,
                start_time=time(start_h, 0), end_time=time(end_h, 0),
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] YZM BAHAR seed tamamlandı. "
            f"Dersler: {len(course_map)}, Hocalar: {len(instructor_map)}"
        ))
