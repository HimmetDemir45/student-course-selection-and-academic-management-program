"""
Kapsamlı seed komutu: Bölümler, dersler, akademisyenler, derslikler, curriculum.

ESM, YZM, OINS bölümleri ve 4 yıllık curriculum'ı oluşturur.
Her bölüme ait dersler, eğitim görevlileri ve ders saatleri tanımlanır.

Kullanım:
    python manage.py seed_comprehensive
    python manage.py seed_comprehensive --reset
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from academic.models import (
    Department,
    Program,
    CurriculumItem,
    Semester,
)
from courses.models import Course, CourseOffering, Classroom, ElectivePool
from instructors.models import InstructorProfile
from accounts.models import User


DEPARTMENTS = [
    {"code": "ESM", "name": "Enerji Sistemleri Mühendisliği", "description": "ESM"},
    {"code": "YZM", "name": "Yazılım Mühendisliği", "description": "YZM"},
    {"code": "OINS", "name": "İnşaat Mühendisliği", "description": "OINS"},
    {"code": "UZEM", "name": "Uzaktan Eğitim Merkezi", "description": "Üniversite ortak dersleri"},
]

PROGRAMS = [
    {"code": "ESM-LIS", "name": "Enerji Sistemleri Lisans", "dept": "ESM", "level": "BACHELOR"},
    {"code": "YZM-LIS", "name": "Yazılım Mühendisliği Lisans", "dept": "YZM", "level": "BACHELOR"},
    {"code": "OINS-LIS", "name": "İnşaat Mühendisliği Lisans", "dept": "OINS", "level": "BACHELOR"},
]

INSTRUCTORS = [
    # ESM
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
    # YZM+ESM (ESM derslerini de öğrettiği için multi-dept)
    {"username": "dr_hamed_shamsi", "first": "Dr. Öğr. Üyesi Hamed", "last": "SHAMSİ", "title": "Yardımcı Doçent", "dept": "ESM"},
    {"username": "dr_coskun_bayram", "first": "Dr. Öğr. Üyesi Coşkun", "last": "BAYRAM", "title": "Yardımcı Doçent", "dept": "YZM"},
    {"username": "ogr_gor_bekir_sitki", "first": "Öğr. Gör. Bekir Sıtkı", "last": "ÖZGEN", "title": "Öğretim Görevlisi", "dept": "YZM"},
    # OINS
    {"username": "dr_muhammet_yazici", "first": "Dr. Öğr. Üyesi Muhammet", "last": "YAZICI", "title": "Yardımcı Doçent", "dept": "OINS"},
    {"username": "dr_tekmile_curebal", "first": "Dr. Tekmile", "last": "CÜREBAL", "title": "Doktor", "dept": "OINS"},
    {"username": "ogr_gor_aziz_asan", "first": "Öğr. Gör. Aziz", "last": "AŞAN", "title": "Öğretim Görevlisi", "dept": "OINS"},
    {"username": "ogr_gor_alper_kilic", "first": "Öğr. Gör. Alper", "last": "KILIÇOĞLU", "title": "Öğretim Görevlisi", "dept": "OINS"},
]

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

# ─── ESM COURSES ────────────────────────────────────────────────────────────
# Format: (code, name, credits)
# Seçmeli havuz dersleri de dahil; CurriculumItem ile ilişkilendirilir.

ESM_COURSES = {
    1: {
        "fall": [
            ("AITB1003", "Atatürk İlkeleri ve İnkılap Tarihi - I", 2),
            ("ESM1003", "Matematik - I", 5),
            ("ESM1005", "Fizik - I", 5),
            ("ESM1011", "Genel Kimya", 5),
            ("ESM1013", "Mühendislik Çizimi - I", 5),
            ("ESM1015", "Enerji Sistemleri Mühendisliğine Giriş", 2),
            ("ESM1017", "İş Sağlığı ve Güvenliği - I", 2),
            ("TDB1005", "Türk Dili - I", 2),
            ("YDB1003", "İngilizce - I", 2),
        ],
        "spring": [
            ("AITB1004", "Atatürk İlkeleri ve İnkılap Tarihi - II", 2),
            ("ESM1000", "Matematik - II", 5),
            ("ESM1004", "Fizik - II", 5),
            ("ESM1010", "Bilgisayar Programlama", 3),
            ("ESM1012", "Mühendislik Çizimi - II", 4),
            ("ESM1014", "Lineer Cebir", 5),
            ("ESM1016", "İş Sağlığı ve Güvenliği - II", 2),
            ("TDB1004", "Türk Dili - II", 2),
            ("YDB1004", "İngilizce - II", 2),
        ],
    },
    2: {
        "fall": [
            # Zorunlu dersler
            ("ESM2007", "Mekanik", 5),
            ("ESM2017", "Diferansiyel Denklemler", 5),
            ("ESM2037", "Ölçme Tekniği", 3),
            ("ESM2039", "Olasılık ve İstatistik", 4),
            ("ESM2041", "Devre Analizi - I", 3),
            ("ESM2043", "Girişimcilik ve Kariyer Planlaması", 2),
            # Sosyal Seçmeli Havuz - I (öğrenci 1 seçer, 4 AKTS)
            ("ESM2013", "Elektronik - I", 4),
            ("ESM2023", "Termokimya", 4),
            ("USEC0003", "Meslek Etiği", 4),
        ],
        "spring": [
            # Zorunlu dersler
            ("ESM2032", "Termodinamik - I", 4),
            ("ESM2034", "Elektronik", 3),
            ("ESM2036", "Devre Analizi - II", 3),
            ("ESM2038", "Sayısal Çözümleme", 4),
            ("ESM2040", "Enerji Yönetimi ve Politikaları", 4),
            ("ESM2054", "Mühendislik Matematiği", 4),
            # Teknik Seçmeli / Sosyal Seçmeli Havuz
            ("ESM2002", "Araştırma Yöntem ve Teknikleri", 4),
            ("YDI2008", "İngilizce Konuşma", 4),
            ("USEC0008", "Kişisel Verilerin Korunması", 4),
            ("ESM2026", "Sunum ve Sunuş Teknikleri", 4),
            ("USEC0044", "Girişimcilik", 4),
        ],
    },
    3: {
        "fall": [
            # Zorunlu dersler
            ("ESM3041", "Güç Elektroniği", 4),
            ("ESM3043", "Güç Sistemlerine Giriş", 5),
            ("ESM3045", "Isı ve Kütle Transferi", 5),
            ("ESM3047", "Elektrik Makinaları", 5),
            ("ESM3049", "Termodinamik-II", 3),
            # Teknik Seçmeli Havuz - II
            ("ESM3029", "Çevre Sorunları", 4),
            ("ESM3031", "Programlanabilir Lojik Kontrol", 4),
            # Sosyal Seçmeli Havuz - IV
            ("USEC0005", "Genel Sosyoloji", 4),
        ],
        "spring": [
            # Zorunlu dersler
            ("ESM3050", "Otomasyon Sistemleri", 4),
            ("ESM3052", "Akışkanlar Mekaniği", 4),
            ("ESM3054", "Mühendislik Tasarımı", 5),
            ("ESM3056", "Güç Sistemlerinde İletim ve Dağıtım", 5),
            ("ESM3058", "Sistem Dinamiği ve Kontrol", 4),
            # Teknik Seçmeli Havuz - III ve IV
            ("ESM3038", "Isıtma, Havalandırma ve İklimlendirme", 4),
            ("ESM3028", "Yakıtlar ve Yanma", 4),
            ("ESM3044", "Nükleer Enerji", 4),
            ("ESM3048", "Lojik Devreler", 4),
        ],
    },
    4: {
        "fall": [
            ("ESM4009", "Bitirme Çalışması", 6),
            ("ESM4011", "Enerji Laboratuarı", 3),
            ("ESM4013", "Enerji Mevzuatı ve Hukuku", 2),
            ("ESM4015", "Enerji Sistemlerinde Modelleme ve Analiz", 5),
            ("ESM4017", "Çok Disiplinli Mühendislik Uygulamaları", 2),
            # Teknik Seçmeli Havuz - V, VI, VII
            ("ESM4010", "Kombine Isı ve Güç Santralleri", 4),
            ("ESM4044", "Rüzgâr ve Güneş Enerji Sistemleri", 4),
            ("ESM4054", "Doğal Gaz Tesisatı", 4),
            ("ESM4030", "Elektrik Tesislerinde Güvenlik", 4),
        ],
        "spring": [
            ("ESM4064", "İş Yeri Eğitimi", 24),
            ("ESM4066", "Mesleki Deneyim - I", 3),
            ("ESM4068", "Mesleki Deneyim - II", 3),
            # Bahar Seçmeli Havuz
            ("USEC0018", "İş Sağlığı ve Güvenliği", 4),
            ("USEC0012", "Kariyer Planlama", 4),
        ],
    },
}

# Elective pools for ESM
ESM_ELECTIVE_POOLS = [
    {
        "name": "Sosyal Seçmeli I/II (2. Sınıf Güz)", "year": 2, "term": "fall",
        "required": 2, "courses": ["ESM2013", "ESM2023", "USEC0003"],
    },
    {
        "name": "Teknik/Sosyal Seçmeli (2. Sınıf Bahar)", "year": 2, "term": "spring",
        "required": 2, "courses": ["ESM2002", "YDI2008", "USEC0008", "ESM2026", "USEC0044"],
    },
    {
        "name": "Teknik Seçmeli II (3. Sınıf Güz)", "year": 3, "term": "fall",
        "required": 1, "courses": ["ESM3029", "ESM3031"],
    },
    {
        "name": "Teknik Seçmeli III/IV (3. Sınıf Bahar)", "year": 3, "term": "spring",
        "required": 2, "courses": ["ESM3038", "ESM3028", "ESM3044", "ESM3048"],
    },
    {
        "name": "Teknik Seçmeli V/VI/VII (4. Sınıf Güz)", "year": 4, "term": "fall",
        "required": 3, "courses": ["ESM4010", "ESM4044", "ESM4054", "ESM4030"],
    },
    {
        "name": "Bahar Seçmeli (4. Sınıf Bahar)", "year": 4, "term": "spring",
        "required": 2, "courses": ["USEC0018", "USEC0012"],
    },
]

# ─── YZM COURSES ────────────────────────────────────────────────────────────

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
            ("YZM1017", "Yazılım Mühendisliğine Giriş", 2),
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
            ("YZM1018", "Yazılım Gereksinim Mühendisliği", 2),
        ],
    },
    2: {
        "fall": [
            # Zorunlu
            ("YZM2005", "Diferansiyel Denklemler", 5),
            ("YZM2029", "Olasılık ve İstatistik", 4),
            ("YZM2031", "Nesne Yönelimli Programlama", 5),
            ("YZM2033", "Veri Tabanı ve Yönetimi", 4),
            ("YZM2035", "Akademik İngilizce", 4),
            # Sosyal Seçmeli Havuz I/II
            ("YZM2025", "Bilimsel Proje Hazırlama", 4),
            ("USEC0005", "Genel Sosyoloji", 4),
            ("YZM2015", "Mühendislik ve Bilişim Etiği", 4),
            ("USEC0035", "Kalite Okuryazarlığı", 4),
        ],
        "spring": [
            # Zorunlu
            ("YZM2008", "Ayrık Matematik", 4),
            ("YZM2026", "Sayısal Çözümleme", 4),
            ("YZM2028", "Veri Yapıları", 5),
            ("YZM2030", "Algoritmalar", 5),
            ("YZM2032", "Mesleki İngilizce", 4),
            # Sosyal Seçmeli Havuz III/IV
            ("USEC0004", "Meslek Etiği", 4),
            ("YZM2020", "Bilimsel Araştırma Yöntemleri", 4),
            ("USEC0002", "Bilim Tarihi", 4),
            ("YZM2006", "Sunum ve Sunuş Teknikleri", 4),
            ("USEC0012", "Kariyer Planlama", 4),
        ],
    },
    3: {
        "fall": [
            # Zorunlu
            ("YZM3017", "Yazılım Tasarımı ve Mimarisi", 5),
            ("YZM3041", "Biçimsel Diller ve Otomata", 5),
            ("YZM3043", "İşletim Sistemleri", 5),
            ("YZM3057", "Mikroişlemciler", 5),
            # Teknik Seçmeli Havuz I/II
            ("YZM3013", "Betik Diller", 4),
            ("YZM3031", "Bilgi Güvenliği ve Kriptoloji", 4),
            ("YZM3033", "Programlama Dili Kavramları", 4),
        ],
        "spring": [
            # Zorunlu
            ("YZM3012", "Yapay Zekâ", 5),
            ("YZM3042", "Mühendislik Tasarımı", 5),
            ("YZM3044", "Yazılım Sınama ve Doğrulama", 5),
            ("YZM3046", "Bilgisayar Ağları", 5),
            # Teknik Seçmeli Havuz III/IV
            ("YZM3024", "Mobil Programlama", 4),
            ("YZM3006", "Veri Tabanı Yönetim Sistemleri", 4),
            ("YZM3028", "Gömülü Sistemler", 4),
            ("YZM3034", "Optimizasyon Teorisi", 4),
        ],
    },
    4: {
        "fall": [
            ("YZM4009", "Bitirme Çalışması", 6),
            ("YZM4011", "Çok Disiplinli Mühendislik Uygulamaları", 2),
            ("YZM4013", "Girişimcilik ve Kariyer Planlaması", 2),
            ("YZM4015", "Yazılım Proje Yönetimi", 5),
            # Teknik Seçmeli Havuz V/VI/VII
            ("YZM4008", "Veri Madenciliği", 4),
            ("YZM4032", "Meta-Sezgisel Optimizasyon", 4),
            ("YZM4038", "Derin Öğrenme", 4),
            ("YZM4034", "Siber Güvenlik ve Uygulamaları", 4),
        ],
        "spring": [
            ("YZM4044", "İş Yeri Eğitimi", 24),
            ("YZM4046", "Mesleki Deneyim - I", 3),
            ("YZM4048", "Mesleki Deneyim - II", 3),
        ],
    },
}

YZM_ELECTIVE_POOLS = [
    {
        "name": "Sosyal Seçmeli I/II (2. Sınıf Güz)", "year": 2, "term": "fall",
        "required": 2, "courses": ["YZM2025", "USEC0005", "YZM2015", "USEC0035"],
    },
    {
        "name": "Sosyal Seçmeli III/IV (2. Sınıf Bahar)", "year": 2, "term": "spring",
        "required": 2, "courses": ["USEC0004", "YZM2020", "USEC0002", "YZM2006", "USEC0012"],
    },
    {
        "name": "Teknik Seçmeli I/II (3. Sınıf Güz)", "year": 3, "term": "fall",
        "required": 2, "courses": ["YZM3013", "YZM3031", "YZM3033"],
    },
    {
        "name": "Teknik Seçmeli III/IV (3. Sınıf Bahar)", "year": 3, "term": "spring",
        "required": 2, "courses": ["YZM3024", "YZM3006", "YZM3028", "YZM3034"],
    },
    {
        "name": "Teknik Seçmeli V/VI/VII (4. Sınıf Güz)", "year": 4, "term": "fall",
        "required": 3, "courses": ["YZM4008", "YZM4032", "YZM4038", "YZM4034"],
    },
]

# ─── OINS COURSES ───────────────────────────────────────────────────────────

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
            # Zorunlu
            ("OINS2015", "Ölçme Bilgisi", 3),
            ("OINS2017", "Dinamik", 4),
            ("OINS2029", "Malzeme Bilimi", 3),
            ("OINS2035", "Mukavemet - I", 5),
            ("OINS2037", "Diferansiyel Denklemler", 5),
            ("OINS2039", "İş Sağlığı ve Güvenliği - I", 2),
            # Havuz 1/2
            ("OINS2019", "İnşaat Makineleri", 4),
            ("OINS2027", "Bilgisayar Programlama", 4),
            ("OINS2001", "Çevre Teknolojileri", 4),
            ("OINS2033", "Mesleki İngilizce - I", 4),
            ("USEC0005", "Genel Sosyoloji", 4),
        ],
        "spring": [
            # Zorunlu
            ("OINS2026", "Mukavemet - II", 5),
            ("OINS2040", "Yapı Malzemesi", 4),
            ("OINS2042", "Hidroloji", 3),
            ("OINS2044", "Mühendislik Matematiği", 4),
            ("OINS2046", "İş Sağlığı ve Güvenliği - II", 2),
            ("OINS2058", "Sayısal Çözümleme", 4),
            # Havuz 3/4
            ("USEC0014", "Teknoloji Bağımlılığı", 4),
            ("USEC0038", "Gönüllülük Çalışmaları", 4),
            ("USEC0016", "Project Management", 4),
            ("OINS2002", "Mühendislik Matematiği (Seçmeli)", 4),
            ("OINS2034", "Sayısal Analiz", 4),
            ("OINS2014", "Girişimcilik", 4),
            ("OINS2016", "Sunum ve Sunuş Teknikleri", 4),
            ("OINS2018", "Mimarlık Bilgisi", 4),
            ("USEC0002", "Bilim Tarihi", 4),
        ],
    },
    3: {
        "fall": [
            # Zorunlu
            ("OINS3035", "Yapı Statiği - I", 4),
            ("OINS3037", "Akışkanlar Mekaniği", 4),
            ("OINS3039", "Zemin Mekaniği - I", 4),
            ("OINS3041", "Betonarme - I", 4),
            ("OINS3043", "Ulaşım - I", 4),
            ("OINS3045", "Girişimcilik ve Kariyer Planlama", 2),
            ("OINS3047", "Mesleki İngilizce", 4),
            # Havuz 5
            ("OINS3011", "Tüneller", 4),
            ("OINS3023", "Yol Üst Yapısı", 4),
            ("OINS3029", "Beton Teknolojileri", 4),
            ("OINS3015", "Yapı Dinamiği", 4),
        ],
        "spring": [
            # Zorunlu
            ("OINS3036", "Yapı Statiği - II", 4),
            ("OINS3038", "Hidrolik", 4),
            ("OINS3040", "Zemin Mekaniği - II", 4),
            ("OINS3042", "Betonarme - II", 4),
            ("OINS3044", "Ulaşım - II", 4),
            ("OINS3046", "Mühendislik Tasarımı", 3),
            ("OINS3048", "İnşaat Hukuku", 3),
            # Havuz 6
            ("OINS3002", "Yapı Mühendisliği Bilgisayar Uygulamaları", 4),
            ("OINS3022", "Köprüler", 4),
            ("OINS3028", "Demiryolu", 4),
            ("USEC0010", "Proje Yönetimi", 4),
            ("OINS3030", "İş Güvenliği", 4),
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
            # Havuz 7/8
            ("OINS4036", "Deprem Mühendisliğine Giriş", 4),
            ("OINS4038", "Betonarmede Özel Konular", 4),
            ("OINS4024", "Denize Deşarj Yapıları", 4),
            ("USEC0012", "Kariyer Planlama", 4),
            ("OINS4010", "Betonarme Projelerin Bilgisayar Yardımıyla Çözümü", 4),
            ("OINS4016", "Ulaşım Politikaları", 4),
        ],
        "spring": [
            ("OINS4040", "İş Yeri Eğitimi", 20),
            ("OINS4042", "Mesleki Deneyim - I", 5),
            ("OINS4044", "Mesleki Deneyim - II", 5),
        ],
    },
}

OINS_ELECTIVE_POOLS = [
    {
        "name": "Havuz 1/2 (2. Sınıf Güz)", "year": 2, "term": "fall",
        "required": 2, "courses": ["OINS2019", "OINS2027", "OINS2001", "OINS2033", "USEC0005"],
    },
    {
        "name": "Havuz 3/4 (2. Sınıf Bahar)", "year": 2, "term": "spring",
        "required": 2,
        "courses": ["USEC0014", "USEC0038", "USEC0016", "OINS2002", "OINS2034",
                    "OINS2014", "OINS2016", "OINS2018", "USEC0002"],
    },
    {
        "name": "Havuz 5 (3. Sınıf Güz)", "year": 3, "term": "fall",
        "required": 1, "courses": ["OINS3011", "OINS3023", "OINS3029", "OINS3015"],
    },
    {
        "name": "Havuz 6 (3. Sınıf Bahar)", "year": 3, "term": "spring",
        "required": 1, "courses": ["OINS3002", "OINS3022", "OINS3028", "USEC0010", "OINS3030"],
    },
    {
        "name": "Havuz 7/8 (4. Sınıf Güz)", "year": 4, "term": "fall",
        "required": 2,
        "courses": ["OINS4036", "OINS4038", "OINS4024", "USEC0012", "OINS4010", "OINS4016"],
    },
]

# ─── COURSE → INSTRUCTOR EŞLEŞTİRMELERİ ────────────────────────────────────

COURSE_TO_INSTRUCTOR = {
    # ESM 1. Sınıf Bahar
    "ESM1000": "ogr_gor_senol_demir",   # Matematik - II
    "ESM1004": "prof_ismail_polat",      # Fizik - II
    "ESM1003": "ogr_gor_senol_demir",   # Matematik - I (Güz)
    "ESM1005": "prof_ismail_polat",      # Fizik - I (Güz)
    "ESM1010": "dr_hamed_shamsi",        # Bilgisayar Programlama
    "ESM1012": "dr_coskun_bayram",       # Mühendislik Çizimi - II
    "ESM1016": "dr_tekmile_curebal",    # İş Sağlığı ve Güvenliği - II
    "YDB1004": "ogr_gor_bekir_sitki",   # İngilizce - II
    "YDB1003": "ogr_gor_bekir_sitki",   # İngilizce - I
    # ESM 2. Sınıf
    "ESM2038": "doc_esma_ulutas",        # Sayısal Çözümleme
    "ESM2032": "dr_coskun_bayram",       # Termodinamik - I
    "ESM2026": "doc_nurullah_oksuz",     # Sunum ve Sunuş Teknikleri
    "ESM2002": "prof_burcu_savaskam",    # Araştırma Yöntem ve Teknikleri
    "ESM2041": "dr_hamed_shamsi",        # Devre Analizi - I
    "ESM2036": "dr_hamed_shamsi",        # Devre Analizi - II
    "ESM2054": "doc_esma_ulutas",        # Mühendislik Matematiği
    "ESM2023": "doc_esma_ulutas",        # Termokimya
    # ESM 3. Sınıf
    "ESM3043": "dr_omur_akyazi",         # Güç Sistemlerine Giriş
    "ESM3047": "dr_omur_akyazi",         # Elektrik Makinaları
    "ESM3056": "dr_omur_akyazi",         # Güç Sistemlerinde İletim ve Dağıtım
    "ESM3044": "prof_irfan_acar",        # Nükleer Enerji
    "ESM3048": "dr_erhan_sesli",         # Lojik Devreler
    "ESM3045": "dr_ozlem_fazlioglu",     # Isı ve Kütle Transferi
    "ESM3038": "dr_ozlem_fazlioglu",     # Isıtma, Havalandırma ve İklimlendirme
    "ESM3029": "prof_irfan_acar",        # Çevre Sorunları
    "ESM3031": "dr_erhan_sesli",         # Programlanabilir Lojik Kontrol
    # ESM 4. Sınıf
    "ESM4013": "prof_burcu_savaskam",    # Enerji Mevzuatı ve Hukuku
    "ESM4044": "prof_ismail_polat",      # Rüzgâr ve Güneş Enerji Sistemleri
    "ESM4054": "dr_haluk_keles",         # Doğal Gaz Tesisatı
    "ESM4010": "dr_haluk_keles",         # Kombine Isı ve Güç Santralleri
    "ESM4030": "dr_omur_akyazi",         # Elektrik Tesislerinde Güvenlik
    "ESM4011": "prof_ismail_polat",      # Enerji Laboratuarı (lab - birden fazla)
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

# ─── CLASSROOM → COURSE EŞLEŞTİRMELERİ (Bahar Dönemi) ─────────────────────
# Yalnızca CourseOffering güncellemesinde kullanılır

COURSE_TO_CLASSROOM = {
    # ESM-D1
    "ESM1004": ("Enerji Blok", "D1"),   # Fizik-II
    "YDB1004": ("Enerji Blok", "D1"),   # İngilizce-II
    "ESM1014": ("Enerji Blok", "D1"),   # Lineer Cebir
    "YDI2008": ("Enerji Blok", "D1"),   # İngilizce Konuşma
    "ESM4013": ("Enerji Blok", "D1"),   # Enerji Mevzuatı
    "ESM4044": ("Enerji Blok", "D1"),   # Rüzgâr ve Güneş
    "ESM4054": ("Enerji Blok", "D1"),   # Doğal Gaz Tesisatı
    "ESM4010": ("Enerji Blok", "D1"),   # Kombine Isı ve Güç
    # ESM-D2
    "ESM2038": ("Enerji Blok", "D2"),   # Sayısal Çözümleme
    "ESM2032": ("Enerji Blok", "D2"),   # Termodinamik-I
    "ESM2002": ("Enerji Blok", "D2"),   # Araştırma Yöntemleri
    "ESM2041": ("Enerji Blok", "D2"),   # Devre Analizi-I
    "ESM2054": ("Enerji Blok", "D2"),   # Mühendislik Matematiği
    # ESM-D3
    "ESM3044": ("Enerji Blok", "D3"),   # Nükleer Enerji
    "ESM3047": ("Enerji Blok", "D3"),   # Elektrik Makinaları
    "ESM3043": ("Enerji Blok", "D3"),   # Güç Sistemlerine Giriş
    "ESM3056": ("Enerji Blok", "D3"),   # Güç Sistemleri İletim
    "ESM4030": ("Enerji Blok", "D3"),   # Elektrik Tesislerinde Güvenlik
    # ESM-D5
    "ESM3038": ("Enerji Blok", "D5"),   # Isıtma, Havalandırma
    # Bilgisayar Lab DOKAP
    "ESM1010": ("Bilgisayar Lab", "DOKAP"),  # Bilgisayar Programlama
    "ESM1012": ("Bilgisayar Lab", "DOKAP"),  # Mühendislik Çizimi-II
    "ESM3048": ("Bilgisayar Lab", "DOKAP"),  # Lojik Devreler
    # İnşaat D1
    "ESM1000": ("İnşaat Blok", "D1"),   # Matematik-II
    # Konferans Salonu
    "ESM1016": ("Prof. K. GELİŞLİ Sal.", "Konferans"),   # İş Sağlığı Güvenliği
    "ESM2026": ("Prof. K. GELİŞLİ Sal.", "Konferans"),   # Sunum ve Sunuş Tek.
    # Enerji Laboratuvarı
    "ESM4011": ("Enerji Lab", "Lab-1"),  # Enerji Laboratuvarı
}


# ─── SEÇMELİ DERS AÇIKLAMALARI ──────────────────────────────────────────────

COURSE_DESCRIPTIONS = {
    # Ortak seçmeli (USEC)
    "USEC0002": "Bilimin tarihsel gelişimi, bilimsel yöntem ve paradigma değişimleri üzerine kapsamlı bir inceleme.",
    "USEC0003": "Mesleki yaşamda etik ilkeler, karar alma süreçleri ve etik ikilemi çözme yöntemleri.",
    "USEC0004": "İş ve mesleki yaşamda etik sorunlar, örnek vakalar üzerinden etik düşünme pratiği.",
    "USEC0005": "Toplumsal yapı, kurumlar ve sosyal ilişkileri inceleyen temel sosyoloji kavramları.",
    "USEC0008": "KVKK kapsamında kişisel veri işleme ilkeleri, haklar ve kurumsal uyum gereklilikleri.",
    "USEC0010": "Proje planlama, kaynak yönetimi, risk analizi ve proje yaşam döngüsü yönetimi.",
    "USEC0012": "Kariyer hedefleri belirleme, CV hazırlama, mülakat teknikleri ve iş arama stratejileri.",
    "USEC0014": "Dijital teknoloji kullanım alışkanlıkları, bağımlılık belirtileri ve sağlıklı teknoloji kullanımı.",
    "USEC0016": "İngilizce ortamda proje yönetimi kavramları, proje döngüsü ve ekip koordinasyonu.",
    "USEC0018": "İş yerinde sağlık ve güvenlik mevzuatı, risk değerlendirme ve kaza önleme yöntemleri.",
    "USEC0035": "Kalite yönetim sistemleri, ISO standartları ve veri okur-yazarlığı temel kavramları.",
    "USEC0038": "Toplumsal duyarlılık projeleri, sivil toplum kuruluşları ile gönüllü çalışma deneyimi.",
    "USEC0044": "Girişimcilik ekosistemi, iş fikri geliştirme, iş planı hazırlama ve finansman kaynakları.",
    # YZM seçmeli dersler
    "YZM2006": "Yazılım geliştirme süreçlerinde kalite güvencesi, test stratejileri ve otomasyon araçları.",
    "YZM2015": "Karmaşık sistemlerde matematiksel modelleme, optimizasyon ve sayısal analiz teknikleri.",
    "YZM2020": "Veri tabanı tasarımı, SQL ve NoSQL sistemleri, veri modelleme ve sorgulama ileri konuları.",
    "YZM2025": "Yazılım mimarisi kalıpları, dağıtık sistemler ve büyük ölçekli sistem tasarım prensipleri.",
    "YZM3028": "Yapay zeka temel algoritmaları, makine öğrenimi modelleri ve uygulama alanları.",
    "YZM3033": "Programlama dili paradigmaları, sözdizimi analizi ve dil tasarım ilkeleri.",
    "YZM3034": "Mobil uygulama geliştirme süreçleri, iOS/Android platformları ve kullanıcı deneyimi tasarımı.",
    # ESM seçmeli dersler
    "ESM2013": "Enerji çevrimi ve enerji kaynaklarının termodinamik analizi, enerji verimliliği ilkeleri.",
    "ESM2023": "Kimyasal reaksiyonlarda ısı ve enerji dengesi, endüstriyel termokimya uygulamaları.",
    "ESM3044": "Nükleer fisyon ve füzyon, reaktör tasarımı ve nükleer enerji santralleri işletimi.",
    "ESM3048": "Kombinasyonel ve ardışık lojik devre tasarımı, sayısal elektronik ve FPGA uygulamaları.",
    # OINS seçmeli dersler
    "OINS2001": "İnşaat malzemelerinin mekanik özellikleri, beton, çelik ve ahşap yapı malzemeleri.",
    "OINS2002": "Zemin mekaniği ilkeleri, temel mühendisliği ve zemin araştırma yöntemleri.",
    "OINS2014": "Yapı statik analizi, yük dağılımları ve basit yapı sistemlerinin hesabı.",
    "OINS2016": "İnşaat proje yönetimi, maliyet tahmini, program yapımı ve sözleşme yönetimi.",
    "OINS2018": "Çevre mühendisliği temelleri, atık su arıtma ve çevresel etki değerlendirmesi.",
    "OINS2019": "Yapı malzemeleri ve tekniklerinin genel tanıtımı, temel inşaat uygulamaları.",
    "OINS2027": "Mühendislik çizim teknikleri, CAD programları ve teknik belgeleme standartları.",
    "OINS2033": "Beton teknolojisi, karışım tasarımı ve beton kalite kontrol yöntemleri.",
    "OINS2034": "Ulaştırma mühendisliği temel kavramları, yol geometrisi ve trafik akışı.",
    "OINS3002": "Köprü, tünel ve viyadük tasarımı; altyapı yapılarının mühendislik ilkeleri.",
    "OINS3022": "Betonarme yapı elemanlarının tasarımı ve hesabı, TS500 ve Eurocode kapsamında.",
    "OINS3028": "Deprem mühendisliği, yük analizi ve yapıların deprem performans değerlendirmesi.",
    "OINS3030": "Su kaynakları planlaması, sulama sistemleri ve hidrolik yapı tasarımı.",
    "OINS4010": "İnşaat sektöründe araştırma metodolojisi, veri analizi ve akademik yazım.",
    "OINS4016": "Çelik yapı sistemleri, birleşim detayları ve hafif çelik konstrüksiyonlar.",
    "OINS4024": "Akıllı ulaşım sistemleri, trafik simülasyonu ve kentsel hareketlilik çözümleri.",
    "OINS4036": "Yapı proje yönetiminde ileri konular, risk analizi ve BIM teknolojileri.",
    "OINS4038": "Kentsel dönüşüm projeleri, yapı güçlendirme ve yıkım mühendisliği.",
    # Diğer seçmeli dersler
    "YDI2008": "Akademik ve mesleki İngilizce konuşma becerileri, sunum ve tartışma pratiği.",
}


class Command(BaseCommand):
    help = "ESM, YZM, OINS bölümleri ve derslerini seed'le (update_or_create)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Var olan bölüm ve dersleri sil ve yeniden oluştur",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Department.objects.filter(code__in=["ESM", "YZM", "OINS", "UZEM"]).delete()
            self.stdout.write(self.style.WARNING("[x] Eski bölümler silindi."))

        # Departments
        dept_map = {}
        for dept_data in DEPARTMENTS:
            dept, created = Department.objects.get_or_create(
                code=dept_data["code"],
                defaults={"name": dept_data["name"], "description": dept_data["description"]},
            )
            if not created:
                dept.name = dept_data["name"]
                dept.save(update_fields=["name"])
            dept_map[dept_data["code"]] = dept
            self.stdout.write(f"{'OK' if created else 'UPD'} Dept: {dept.code}")

        # Programs
        prog_map = {}
        for prog_data in PROGRAMS:
            dept = dept_map[prog_data["dept"]]
            level = Program.DegreeLevel.UNDERGRAD if prog_data["level"] == "BACHELOR" else Program.DegreeLevel.MASTER
            prog, created = Program.objects.get_or_create(
                code=prog_data["code"],
                defaults={"department": dept, "name": prog_data["name"], "degree_level": level},
            )
            prog_map[prog_data["code"]] = prog
            self.stdout.write(f"{'OK' if created else 'UPD'} Program: {prog.code}")

        # Instructors
        instr_map = {}
        for instr_data in INSTRUCTORS:
            dept = dept_map[instr_data["dept"]]
            user, u_created = User.objects.get_or_create(
                username=instr_data["username"],
                defaults={
                    "first_name": instr_data["first"],
                    "last_name": instr_data["last"],
                    "email": f"{instr_data['username']}@uni.edu.tr",
                    "role": User.Role.INSTRUCTOR,
                },
            )
            if u_created or not user.has_usable_password():
                user.set_password("DemoPass2026!")
                user.save()

            profile, p_created = InstructorProfile.objects.get_or_create(
                user=user,
                defaults={"department": dept, "title": instr_data["title"], "is_approved": True},
            )
            instr_map[instr_data["username"]] = profile
            self.stdout.write(f"{'OK' if p_created else 'UPD'} Instructor: {user.get_full_name()}")

        # Classrooms
        classroom_map = {}
        for cls_data in CLASSROOMS:
            classroom, c_created = Classroom.objects.get_or_create(
                building=cls_data["building"],
                room_number=cls_data["room"],
                defaults={"capacity": cls_data["capacity"]},
            )
            classroom_map[(cls_data["building"], cls_data["room"])] = classroom
            self.stdout.write(f"{'OK' if c_created else 'UPD'} Classroom: {classroom.building} {classroom.room_number}")

        uzem_dept = dept_map["UZEM"]

        # Courses + Curriculum + Elective Pools
        self._create_courses_and_curriculum(prog_map["ESM-LIS"], ESM_COURSES, instr_map, uzem_dept)
        self._create_elective_pools(prog_map["ESM-LIS"], ESM_ELECTIVE_POOLS)

        self._create_courses_and_curriculum(prog_map["YZM-LIS"], YZM_COURSES, instr_map, uzem_dept)
        self._create_elective_pools(prog_map["YZM-LIS"], YZM_ELECTIVE_POOLS)

        self._create_courses_and_curriculum(prog_map["OINS-LIS"], OINS_COURSES, instr_map, uzem_dept)
        self._create_elective_pools(prog_map["OINS-LIS"], OINS_ELECTIVE_POOLS)

        self.stdout.write(self.style.SUCCESS("\n[OK] Comprehensive seed tamamlandı!\n"))

    def _create_courses_and_curriculum(self, program, courses_data, instr_map, uzem_dept):
        for year, terms in courses_data.items():
            for term, courses in terms.items():
                term_enum = Semester.Term.FALL if term == "fall" else Semester.Term.SPRING
                for code, name, credits in courses:
                    # Shared codes (AITB, TDB, YDB, USEC, YDI) → UZEM dept, no program
                    is_shared = any(code.startswith(pfx) for pfx in
                                    ("AITB", "TDB", "YDB", "USEC", "YDI"))
                    if is_shared:
                        course, created = Course.objects.get_or_create(
                            code=code,
                            defaults={"department": uzem_dept, "name": name, "credits": credits},
                        )
                    else:
                        course, created = Course.objects.get_or_create(
                            code=code,
                            defaults={
                                "department": program.department,
                                "program": program,
                                "name": name,
                                "credits": credits,
                            },
                        )

                    # Update name/credits/description even if course existed
                    changed = False
                    if course.name != name:
                        course.name = name
                        changed = True
                    if course.credits != credits:
                        course.credits = credits
                        changed = True
                    desc = COURSE_DESCRIPTIONS.get(code, "")
                    if desc and course.description != desc:
                        course.description = desc
                        changed = True
                    if changed:
                        course.save(update_fields=["name", "credits", "description"])

                    CurriculumItem.objects.get_or_create(
                        program=program,
                        course=course,
                        defaults={"year_level": year, "term": term_enum},
                    )

                    status = "OK" if created else "UPD"
                    self.stdout.write(f"  {status} Course [{program.code}]: {code} - {name} ({credits} AKTS)")

    def _create_elective_pools(self, program, pools_data):
        for pool_data in pools_data:
            pool, created = ElectivePool.objects.get_or_create(
                program=program,
                name=pool_data["name"],
                defaults={"required_count": pool_data["required"]},
            )
            if not created:
                pool.required_count = pool_data["required"]
                pool.save(update_fields=["required_count"])

            for code in pool_data["courses"]:
                try:
                    course = Course.objects.get(code=code)
                    pool.courses.add(course)
                except Course.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  [!] Havuz kursu bulunamadı: {code}"))

            status = "OK" if created else "UPD"
            self.stdout.write(f"  {status} ElectivePool [{program.code}]: {pool.name}")
