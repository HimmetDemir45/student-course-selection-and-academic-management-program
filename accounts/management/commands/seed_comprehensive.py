"""
Kapsamlı seed komutu: Bölümler, dersler, akademisyenler, derslikler, curriculum.

ESM, YZM, OINS bölümleri ve 4 yıllık curriculum'ı oluşturur.
Her bölüme ait dersler, eğitim görevlileri ve ders saatleri tanımlanır.

Kullanım:
    python manage.py seed_comprehensive
    python manage.py seed_comprehensive --reset
"""

from __future__ import annotations

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from academic.models import (
    Department,
    Program,
    CurriculumItem,
    Semester,
    CourseSection,
)
from courses.models import Course, CourseOffering, Classroom
from instructors.models import InstructorProfile
from accounts.models import User


# Departments with their properties
DEPARTMENTS = [
    {"code": "ESM", "name": "Enerji Sistemleri Mühendisliği", "description": "ESM"},
    {"code": "YZM", "name": "Yazılım Mühendisliği", "description": "YZM"},
    {"code": "OINS", "name": "İnşaat Mühendisliği", "description": "OINS"},
]

# Programs for each department
PROGRAMS = [
    {"code": "ESM-LIS", "name": "Enerji Sistemleri Lisans", "dept": "ESM", "level": "BACHELOR"},
    {"code": "YZM-LIS", "name": "Yazılım Mühendisliği Lisans", "dept": "YZM", "level": "BACHELOR"},
    {"code": "OINS-LIS", "name": "İnşaat Mühendisliği Lisans", "dept": "OINS", "level": "BACHELOR"},
]

# Instructors with their details
INSTRUCTORS = [
    # ESM Instructors
    {"username": "prof_ismail_polat", "first": "Prof. Dr. İsmail", "last": "POLAT", "title": "Profesör", "dept": "ESM"},
    {"username": "prof_irfan_acar", "first": "Prof. Dr. İrfan", "last": "ACAR", "title": "Profesör", "dept": "ESM"},
    {"username": "prof_burcu_savaskam", "first": "Prof. Dr. Burcu", "last": "SAVAŞKAN", "title": "Profesör", "dept": "ESM"},
    {"username": "doc_esma_ulutas", "first": "Doç. Dr. Esma", "last": "ULUTAŞ", "title": "Doçent", "dept": "ESM"},
    {"username": "doc_nurullah_oksuz", "first": "Doç. Dr. Nurullah", "last": "ÖKSÜZER", "title": "Doçent", "dept": "ESM"},
    {"username": "dr_ozlem_fazlioglu", "first": "Dr. Özlem", "last": "FAZLIOĞLU", "title": "Doktor", "dept": "ESM"},
    {"username": "dr_haluk_keles", "first": "Dr. Öğr. Üyesi Haluk", "last": "KELEŞ", "title": "Yardımcı Doçent", "dept": "ESM"},
    {"username": "dr_omur_akyazi", "first": "Dr. Öğr. Üyesi Ömür", "last": "AKYAZI", "title": "Yardımcı Doçent", "dept": "ESM"},
    {"username": "dr_erhan_sesli", "first": "Dr. Öğr. Üyesi Erhan", "last": "SESLİ", "title": "Yardımcı Doçent", "dept": "ESM"},
    {"username": "ogr_gor_senol_demir", "first": "Öğr. Gör. Dr. Şenol", "last": "DEMİR", "title": "Öğretim Görevlisi", "dept": "ESM"},

    # YZM Instructors
    {"username": "dr_hamed_shamsi", "first": "Dr. Öğr. Üyesi Hamed", "last": "SHAMSİ", "title": "Yardımcı Doçent", "dept": "YZM"},
    {"username": "dr_coskun_bayram", "first": "Dr. Öğr. Üyesi Coşkun", "last": "BAYRAM", "title": "Yardımcı Doçent", "dept": "YZM"},
    {"username": "ogr_gor_bekir_sitki", "first": "Öğr. Gör. Bekir Sıtkı", "last": "ÖZGEN", "title": "Öğretim Görevlisi", "dept": "YZM"},

    # OINS Instructors
    {"username": "dr_muhammet_yazici", "first": "Dr. Öğr. Üyesi Muhammet", "last": "YAZICI", "title": "Yardımcı Doçent", "dept": "OINS"},
    {"username": "dr_tekmile_curebal", "first": "Dr. Tekmile", "last": "CÜREBAL", "title": "Doktor", "dept": "OINS"},
    {"username": "ogr_gor_aziz_asan", "first": "Öğr. Gör. Aziz", "last": "AŞAN", "title": "Öğretim Görevlisi", "dept": "OINS"},
    {"username": "ogr_gor_alper_kilic", "first": "Öğr. Gör. Alper", "last": "KILIÇOĞLU", "title": "Öğretim Görevlisi", "dept": "OINS"},
]

# Classrooms
CLASSROOMS = [
    {"building": "Enerji Blok", "room": "D1", "capacity": 60},
    {"building": "Enerji Blok", "room": "D2", "capacity": 50},
    {"building": "Enerji Blok", "room": "D3", "capacity": 40},
    {"building": "Enerji Blok", "room": "D5", "capacity": 35},
    {"building": "Bilgisayar Lab", "room": "YZM-DS", "capacity": 25},
    {"building": "Bilgisayar Lab", "room": "DOKAP", "capacity": 30},
    {"building": "İnşaat Blok", "room": "D1", "capacity": 70},
    {"building": "Prof. K. GELİŞLİ Sal.", "room": "Konferans", "capacity": 100},
    {"building": "Enerji Lab", "room": "Lab-1", "capacity": 15},
]

# ESM Courses (Enerji Sistemleri Mühendisliği)
ESM_COURSES = {
    1: {
        "fall": [
            ("AITB1003", "Atatürk İlkeleri ve İnkılap Tarihi - I", 2),
            ("TDB1005", "Türk Dili - I", 2),
            ("YDB1003", "İngilizce - I", 2),
            ("ESM1005", "Matematik - I", 5),
            ("ESM1011", "Fizik - I", 5),
            ("ESM1013", "Genel Kimya", 5),
            ("ESM1015", "Mühendislik Çizimi - I", 3),
            ("ESM1017", "Enerji Sistemleri Mühendisliğine Giriş", 2),
        ],
        "spring": [
            ("AITB1004", "Atatürk İlkeleri ve İnkılap Tarihi - II", 2),
            ("TDB1004", "Türk Dili - II", 2),
            ("YDB1004", "İngilizce - II", 2),
            ("ESM1002", "Lineer Cebir", 5),
            ("ESM1004", "Matematik - II", 5),
            ("ESM1012", "Fizik - II", 5),
            ("ESM1024", "Mühendislik Çizimi - II", 3),
            ("ESM1014", "İş Sağlığı ve Güvenliği - I", 2),
        ],
    },
    2: {
        "fall": [
            ("ESM2007", "Mekanik", 5),
            ("ESM2017", "Diferansiyel Denklemler", 5),
            ("ESM2037", "Ölçme Tekniği", 3),
            ("ESM2039", "Olasılık ve İstatistik", 4),
            ("ESM2041", "Devre Analizi - I", 3),
            ("ESM2043", "Girişimcilik ve Kariyer Planlaması", 2),
            ("ESM2013", "Elektronik - I", 4),
            ("ESM2023", "Termokimya", 4),
        ],
        "spring": [
            ("ESM2032", "Termodinamik - I", 4),
            ("ESM2034", "Elektronik", 3),
            ("ESM2036", "Devre Analizi - II", 3),
            ("ESM2038", "Sayısal Çözümleme", 4),
            ("ESM2040", "Enerji Yönetimi ve Politikaları", 4),
            ("ESM2054", "Mühendislik Matematiği", 4),
            ("ESM2002", "Araştırma Yöntem ve Teknikleri", 4),
            ("ESM2026", "Sunum ve Sunuş Teknikleri", 4),
        ],
    },
    3: {
        "fall": [
            ("ESM3041", "Güç Elektroniği", 4),
            ("ESM3043", "Güç Sistemlerine Giriş", 5),
            ("ESM3045", "Isı ve Kütle Transferi", 5),
            ("ESM3047", "Elektrik Makinaları", 5),
            ("ESM3049", "Termodinamik-II", 3),
            ("ESM3029", "Çevre Sorunları", 4),
            ("ESM3031", "Programlanabilir Lojik Kontrol", 4),
        ],
        "spring": [
            ("ESM3050", "Otomasyon Sistemleri", 4),
            ("ESM3052", "Akışkanlar Mekaniği", 4),
            ("ESM3054", "Mühendislik Tasarımı", 5),
            ("ESM3056", "Güç Sistemlerinde İletim ve Dağıtım", 5),
            ("ESM3058", "Sistem Dinamiği ve Kontrol", 4),
            ("ESM3038", "Isıtma, Havalandırma ve İklimlendirme", 4),
            ("ESM3028", "Yakıtlar ve Yanma", 4),
            ("ESM3044", "Nükleer Enerji", 4),
        ],
    },
    4: {
        "fall": [
            ("ESM4009", "Bitirme Çalışması", 6),
            ("ESM4011", "Enerji Laboratuarı", 3),
            ("ESM4013", "Enerji Mevzuatı ve Hukuku", 2),
            ("ESM4015", "Enerji Sistemlerinde Modelleme ve Analiz", 5),
            ("ESM4017", "Çok Disiplinli Mühendislik Uygulamaları", 2),
        ],
        "spring": [
            ("ESM4010", "Kombine Isı ve Güç Santralleri", 4),
            ("ESM4044", "Rüzgâr ve Güneş Enerji Sistemleri", 4),
            ("ESM4054", "Doğal Gaz Tesisatı", 4),
            ("ESM4030", "Elektrik Tesislerinde Güvenlik", 4),
        ],
    },
}

# YZM Courses (Yazılım Mühendisliği)
YZM_COURSES = {
    1: {
        "fall": [
            ("AITB1003", "Atatürk İlkeleri ve İnkılap Tarihi - I", 2),
            ("TDB1005", "Türk Dili - I", 2),
            ("YDB1003", "İngilizce - I", 2),
            ("YZM1005", "Matematik - I", 5),
            ("YZM1007", "Bilgisayarın Temelleri", 5),
            ("YZM1011", "Fizik - I", 5),
            ("YZM1013", "İş Sağlığı ve Güvenliği - I", 2),
            ("YZM1015", "Programlama - I", 5),
        ],
        "spring": [
            ("AITB1004", "Atatürk İlkeleri ve İnkılap Tarihi - II", 2),
            ("TDB1004", "Türk Dili - II", 2),
            ("YDB1004", "İngilizce - II", 2),
            ("YZM1002", "Lineer Cebir", 5),
            ("YZM1004", "Matematik - II", 5),
            ("YZM1012", "Fizik - II", 5),
            ("YZM1014", "İş Sağlığı ve Güvenliği - II", 2),
            ("YZM1016", "Programlama - II", 5),
        ],
    },
    2: {
        "fall": [
            ("YZM2005", "Diferansiyel Denklemler", 5),
            ("YZM2029", "Olasılık ve İstatistik", 4),
            ("YZM2031", "Nesne Yönelimli Programlama", 5),
            ("YZM2033", "Veri Tabanı ve Yönetimi", 4),
            ("YZM2035", "Akademik İngilizce", 4),
            ("YZM2025", "Bilimsel Proje Hazırlama", 4),
            ("YZM2015", "Mühendislik ve Bilişim Etiği", 4),
        ],
        "spring": [
            ("YZM2008", "Ayrık Matematik", 4),
            ("YZM2026", "Sayısal Çözümleme", 4),
            ("YZM2028", "Veri Yapıları", 5),
            ("YZM2030", "Algoritmalar", 5),
            ("YZM2032", "Mesleki İngilizce", 4),
            ("YZM2020", "Bilimsel Araştırma Yöntemleri", 4),
            ("YZM2006", "Sunum ve Sunuş Teknikleri", 4),
        ],
    },
    3: {
        "fall": [
            ("YZM3017", "Yazılım Tasarımı ve Mimarisi", 5),
            ("YZM3041", "Biçimsel Diller ve Otomata", 5),
            ("YZM3043", "İşletim Sistemleri", 5),
            ("YZM3057", "Mikroişlemciler", 5),
            ("YZM3013", "Betik Diller", 4),
            ("YZM3031", "Bilgi Güvenliği ve Kriptoloji", 4),
        ],
        "spring": [
            ("YZM3012", "Yapay Zekâ", 5),
            ("YZM3042", "Mühendislik Tasarımı", 5),
            ("YZM3044", "Yazılım Sınama ve Doğrulama", 5),
            ("YZM3046", "Bilgisayar Ağları", 5),
            ("YZM3024", "Mobil Programlama", 4),
            ("YZM3006", "Veri Tabanı Yönetim Sistemleri", 4),
        ],
    },
    4: {
        "fall": [
            ("YZM4009", "Bitirme Çalışması", 6),
            ("YZM4011", "Çok Disiplinli Mühendislik Uygulamaları", 2),
            ("YZM4013", "Girişimcilik ve Kariyer Planlaması", 2),
            ("YZM4015", "Yazılım Proje Yönetimi", 5),
        ],
        "spring": [
            ("YZM4008", "Veri Madenciliği", 4),
            ("YZM4032", "Meta - Sezgisel Optimizasyon", 4),
            ("YZM4038", "Derin Öğrenme", 4),
            ("YZM4034", "Siber Güvenlik ve Uygulamaları", 4),
        ],
    },
}

# OINS Courses (İnşaat Mühendisliği)
OINS_COURSES = {
    1: {
        "fall": [
            ("AITB1003", "Atatürk İlkeleri ve İnkılap Tarihi - I", 2),
            ("OINS1007", "İnşaat Mühendisliğine Giriş", 3),
            ("OINS1009", "Matematik - I", 5),
            ("OINS1011", "Genel Kimya", 5),
            ("OINS1013", "Mühendislik Çizimi", 6),
            ("OINS1015", "Fizik - I", 5),
            ("TDB1005", "Türk Dili - I", 2),
            ("YDB1003", "İngilizce - I", 2),
        ],
        "spring": [
            ("AITB1004", "Atatürk İlkeleri ve İnkılap Tarihi - II", 2),
            ("OINS1005", "Statik", 5),
            ("OINS1044", "İnşaat Jeolojisi", 4),
            ("OINS1008", "Matematik - II", 5),
            ("OINS1010", "Fizik - II", 5),
            ("OINS1012", "Olasılık ve İstatistik", 5),
            ("TDB1004", "Türk Dili - II", 2),
            ("YDB1004", "İngilizce - II", 2),
        ],
    },
    2: {
        "fall": [
            ("OINS2015", "Ölçme Bilgisi", 3),
            ("OINS2017", "Dinamik", 4),
            ("OINS2029", "Malzeme Bilimi", 3),
            ("OINS2035", "Mukavemet - I", 5),
            ("OINS2037", "Diferansiyel Denklemler", 5),
            ("OINS2039", "İş Sağlığı ve Güvenliği - I", 2),
            ("OINS2019", "İnşaat Makineleri", 4),
            ("OINS2027", "Bilgisayar Programlama", 4),
        ],
        "spring": [
            ("OINS2026", "Mukavemet - II", 5),
            ("OINS2040", "Yapı Malzemesi", 4),
            ("OINS2042", "Hidroloji", 3),
            ("OINS2044", "Mühendislik Matematiği", 4),
            ("OINS2046", "İş Sağlığı ve Güvenliği - II", 2),
            ("OINS2058", "Sayısal Çözümleme", 4),
            ("OINS2001", "Çevre Teknolojileri", 4),
            ("OINS2033", "Mesleki İngilizce - I", 4),
        ],
    },
    3: {
        "fall": [
            ("OINS3035", "Yapı Statiği - I", 4),
            ("OINS3037", "Akışkanlar Mekaniği", 4),
            ("OINS3039", "Zemin Mekaniği - I", 4),
            ("OINS3041", "Betonarme - I", 4),
            ("OINS3043", "Ulaşım - I", 4),
            ("OINS3045", "Girişimcilik ve Kariyer Planlama", 2),
            ("OINS3047", "Mesleki İngilizce", 4),
            ("OINS3011", "Tüneller", 4),
        ],
        "spring": [
            ("OINS3036", "Yapı Statiği - II", 4),
            ("OINS3038", "Hidrolik", 4),
            ("OINS3040", "Zemin Mekaniği - II", 4),
            ("OINS3042", "Betonarme - II", 4),
            ("OINS3044", "Ulaşım - II", 4),
            ("OINS3046", "Mühendislik Tasarımı", 3),
            ("OINS3048", "İnşaat Hukuku", 3),
            ("OINS3022", "Köprüler", 4),
        ],
    },
    4: {
        "fall": [
            ("OINS4009", "Bitirme Çalışması", 5),
            ("OINS4011", "Su Yapıları", 4),
            ("OINS4013", "Temel Mühendisliği", 4),
            ("OINS4015", "Çelik Yapılar", 4),
            ("OINS4017", "Şantiye Yönetimi", 3),
            ("OINS4019", "Çok Disiplinli Mühendislik Uygulamaları", 2),
        ],
        "spring": [
            ("OINS4036", "Deprem Mühendisliğine Giriş", 4),
            ("OINS4038", "Betonarmede Özel Konular", 4),
            ("OINS4024", "Denize Deşarj Yapıları", 4),
            ("OINS4010", "Betonarme Projelerin Bilgisayar Yardımıyla Çözümü", 4),
        ],
    },
}

# Course to Instructor mappings
COURSE_TO_INSTRUCTOR = {
    # ESM
    "ESM1004": "prof_ismail_polat",
    "ESM1011": "prof_ismail_polat",
    "ESM2032": "doc_esma_ulutas",
    "ESM2054": "doc_esma_ulutas",
    "ESM2041": "dr_hamed_shamsi",
    "ESM2036": "dr_hamed_shamsi",
    "ESM3043": "dr_omur_akyazi",
    "ESM3047": "dr_omur_akyazi",
    "ESM3056": "dr_omur_akyazi",
    "ESM4013": "prof_burcu_savaskam",
    "ESM3029": "prof_irfan_acar",
    "ESM3044": "prof_irfan_acar",
    "ESM4044": "prof_ismail_polat",
    "ESM3045": "dr_ozlem_fazlioglu",
    "ESM3038": "dr_ozlem_fazlioglu",
    "ESM4054": "dr_haluk_keles",
    "ESM3031": "dr_erhan_sesli",
    "ESM2023": "doc_esma_ulutas",
    "ESM2026": "doc_nurullah_oksuz",
    "ESM2002": "prof_burcu_savaskam",
    "ESM4030": "dr_omur_akyazi",
    # YZM
    "YZM1005": "ogr_gor_senol_demir",
    "YZM1004": "ogr_gor_senol_demir",
    "YZM2031": "dr_hamed_shamsi",
    "YZM2033": "dr_hamed_shamsi",
    "YZM1015": "dr_hamed_shamsi",
    "YZM1016": "dr_hamed_shamsi",
    "YZM1024": "dr_coskun_bayram",
    # OINS
    "OINS1009": "dr_muhammet_yazici",
    "OINS1008": "dr_muhammet_yazici",
}


class Command(BaseCommand):
    help = "ESM, YZM, OINS bölümleri ve derslerini seed'le"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Var olan bölüm ve dersleri sil ve yeniden oluştur",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Department.objects.filter(code__in=["ESM", "YZM", "OINS"]).delete()
            self.stdout.write(self.style.WARNING("[x] Eski bölümler silindi."))

        # Create departments
        dept_map = {}
        for dept_data in DEPARTMENTS:
            dept, created = Department.objects.get_or_create(
                code=dept_data["code"],
                defaults={"name": dept_data["name"], "description": dept_data["description"]},
            )
            dept_map[dept_data["code"]] = dept
            status = "OK" if created else "UPD"
            self.stdout.write(f"{status} Dept: {dept.code} - {dept.name}")

        # Create programs
        prog_map = {}
        for prog_data in PROGRAMS:
            dept = dept_map[prog_data["dept"]]
            level = Program.DegreeLevel.UNDERGRAD if prog_data["level"] == "BACHELOR" else Program.DegreeLevel.MASTER
            prog, created = Program.objects.get_or_create(
                code=prog_data["code"],
                defaults={
                    "department": dept,
                    "name": prog_data["name"],
                    "degree_level": level,
                },
            )
            prog_map[prog_data["code"]] = prog
            status = "OK" if created else "UPD"
            self.stdout.write(f"{status} Program: {prog.code} - {prog.name}")

        # Create instructors
        instr_map = {}
        for instr_data in INSTRUCTORS:
            user, created = User.objects.get_or_create(
                username=instr_data["username"],
                defaults={
                    "first_name": instr_data["first"],
                    "last_name": instr_data["last"],
                    "email": f"{instr_data['username']}@uni.test",
                    "role": User.Role.INSTRUCTOR,
                },
            )
            if created or not user.has_usable_password():
                user.set_password("DemoPass2026!")
                user.save()

            dept = dept_map[instr_data["dept"]]
            profile, created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "department": dept,
                    "title": instr_data["title"],
                    "is_approved": True,
                },
            )
            instr_map[instr_data["username"]] = profile
            status = "OK" if created else "UPD"
            self.stdout.write(f"{status} Instructor: {user.get_full_name()}")

        # Create classrooms
        for classroom_data in CLASSROOMS:
            classroom, created = Classroom.objects.get_or_create(
                building=classroom_data["building"],
                room_number=classroom_data["room"],
                defaults={"capacity": classroom_data["capacity"]},
            )
            status = "OK" if created else "UPD"
            self.stdout.write(f"{status} Classroom: {classroom.building} {classroom.room_number}")

        # Create courses and curriculum items for all programs
        self._create_courses_and_curriculum(
            "ESM-LIS", prog_map["ESM-LIS"], ESM_COURSES, instr_map
        )
        self._create_courses_and_curriculum(
            "YZM-LIS", prog_map["YZM-LIS"], YZM_COURSES, instr_map
        )
        self._create_courses_and_curriculum(
            "OINS-LIS", prog_map["OINS-LIS"], OINS_COURSES, instr_map
        )

        self.stdout.write(self.style.SUCCESS("\n[OK] Comprehensive seed tamamlandi!\n"))

    def _create_courses_and_curriculum(self, prog_code, program, courses_data, instr_map):
        """Create courses and curriculum items for a program"""
        for year, terms in courses_data.items():
            for term, courses in terms.items():
                for code, name, credits in courses:
                    course, created = Course.objects.get_or_create(
                        code=code,
                        defaults={
                            "department": program.department,
                            "program": program,
                            "name": name,
                            "credits": credits,
                        },
                    )

                    # Create curriculum item
                    term_enum = Semester.Term.FALL if term == "fall" else Semester.Term.SPRING
                    CurriculumItem.objects.get_or_create(
                        program=program,
                        course=course,
                        year_level=year,
                        term=term_enum,
                    )
