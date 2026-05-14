"""
Gerçek veri seed komutu: CourseOffering + CourseSection + SectionTimeSlot.

seed_comprehensive çalıştıktan SONRA çalıştırılmalı.
Var olan semester'ları kullanır (veya oluşturur), her curriculum dersi için
CourseOffering + Section + TimeSlot kaydı oluşturur.

Kullanım:
    python manage.py seed_real_data
    python manage.py seed_real_data --academic-year 2025-2026
"""

from __future__ import annotations

from datetime import date, time

from django.core.management.base import BaseCommand
from django.db import transaction

from academic.models import (
    CourseSection,
    CurriculumItem,
    Department,
    SectionTimeSlot,
    Semester,
)
from courses.models import Classroom, Course, CourseOffering
from instructors.models import InstructorProfile

# ─── EĞITIM GÖREVLİSİ → DERS EŞLEŞME ───────────────────────────────────────
# seed_comprehensive.py'daki COURSE_TO_INSTRUCTOR ile tutarlı
COURSE_INSTRUCTOR = {
    # ESM 1. Sınıf
    "ESM1003": "ogr_gor_senol_demir",
    "ESM1005": "prof_ismail_polat",
    "ESM1000": "ogr_gor_senol_demir",
    "ESM1004": "prof_ismail_polat",
    "ESM1010": "dr_hamed_shamsi",
    "ESM1012": "dr_coskun_bayram",
    "ESM1016": "dr_tekmile_curebal",
    "YDB1003": "ogr_gor_bekir_sitki",
    "YDB1004": "ogr_gor_bekir_sitki",
    # ESM 2. Sınıf
    "ESM2041": "dr_hamed_shamsi",
    "ESM2036": "dr_hamed_shamsi",
    "ESM2038": "doc_esma_ulutas",
    "ESM2032": "dr_coskun_bayram",
    "ESM2026": "doc_nurullah_oksuz",
    "ESM2002": "prof_burcu_savaskam",
    "ESM2054": "doc_esma_ulutas",
    "ESM2023": "doc_esma_ulutas",
    # ESM 3. Sınıf
    "ESM3043": "dr_omur_akyazi",
    "ESM3047": "dr_omur_akyazi",
    "ESM3056": "dr_omur_akyazi",
    "ESM4030": "dr_omur_akyazi",
    "ESM3044": "prof_irfan_acar",
    "ESM3045": "dr_ozlem_fazlioglu",
    "ESM3038": "dr_ozlem_fazlioglu",
    "ESM3029": "prof_irfan_acar",
    "ESM3031": "dr_erhan_sesli",
    "ESM3048": "dr_erhan_sesli",
    # ESM 4. Sınıf
    "ESM4013": "prof_burcu_savaskam",
    "ESM4044": "prof_ismail_polat",
    "ESM4054": "dr_haluk_keles",
    "ESM4010": "dr_haluk_keles",
    "ESM4011": "prof_ismail_polat",
    # YZM
    "YZM1005": "ogr_gor_senol_demir",
    "YZM1004": "ogr_gor_senol_demir",
    "YZM2031": "dr_hamed_shamsi",
    "YZM2033": "dr_hamed_shamsi",
    "YZM1015": "dr_hamed_shamsi",
    "YZM1016": "dr_hamed_shamsi",
    "YZM1007": "dr_hamed_shamsi",
    # OINS
    "OINS1009": "dr_muhammet_yazici",
    "OINS1008": "dr_muhammet_yazici",
}

# ─── DERS → DERSLİK EŞLEŞMESİ ───────────────────────────────────────────────
COURSE_CLASSROOM = {
    # ESM-D1
    "ESM1004": ("Enerji Blok", "D1"),
    "YDB1004": ("Enerji Blok", "D1"),
    "ESM1014": ("Enerji Blok", "D1"),
    "YDI2008": ("Enerji Blok", "D1"),
    "ESM4013": ("Enerji Blok", "D1"),
    "ESM4044": ("Enerji Blok", "D1"),
    "ESM4054": ("Enerji Blok", "D1"),
    "ESM4010": ("Enerji Blok", "D1"),
    # ESM-D2
    "ESM2038": ("Enerji Blok", "D2"),
    "ESM2032": ("Enerji Blok", "D2"),
    "ESM2002": ("Enerji Blok", "D2"),
    "ESM2041": ("Enerji Blok", "D2"),
    "ESM2054": ("Enerji Blok", "D2"),
    # ESM-D3
    "ESM3044": ("Enerji Blok", "D3"),
    "ESM3047": ("Enerji Blok", "D3"),
    "ESM3043": ("Enerji Blok", "D3"),
    "ESM3056": ("Enerji Blok", "D3"),
    "ESM4030": ("Enerji Blok", "D3"),
    # ESM-D5
    "ESM3038": ("Enerji Blok", "D5"),
    # Bilgisayar Lab DOKAP
    "ESM1010": ("Bilgisayar Lab", "DOKAP"),
    "ESM1012": ("Bilgisayar Lab", "DOKAP"),
    "ESM3048": ("Bilgisayar Lab", "DOKAP"),
    # İnşaat D1
    "ESM1000": ("İnşaat Blok", "D1"),
    # Konferans
    "ESM1016": ("Prof. K. GELİŞLİ Sal.", "Konferans"),
    "ESM2026": ("Prof. K. GELİŞLİ Sal.", "Konferans"),
    # Lab
    "ESM4011": ("Enerji Lab", "Lab-1"),
}

# ─── DERS SAATLERİ ──────────────────────────────────────────────────────────
# Haftanın günleri: 0=Pzt, 1=Sal, 2=Çar, 3=Per, 4=Cum
# Zaman dilimleri: her slot 2 saatlik blok
TIME_SLOTS = [
    (time(8, 0), time(10, 0)),
    (time(10, 0), time(12, 0)),
    (time(13, 0), time(15, 0)),
    (time(15, 0), time(17, 0)),
    (time(17, 0), time(19, 0)),
]

# Ders koduna göre sabit ama dağıtılmış gün/saat ataması.
# AKTS >= 4 → 2 saat bloğu, AKTS >= 6 → 3 blok.
def _pick_timeslot(code: str, credits: int):
    """Ders koduna göre deterministic gün/saat seç."""
    idx = sum(ord(c) for c in code) % (5 * len(TIME_SLOTS))
    day = idx % 5
    slot_idx = (idx // 5) % len(TIME_SLOTS)
    start, end = TIME_SLOTS[slot_idx]
    slots = [(day, start, end)]
    if credits >= 4:
        # İkinci blok farklı günde
        day2 = (day + 2) % 5
        slot2_idx = (slot_idx + 1) % len(TIME_SLOTS)
        s2, e2 = TIME_SLOTS[slot2_idx]
        slots.append((day2, s2, e2))
    if credits >= 6:
        day3 = (day + 4) % 5
        slot3_idx = (slot_idx + 2) % len(TIME_SLOTS)
        s3, e3 = TIME_SLOTS[slot3_idx]
        slots.append((day3, s3, e3))
    return slots


class Command(BaseCommand):
    help = "CourseOffering + CourseSection + SectionTimeSlot seed"

    def add_arguments(self, parser):
        parser.add_argument(
            "--academic-year",
            default="2025-2026",
            help="Akademik yıl (örn: 2025-2026)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        year = options["academic_year"]

        # ─── Semester'ları bul veya oluştur ──────────────────────────────
        fall_sem, _ = Semester.objects.get_or_create(
            academic_year=year,
            term=Semester.Term.FALL,
            defaults={
                "name": f"{year} Güz",
                "start_date": date(int(year[:4]), 9, 16),
                "end_date": date(int(year[:4]) + 1, 1, 31),
                "add_drop_start": date(int(year[:4]), 9, 16),
                "add_drop_end": date(int(year[:4]), 10, 15),
                "is_active": False,
            },
        )
        spring_sem, _ = Semester.objects.get_or_create(
            academic_year=year,
            term=Semester.Term.SPRING,
            defaults={
                "name": f"{year} Bahar",
                "start_date": date(int(year[:4]) + 1, 2, 10),
                "end_date": date(int(year[:4]) + 1, 6, 30),
                "add_drop_start": date(int(year[:4]) + 1, 2, 10),
                "add_drop_end": date(int(year[:4]) + 1, 3, 7),
                "is_active": True,
            },
        )

        self.stdout.write(f"Semester: {fall_sem} / {spring_sem}")

        # ─── Eğitim görevlisi ve derslik map'i ───────────────────────────
        instr_map = {}
        for username, profile in InstructorProfile.objects.select_related("user").values_list(
            "user__username", "pk"
        ):
            instr_map[username] = profile

        classroom_map = {}
        for cls in Classroom.objects.all():
            classroom_map[(cls.building, cls.room_number)] = cls

        # ─── Her CurriculumItem için offering oluştur ─────────────────────
        created_count = 0
        skipped_count = 0

        for ci in CurriculumItem.objects.select_related(
            "course", "program"
        ).prefetch_related("course__offerings"):

            course = ci.course
            sem = fall_sem if ci.term == "fall" else spring_sem

            # Instructor bul
            instr_username = COURSE_INSTRUCTOR.get(course.code)
            instr = None
            if instr_username:
                instr_pk = instr_map.get(instr_username)
                if instr_pk:
                    try:
                        instr = InstructorProfile.objects.get(pk=instr_pk)
                    except InstructorProfile.DoesNotExist:
                        pass

            # Classroom bul
            cls_key = COURSE_CLASSROOM.get(course.code)
            classroom = classroom_map.get(cls_key) if cls_key else None

            # Offering oluştur
            offering, o_created = CourseOffering.objects.get_or_create(
                course=course,
                semester=sem,
                section="A",
                defaults={
                    "instructor": instr,
                    "classroom": classroom,
                    "quota": 30,
                    "is_active": True,
                },
            )

            # Instructor ve classroom güncelle (zaten varsa)
            if not o_created:
                updated = False
                if instr and offering.instructor != instr:
                    offering.instructor = instr
                    updated = True
                if classroom and offering.classroom != classroom:
                    offering.classroom = classroom
                    updated = True
                if updated:
                    offering.save(update_fields=["instructor", "classroom"])

            # CourseSection oluştur
            section, s_created = CourseSection.objects.get_or_create(
                offering=offering,
                defaults={"max_enrollment": None},
            )

            # SectionTimeSlot oluştur (sadece yeni section için)
            if s_created:
                timeslots = _pick_timeslot(course.code, course.credits)
                for day, start, end in timeslots:
                    SectionTimeSlot.objects.get_or_create(
                        section=section,
                        weekday=day,
                        start_time=start,
                        defaults={"end_time": end},
                    )
                created_count += 1
            else:
                skipped_count += 1

            status = "OK" if o_created else "UPD"
            self.stdout.write(
                f"  {status} Offering: {course.code} — {sem.name} "
                f"(instr: {instr.user.last_name if instr else '-'}, "
                f"room: {classroom or '-'})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[OK] seed_real_data tamamlandı: "
                f"{created_count} yeni, {skipped_count} mevcut\n"
            )
        )
