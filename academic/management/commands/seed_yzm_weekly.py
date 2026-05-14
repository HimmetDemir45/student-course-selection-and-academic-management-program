"""
YZM Lisans haftalık ders programını seed eder (GÜZ 2025-2026).

Görseldeki KTU OF Teknoloji Fak. Yazılım Mühendisliği 2025-2026 Güz programını
Güz 2025-2026 dönemine bağlar. Derslikler CourseOffering.classroom alanına
düzgün eşleştirilir. Idempotent — tekrar çalıştırılabilir.

Kullanım:
    python manage.py seed_yzm_weekly
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
    (0, 8, 10, 2, "Veri Tabanı ve Yönetimi", "Arş.Gör.Dr. Hakan AYDIN", "D2"),
    (0, 10, 12, 2, "Veri Tabanı ve Yönetimi", "Arş.Gör.Dr. Hakan AYDIN", "Lab"),
    (0, 10, 12, 1, "Matematik-I", "Öğr.Gör.Dr. Şenol DEMİR", "D1"),
    (0, 10, 12, 3, "Betik Diller", "Öğr.Gör. Elif ARAS", "D3"),
    (0, 8, 12, 4, "Tasarım Projesi-A", "Dr.Öğr.Üyesi Sefa ARAS", "D4"),
    (0, 13, 15, 1, "Yazılım Mühendisliğine Giriş", "Öğr.Gör. Elif ARAS", "D1"),
    (0, 13, 15, 2, "Diferansiyel Denklemler", "Doç.Dr. Esma ULUTAŞ", "D2"),
    (0, 13, 15, 3, "Yazılım Tasarımı ve Mimarisi-A", "Dr.Öğr.Üyesi Sefa ARAS", "D3"),
    (0, 13, 17, 4, "Tasarım Projesi-F", "Arş.Gör.Dr. Hakan AYDIN", "D4"),
    # ───────── SALI ─────────
    (1, 10, 12, 1, "Programlama-I", "Öğr.Gör. İbrahim Uğur YILMAZ", "Lab"),
    (1, 10, 12, 2, "İngilizce Okuma ve Yazma", "Öğr.Gör.Dr. Zeynep Şahin TİMAR", "D2"),
    (1, 10, 12, 3, "Sayısal Çözümleme", "Doç.Dr. Esma ULUTAŞ", "D3"),
    (1, 10, 12, 4, "Tasarım Projesi-E", "Öğr.Gör. İbrahim Uğur YILMAZ", "D4"),
    (1, 13, 15, 1, "Fizik-I", "Prof.Dr. Burcu SAVAŞKAN", "D1"),
    (1, 13, 15, 2, "Diferansiyel Denklemler", "Doç.Dr. Esma ULUTAŞ", "D2"),
    (1, 13, 15, 3, "Programlama Dili Kavramları", "Öğr.Gör. İbrahim Uğur YILMAZ", "D3"),
    (1, 13, 17, 4, "Tasarım Projesi-C", "Öğr.Gör.Dr. Zeynep Şahin TİMAR", "D4"),
    (1, 15, 17, 1, "Matematik-I", "Öğr.Gör.Dr. Şenol DEMİR", "D1"),
    # ───────── ÇARŞAMBA ─────────
    (2, 8, 10, 1, "İngilizce-I", "Öğr.Gör. Özcan GÜRSOY", "D1"),
    (2, 8, 12, 2, "Nesne Yönelimli Programlama", "Öğr.Gör. Elif ARAS", "D2"),
    (2, 10, 12, 1, "Programlama-I", "Öğr.Gör. İbrahim Uğur YILMAZ", "D1"),
    (2, 10, 12, 3, "Bilgi Güvenliği ve Kriptoloji", "Arş.Gör.Dr. Hakan AYDIN", "D3"),
    (2, 10, 12, 4, "Tasarım Projesi-G", "Arş.Gör.Dr. Mustafa YAZICI", "D4"),
    (2, 13, 16, 1, "Programlama-I", "Öğr.Gör. İbrahim Uğur YILMAZ", "Lab"),
    (2, 14, 16, 2, "İşletim Sistemleri", "Arş.Gör.Dr. Mustafa YAZICI", "D2"),
    (2, 13, 16, 3, "Yazılım Tasarımı ve Mimarisi-B", "Dr.Öğr.Üyesi Sefa ARAS", "D3"),
    (2, 13, 16, 4, "Tasarım Projesi-D", "Öğr.Gör. Elif ARAS", "D4"),
    (2, 20, 21, 2, "USEC0005-Genel Sosyoloji", "Dr.Öğr.Üyesi Ersoy Ö. ALKAN", "U"),
    # ───────── PERŞEMBE ─────────
    (3, 9, 10, 3, "Yazılım Tasarımı ve Mimarisi-A", "Dr.Öğr.Üyesi Sefa ARAS", "Lab"),
    (3, 10, 12, 1, "Bilgisayar Temelleri", "Dr.Öğr.Üyesi Rıfat BENVENİSTE", "D1"),
    (3, 10, 12, 2, "Bilimsel Proje Hazırlama", "Öğr.Gör.Dr. Zeynep Şahin TİMAR", "D2"),
    (3, 10, 12, 3, "Sayısal Çözümleme", "Doç.Dr. Esma ULUTAŞ", "D3"),
    (3, 10, 11, 4, "Mesleki Deneyim-I", "Öğr.Gör. İbrahim Uğur YILMAZ", "D4"),
    (3, 11, 12, 4, "İşyeri Uygulaması", "Öğr.Gör. Elif ARAS", "D4"),
    (3, 13, 15, 1, "İş Sağlığı ve Güvenliği-I", "Öğr. Gör. Dr. M. S. Gedikli", "D1"),
    (3, 13, 15, 2, "Mühendislik ve Bilişim Etiği", "Öğr.Gör.Dr. Zeynep Şahin TİMAR", "D2"),
    (3, 13, 15, 3, "Sistem Programlama", "Dr.Öğr.Üyesi Rıfat BENVENİSTE", "D3"),
    (3, 13, 17, 4, "İşyeri Uygulaması", "Öğr.Gör. Elif ARAS", "D4"),
    (3, 15, 17, 1, "Fizik-I", "Prof.Dr. Burcu SAVAŞKAN", "D1"),
    (3, 15, 17, 3, "Sistem Programlama", "Dr.Öğr.Üyesi Rıfat BENVENİSTE", "Lab"),
    # ───────── CUMA ─────────
    (4, 10, 12, 1, "Türk Dili-I", "Öğr.Gör. Alper KILIÇOĞLU", "U"),
    (4, 10, 12, 2, "Nesne Yönelimli Programlama", "Öğr.Gör. Elif ARAS", "Lab"),
    (4, 10, 12, 3, "Biçimsel Diller ve Otomata", "Arş.Gör.Dr. Mustafa YAZICI", "D3"),
    (4, 10, 12, 4, "Tasarım Projesi-B", "Dr.Öğr.Üyesi Rıfat BENVENİSTE", "D4"),
    (4, 13, 15, 1, "Atatürk İlkeleri ve İnkılap Tarihi-I", "Öğr.Gör. Aziz AŞAN", "U"),
    (4, 13, 15, 2, "Nesne Yönelimli Programlama", "Öğr.Gör. Elif ARAS", "Lab"),
    (4, 13, 15, 4, "Mesleki Deneyim-II", "Öğr.Gör. İbrahim Uğur YILMAZ", "D4"),
    (4, 15, 17, 4, "Bitirme Çalışması", "Öğr.Gör. Elif ARAS", "D4"),
    # ───────── CUMARTESİ ─────────
    (5, 12, 13, 2, "USEC0035-Kalite Okuryazarlığı", "Dr.Öğr.Üyesi Ebru G. AŞIK", "U"),
]

SHARED_PREFIXES = ("USEC", "TDB", "ATA", "YDB", "YDI", "AITB")
UZEM_NAME_KEYWORDS = (
    "ingilizce",
    "türk dili",
    "atatürk",
    "iş sağlığı",
    "mesleki deneyim",
    "i̇şyeri uygulaması",
    "işyeri uygulaması",
)

# Derslik eşleme: room_hint → (building, room_number)  None → classroom=null
ROOM_MAP: dict[str, tuple[str, str] | None] = {
    "D1": ("OF-TF", "D1"),
    "D2": ("OF-TF", "D2"),
    "D3": ("OF-TF", "D3"),
    "D4": ("OF-TF", "D4"),
    "D5": ("OF-TF", "D5"),
    "Lab": ("OF-TF", "Lab"),
    "U": None,  # UZEM / online
}


def _normalize_ascii(s: str) -> str:
    return (
        unicodedata.normalize("NFKD", s)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def _parse_instructor(full: str) -> tuple[str, str, str]:
    parts = full.strip().split()
    last_idx = len(parts) - 1
    surname = parts[last_idx]
    title_parts = []
    i = 0
    while i < last_idx and "." in parts[i]:
        title_parts.append(parts[i])
        i += 1
    title = " ".join(title_parts)
    first_parts = parts[i:last_idx]
    first = " ".join(first_parts) if first_parts else parts[i] if i < last_idx else ""
    return title, first, surname


def _instructor_username(first: str, last: str) -> str:
    first_token = _normalize_ascii(first).split()[0] if first else "x"
    last_token = _normalize_ascii(last).replace(" ", "")
    return f"inst_{first_token}_{last_token}"[:150]


def _course_code(name: str, dept_code: str, counter: dict) -> str:
    head = name.split("-", 1)[0].strip()
    if any(head.startswith(p) for p in SHARED_PREFIXES) and head[-1].isdigit():
        return head
    counter[dept_code] = counter.get(dept_code, 0) + 1
    return f"{dept_code}-WS{counter[dept_code]:03d}"


def _is_shared(name: str) -> bool:
    head = name.split("-", 1)[0].strip()
    if any(head.startswith(p) for p in SHARED_PREFIXES):
        return True
    lower = _normalize_ascii(name)
    return any(kw in lower for kw in (_normalize_ascii(k) for k in UZEM_NAME_KEYWORDS))


def _get_classroom(hint: str) -> Classroom | None:
    mapping = ROOM_MAP.get(hint)
    if mapping is None:
        return None
    building, room_number = mapping
    classroom, _ = Classroom.objects.get_or_create(
        building=building,
        room_number=room_number,
        defaults={"capacity": 60},
    )
    return classroom


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
    help = "YZM Lisans haftalık programını GÜZ 2025-2026 dönemi için seed eder (derslikler dahil)."

    @transaction.atomic
    def handle(self, *args, **opts):
        # ── Semester (GÜZ 2025-2026) ──────────────────────────────────────
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
        if not fall.is_active:
            fall.is_active = True
            fall.save(update_fields=["is_active"])

        # ── Department + Program ──────────────────────────────────────────
        yzm_dept = _get_or_create_department("YZM", "Yazılım Mühendisliği")
        uzem_dept = _get_or_create_department("UZEM", "Uzaktan Eğitim / Ortak Dersler")
        program = _get_or_create_program("YZM-LIS", "Yazılım Mühendisliği Lisans", yzm_dept)

        instructor_map: dict[str, InstructorProfile] = {}
        course_map: dict[str, Course] = {}
        code_counter: dict[str, int] = {"YZM": 0, "UZEM": 0}

        # Hocaları oluştur
        for row in SCHEDULE:
            _, _, _, _, _course, inst_full, _ = row
            if inst_full in instructor_map:
                continue
            title, first, last = _parse_instructor(inst_full)
            username = _instructor_username(first, last)
            user, u_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@uni.edu.tr",
                    "role": User.Role.INSTRUCTOR,
                },
            )
            if u_created or not user.has_usable_password():
                user.set_password("DemoPass2026!")
                user.save()
            employee_no = f"E{abs(hash(username)) % 10**8:08d}"
            profile, p_created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "department": yzm_dept,
                    "title": title or "Öğr. Üyesi",
                    "is_approved": True,
                    "employee_no": employee_no,
                },
            )
            if not profile.is_approved:
                profile.is_approved = True
                profile.save(update_fields=["is_approved"])
            instructor_map[inst_full] = profile
            self.stdout.write(
                f"{'YENI' if p_created else 'OK  '} Hoca: {user.get_full_name()} ({username})"
            )

        # Dersleri oluştur
        for row in SCHEDULE:
            _wd, _sh, _eh, year_level, course_name, _inst, _room = row
            display_name = course_name
            shared = _is_shared(course_name)
            dept = uzem_dept if shared else yzm_dept

            if course_name in course_map:
                continue

            head = display_name.split("-", 1)[0].strip()
            course = None
            if any(head.startswith(p) for p in SHARED_PREFIXES) and head[-1].isdigit():
                course = Course.objects.filter(code=head).first()
            if course is None:
                course = Course.objects.filter(name=display_name).first()
            if course is None:
                code = _course_code(display_name, dept.code, code_counter)
                while Course.objects.filter(code=code).exists():
                    code = _course_code(display_name, dept.code, code_counter)
                course = Course.objects.create(
                    department=dept,
                    program=None if shared else program,
                    code=code,
                    name=display_name,
                    credits=4,
                )
            course_map[course_name] = course

            CurriculumItem.objects.get_or_create(
                program=program,
                course=course,
                defaults={"year_level": year_level, "term": "fall"},
            )

        # ── Offering + Section + TimeSlot ─────────────────────────────────
        offering_cache: dict[tuple[int, int], CourseOffering] = {}

        for row in SCHEDULE:
            weekday, start_h, end_h, _yr, course_name, inst_full, room_hint = row
            course = course_map[course_name]
            instructor = instructor_map[inst_full]
            classroom = _get_classroom(room_hint)
            key = (course.pk, instructor.pk)

            if key in offering_cache:
                offering = offering_cache[key]
            else:
                offering, _ = CourseOffering.objects.get_or_create(
                    course=course,
                    semester=fall,
                    section="A",
                    defaults={
                        "instructor": instructor,
                        "classroom": classroom,
                        "quota": 60,
                        "is_active": True,
                    },
                )
                # Derslik ve hoca her durumda güncel tut
                update_fields = []
                if offering.instructor_id != instructor.pk:
                    offering.instructor = instructor
                    update_fields.append("instructor")
                if offering.classroom_id != (classroom.pk if classroom else None):
                    offering.classroom = classroom
                    update_fields.append("classroom")
                if not offering.is_active:
                    offering.is_active = True
                    update_fields.append("is_active")
                if update_fields:
                    offering.save(update_fields=update_fields)
                offering_cache[key] = offering

            section, _ = CourseSection.objects.get_or_create(
                offering=offering,
                defaults={"is_active": True},
            )
            if not section.is_active:
                section.is_active = True
                section.save(update_fields=["is_active"])

            SectionTimeSlot.objects.get_or_create(
                section=section,
                weekday=weekday,
                start_time=time(start_h, 0),
                end_time=time(end_h, 0),
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[OK] YZM GÜZ haftalık programı seed edildi. "
                f"Dersler: {len(course_map)}, Hocalar: {len(instructor_map)}, "
                f"Satır: {len(SCHEDULE)}"
            )
        )
