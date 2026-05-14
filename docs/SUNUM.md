# Akademik 2.0 — Proje Sunumu

**Öğrenci Ders Kaydı ve Akademik Yönetim Sistemi**
KTÜ OF Teknoloji Fakültesi · Yazılım Mühendisliği Bitirme Projesi

---

## 📌 1. Proje Hakkında

Akademik 2.0, üniversite öğrencilerinin ders seçimi, danışman onay süreçleri, devamsızlık takibi, not girişi ve haftalık ders programı yönetimini tek bir platformda toplayan, **rol tabanlı** ve **denetlenebilir** bir web uygulamasıdır.

| Özellik | Açıklama |
|---------|----------|
| **Hedef kullanıcı** | Öğrenci, Akademisyen, Danışman, Yönetici |
| **Bölüm sayısı** | 3 (Yazılım, İnşaat, Enerji Sistemleri Mühendisliği) |
| **Dönem** | Güz + Bahar 2025–2026 |
| **Backend** | Python 3.12 + Django 5 |
| **Veritabanı** | MySQL 8 (Production: PostgreSQL on Render) |
| **Frontend** | Tailwind CSS + Server-Side Rendering |
| **Dağıtım** | Docker + Render.com |

---

## 🏛️ 2. SOLID Prensiplerinin Projedeki Uygulamaları

### 2.1 SRP — Single Responsibility Principle (Tek Sorumluluk)

> "Her sınıfın yalnızca bir görevi olmalı, onu değiştirmek için tek bir sebep olmalıdır."

**Projemizdeki uygulama:**

Modellerimiz **sadece veriyi tutar**. İş kuralları (validation, hesaplama, durum geçişleri) **`core/services/` klasöründeki servis katmanına** taşınmıştır.

📁 `enrollments/models.py` — `Enrollment` modeli sadece veri:
```python
class Enrollment(TimeStampedModel):
    student = models.ForeignKey("students.StudentProfile", ...)
    section = models.ForeignKey("academic.CourseSection", ...)
    status  = models.CharField(choices=Status.choices, ...)

    def clean(self):
        validate_enrollment_save(self)   # ← Kural servise delege edilmiş
```

📁 `core/services/enrollment_rules.py` — Sadece iş kuralları:
```python
def validate_capacity(section, ...)
def validate_prerequisites(student, course, ...)
def validate_schedule_conflict(student, new_slot, ...)
```

📁 `core/services/gpa.py` — Sadece GPA hesabı:
```python
def compute_weighted_gpa(grades)
def letter_grade_to_points(letter)
```

📁 `audit_logs/services.py` — Sadece denetim kaydı:
```python
def log_event(event_type, actor, target, metadata, ...)
```

**Sonuç:** GPA formülü değişirse `gpa.py`'ye, validation kuralı değişirse `enrollment_rules.py`'ye dokunuruz. Model dosyalarına dokunmayız.

---

### 2.2 OCP — Open/Closed Principle (Açık/Kapalı)

> "Kod, yeni özelliklere açık fakat değişime kapalı olmalıdır."

**Projemizdeki uygulama:**

📁 `enrollments/models.py` — Yeni durum eklemek için sadece enum'a satır eklenir:
```python
class Status(models.TextChoices):
    PENDING    = "pending"
    ENROLLED   = "enrolled"
    DROPPED    = "dropped"
    WITHDRAWN  = "withdrawn"
    COMPLETED  = "completed"
    WAITLISTED = "waitlisted"   # ← yeni statü eklemek bu kadar basit
```

📁 `config/settings/base.py` — Middleware listesi plugin-mimarisi:
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.request_id.RequestIDMiddleware",       # custom
    "core.middleware.login_throttle.LoginBruteForceMiddleware",
    # ↑ Yeni bir middleware (cache, rate limit) eklemek için satır eklenir
    #   Mevcut middleware'lerin koduna dokunulmaz.
]
```

📁 `entrypoint.sh` — Yeni seed komutu eklemek için kontrol bayrağı:
```bash
if [ "${SEED_INS_GUZ:-0}" = "1" ]; then
    python manage.py seed_ins_guz
fi
# ↑ Yeni bölüm seed'i eklemek için yeni bir if bloğu eklenir
```

**Sonuç:** Yeni bölüm, yeni rol, yeni denetim olayı, yeni middleware — hiçbiri mevcut kodu kırmaz.

---

### 2.3 ISP — Interface Segregation Principle (Arayüz Ayrıştırma)

> "Bir sınıfa kullanmayacağı metotları zorla dayatma. Devasa tek arayüz yerine, küçük amaca özel arayüzler kullan."

**Projemizdeki uygulama:**

📁 `core/permissions.py` — Tek bir "RequiresAuth" mixin yerine **rol başına ayrı mixin**:
```python
class AdminRequiredMixin:           # sadece admin için
class StudentRequiredMixin:          # sadece öğrenci + is_approved kontrolü
class InstructorRequiredMixin:       # akademisyen + admin
class FounderAdminRequiredMixin:     # kurucu yönetici (özel)
```

View'lar **sadece ihtiyacı olan** mixin'i miras alır:
```python
class StudentTranscriptView(StudentRequiredMixin, View): ...
class GradeEntryView(InstructorRequiredMixin, View): ...
class UserApprovalQueueView(AdminRequiredMixin, View): ...
```

📁 `core/services/enrollment_rules.py` — Tek dev fonksiyon yerine **küçük validasyon fonksiyonları**:
```python
validate_capacity()           # kapasite
validate_prerequisites()      # önkoşul
validate_schedule_conflict()  # çakışma
validate_add_drop_window()    # ekleme/bırakma penceresi
validate_credit_limit()       # kredi sınırı
```

**Sonuç:** Öğrenci view'ı admin metotları görmez. Çakışma kuralını değiştirmek istesek diğer kurallara dokunmayız.

---

### 2.4 DIP — Dependency Inversion Principle (Bağımlılıkların Tersine Çevrilmesi)

> "Üst-seviye modüller alt-seviyeye değil, soyutlamalara bağlı olmalı. `new` ile sınıf oluşturmak yerine interface üzerinden konuş."

**Projemizdeki uygulama:**

**1) Django ORM — Veritabanı soyutlaması:**
```python
# ❌ Sıkı bağlı (SQL injection riski + DB değişimi zor):
cursor.execute("SELECT * FROM enrollments WHERE student_id = %s", [sid])

# ✅ Soyutlanmış (Django ORM):
Enrollment.objects.filter(student_id=sid)
```
Aynı kod MySQL, PostgreSQL, SQLite, MariaDB üzerinde çalışır. **Render'a geçtiğimizde MySQL → PostgreSQL geçişinde kodu değiştirmedik**, sadece `DATABASE_URL` değişti.

**2) Cache backend swap:**
📁 `config/settings/base.py`:
```python
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
# Prod'da Redis'e geçince: "django.core.cache.backends.redis.RedisCache"
# Kullanan kod (cache.get/set) değişmez.
```

**3) E-posta backend swap:**
📁 `config/settings/render.py`:
```python
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_USER else
    "django.core.mail.backends.console.EmailBackend"   # geliştirme için
)
```
`send_mail()` çağıran kod ne dev'de ne de prod'da değişmiyor.

**4) Storage backend swap:**
- Dev: yerel disk
- Prod: AWS S3 (`django-storages`)
- `default_storage.save(path, file)` her ikisinde de aynı.

---

### 2.5 DI — Dependency Injection (Bağımlılık Enjeksiyonu)

> "Sınıf, ihtiyaç duyduğu nesneleri kendisi yaratmaz, dışarıdan alır."

**Projemizdeki uygulama:**

**1) Django Settings → Environment Variables üzerinden enjeksiyon:**
```python
# Settings dosyası: dışarıdan değer alıyor
DATABASE_URL    = env("DATABASE_URL")
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
SECRET_KEY      = env("DJANGO_SECRET_KEY")
```
Aynı kod farklı ortamlarda (dev/test/prod) farklı bağımlılıklar ile çalışır.

**2) Middleware DI:**
```python
class RequestIDMiddleware:
    def __init__(self, get_response):   # ← get_response dışarıdan
        self.get_response = get_response
```
Middleware kendisi `HttpResponse` oluşturmaz, dışarıdan gelen `get_response` callable'ını çağırır.

**3) View DI — Form ve Request objesi enjeksiyonu:**
```python
def enrollment_approve(request, enrollment_id):
    # request objesi Django tarafından enjekte edilir
    # enrollment_id URL'den enjekte edilir
```

**4) Test'lerde Mock Injection:**
```python
def test_enrollment_capacity_full(self):
    section = SectionFactory(quota=1)
    student = StudentProfileFactory()
    # ↑ gerçek DB yerine test fixture enjekte edilir
```

**5) Context Processor — Template'e bağımlılık enjeksiyonu:**
📁 `core/context_processors.py`:
```python
def landing_stats(request):
    return {"total_students": ..., "active_courses": ...}
# Her template otomatik olarak bu değerleri alır.
```

---

## 🎨 3. Neden MVT, MVC Değil?

### MVC (Model-View-Controller) — Klasik web framework deseni:
```
Kullanıcı → Controller → Model → View → Kullanıcı
              ↑ business logic    ↑ HTML üretimi
```

### Django MVT (Model-View-Template) — İsim farkı, görev farklı:
```
Kullanıcı → URL Router → View → Model + Template → Kullanıcı
                          ↑ business logic   ↑ HTML render
```

| Klasik MVC | Django MVT | Projemizde |
|------------|-----------|------------|
| **Model** | Model | `enrollments/models.py` — veri tanımı |
| **View** (HTML) | **Template** | `templates/enrollments/section_list.html` — sunum |
| **Controller** (logic) | **View** | `enrollments/views.py` — iş mantığı |

**Neden bu isimlendirme?**
Django'cular "View" kelimesini "kullanıcının gördüğü şey değil, **isteğe yanıt veren mantık**" anlamında kullanıyor. Adlandırma farkı olsa da görevler aynı.

**Avantaj:** Django'nun **URL routing → View → ORM → Template** akışı, controller boilerplate kodunu azaltır.

📁 Akış örneğimiz:
```
1. URL:        academic/danishman/advisees/   →  config/urls.py
2. Routing:    academic/urls.py
3. View:       academic/views.py:DanismanAdviseeListView   (controller görevi)
4. Model:      Enrollment, StudentProfile, InstructorProfile
5. Template:   templates/academic/danishman_advisee_list.html
```

---

## 🐍 4. Neden Python (Django)?

| Sebep | Projemizdeki Karşılığı |
|-------|------------------------|
| **Hızlı geliştirme** | "batteries-included" framework — admin paneli, auth, ORM, migrations hazır |
| **Açık ORM** | Karmaşık SQL yazmıyoruz; `Enrollment.objects.filter(...)` yeterli |
| **Güçlü ekosistem** | `django-ratelimit`, `structlog`, `boto3`, `cryptography` — paket olarak hazır |
| **Okunabilirlik** | Indent-based syntax; ekip içi review hızlı |
| **AI/ML hazır** | Gelecekte not tahmini / öğrenci başarı analizi için `numpy`, `pandas`, `scikit-learn` entegrasyonu kolay |
| **Topluluk** | Stack Overflow + Django Forum büyük; sorun çözümü hızlı |
| **Render/Heroku/AWS uyumlu** | Standart WSGI sunucusu (Gunicorn) ile her platforma deploy edilir |

**Alternatifler ve neden seçilmediler:**
- **Node.js (Express):** ORM zayıf, schema migration manuel
- **PHP (Laravel):** Yetiştik ama Python'un AI ekosistemini sunamaz
- **Java (Spring):** Boilerplate fazla, küçük ekip için yavaş
- **Go/Rust:** Düşük seviye, hızlı geliştirme zor

---

## 🗄️ 5. Veritabanı Bağlantısı

📁 `config/settings/base.py`:
```python
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.mysql",
        "NAME":     env("DB_NAME"),
        "USER":     env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST":     env("DB_HOST", default="127.0.0.1"),
        "PORT":     env.int("DB_PORT", default=3306),
        "OPTIONS":  {"charset": "utf8mb4"},
    }
}
```

**Production (Render):**
```python
# config/settings/render.py
DATABASES = {"default": env.db("DATABASE_URL")}
# DATABASE_URL: postgres://user:pass@host:5432/dbname
```

**Akış:**
```
View                ─→ ORM             ─→ DB Driver       ─→ MySQL/PostgreSQL
Enrollment.objects     Django QuerySet    mysqlclient /       Server
.filter(...)           ANSI SQL üretir    psycopg2
```

**Güvenlik:**
- Şifreler `.env` dosyasında, git'e yüklenmez
- ORM otomatik **prepared statements** ile SQL injection engellenir
- `cryptography` paketi MySQL 8 `caching_sha2_password` auth plugin'i için

**ORM Örneği:**
```python
# Aynı saatte iki ders kaydı var mı kontrolü:
conflicts = Enrollment.objects.filter(
    student=student,
    section__time_slots__weekday=slot.weekday,
    section__time_slots__start_time__lt=slot.end_time,
    section__time_slots__end_time__gt=slot.start_time,
).exists()
```
Bu kod **karmaşık bir SQL JOIN** üretir, ama biz Python ile düşünmeye devam ederiz.

---

## 📈 6. Sistemi Büyütme (Scalability)

### 6.1 Şu Anki Yapı (Dikey Ölçek)
```
Kullanıcı → Nginx/Render Edge → Gunicorn (3 worker) → Django → MySQL
                                                            → S3 (statik dosya)
```

### 6.2 Büyütme Adımları

**1. Önbellek (Cache) — İlk adım, en büyük kazanç:**
```python
CACHES["default"]["BACKEND"] = "django.core.cache.backends.redis.RedisCache"
CACHES["default"]["LOCATION"] = "redis://redis:6379/1"
```
- Müfredat, dönem, derslik gibi az değişen veriler Redis'te
- Tahmini gain: **3-5x istek hızı**

**2. Asenkron işler — Celery:**
- E-posta gönderimi
- Toplu öğrenci bildirimleri
- Transkript PDF üretimi
- Audit log batch indexing

**3. Veritabanı ölçekleme:**
- **Read replica:** Okuma trafiğini ana DB'den ayır
- **Connection pooling:** PgBouncer / ProxySQL
- **Indeksleme:** `idx_enrollment_student_status`, `idx_offering_sem_active` — mevcut

**4. CDN (Content Delivery Network):**
- Statik dosyalar (CSS, JS, Tailwind çıktısı, ikon resimler) → CloudFront / Cloudflare
- Coğrafi yakınlığa göre dağıtım
- Origin server yükü azalır

**5. Yatay ölçek (Horizontal scaling):**
- Birden çok Django uygulama sunucusu (stateless tasarım)
- Load balancer (Render otomatik, AWS ALB)
- Session'lar DB'de değil Redis'te

**6. Microservice ayrımı (uzun vadeli):**
- `auth-service`, `enrollment-service`, `grade-service`
- gRPC veya REST üzerinden konuşur
- Her servis kendi ekibi tarafından geliştirilir

**7. API katmanı (DRF):**
- Mobil uygulama için JSON API
- Üçüncü taraf entegrasyonlar (OBS, kayıt sistemi)
- Versiyonlama: `/api/v1/`, `/api/v2/`

**8. Gözlemlenebilirlik (Observability):**
- Şu an: structlog JSON log
- Eklenebilir: Prometheus + Grafana metrikleri, OpenTelemetry tracing, Sentry hata izleme

---

## 🌐 7. Web Teknolojileri ve Projemizdeki Yeri

### 7.1 SSR — Server-Side Rendering ✅ (Kullanıyoruz)
Sunucu HTML'i tam olarak üretir, tarayıcıya hazır gönderir.

**Projemizde:** Tüm sayfalar Django Template ile sunucuda render edilir.
```
Kullanıcı → İstek → View → Template → HTML → Tarayıcı (gör)
```

**Avantajları:**
- ✅ SEO dostu (arama motorları içeriği indeksler)
- ✅ İlk yükleme hızlı (kullanıcı içeriği hemen görür)
- ✅ JavaScript devre dışı olsa bile çalışır
- ✅ Daha az frontend kompleksitesi

**Dezavantajları:**
- ❌ Her etkileşim sunucu yükü
- ❌ Mobil app için ek API gerekir

### 7.2 CSR — Client-Side Rendering ❌ (Kısmi kullanıyoruz)
JavaScript tarayıcıda HTML'i üretir.

**Projemizde:** Çok az — sadece modal aç/kapa, tema değiştirme, datepicker.

### 7.3 SPA — Single Page Application ❌ (Kullanmadık)
Tek bir HTML sayfası yüklenir, sonraki navigasyon AJAX ile yapılır.

**Neden kullanmadık?** Akademik sistem **form-ağırlıklı**, SEO ihtiyacı var, basit. SPA framework (React/Vue) gereksiz karmaşıklık olurdu.

### 7.4 PWA — Progressive Web App ⏳ (Roadmap'te)
Web sitesinin mobil uygulama gibi davranması (offline çalışma, push notification, ana ekran ikonu).

**Projemize eklenebilir:**
- `manifest.json` ekleyerek "Ana ekrana ekle"
- Service Worker ile yoklama listesinin offline cache'lenmesi
- Push notification: yeni duyuru / danışman onayı

### 7.5 CORS — Cross-Origin Resource Sharing 🔒 (Yapılandırılmış)
Bir web sitesinin başka bir domain'den kaynak istemesini denetleyen güvenlik protokolü.

**Projemizde:**
```python
# config/settings/base.py
DJANGO_CSRF_TRUSTED_ORIGINS = ["https://akademik2.onrender.com"]
```
- Aynı origin'den yapılan istekler izinli
- Farklı domain'den (örn: kötü amaçlı bir site) CSRF saldırısı engellenir
- API katmanı eklersek `django-cors-headers` ile genişletilir

### 7.6 CDN — Content Delivery Network 🚀 (Önerilebilir)
İçeriği kullanıcıya en yakın sunucudan dağıtarak gecikme azaltır.

**Projemize eklenebilir:**
- Trabzon'daki bir öğrenci için statik dosyalar İstanbul edge'inden gelir
- AWS CloudFront / Cloudflare entegrasyonu
- `STATIC_URL` cdn domain'e yönlendirilir

### 7.7 DCI — Data Context Interaction
Bir nesnenin **kontekste göre farklı roller** üstlenmesini modelleyen tasarım.

**Projemizde örtük uygulama:**
- `InstructorProfile` aynı obje — **ders sahibi** olduğunda ders işlemleri yapar, **`is_advisor=True`** olduğunda danışman işlemleri yapar
- Kontekste göre `enrollment_approve` view'ı farklı yetki kontrolü uygular:
```python
is_course_instructor = enrollment.section.offering.instructor_id == inst.pk
is_advisor          = enrollment.student.advisor_id == inst.pk and inst.is_advisor
```

---

## 🛡️ 8. Güvenlik (Hocanın Sorabileceği)

| Konu | Bizim Yaklaşımımız |
|------|--------------------|
| **SQL Injection** | Django ORM → otomatik prepared statements |
| **XSS** | Template auto-escape (`{{ value }}` otomatik kaçışlı) |
| **CSRF** | Django'nun yerleşik CSRF token middleware'i |
| **Brute-force login** | `LoginBruteForceMiddleware` — 5 başarısız denemede 15 dk blok |
| **Şifre saklama** | PBKDF2 + SHA256 (Django default) |
| **Yetki bypass** | View mixin'leri her isteğin başında role'ü doğrular |
| **HTTPS** | Render'da varsayılan; `SECURE_SSL_REDIRECT=True` |
| **Secret yönetimi** | `.env` dosyası git'e yüklenmez (`.gitignore`) |
| **Audit log** | Kritik işlemler (onay, red, not, devamsızlık) `audit_logs` tablosunda |
| **Rate limiting** | `django-ratelimit` ders kaydı POST'larında |
| **Email validation** | Form clean methodları + Django validators |

---

## 📋 9. Hocanın Sorabileceği Sorular ve Cevaplar

### Q1: Neden Django, Flask değil?
**Cevap:** Flask "micro" framework, her şeyi kendiniz kurmanız gerekir (auth, admin panel, ORM, migrations). Django "batteries-included" — eğitim projesi için **3-4 hafta kazandırır**. Flask iyi seçim olurdu ama küçük API'ler için. Bizim ihtiyaç: çok rollü, form-ağırlıklı, denetim gerekli → Django ideal.

### Q2: ORM'in dezavantajı yok mu? N+1 problemi?
**Cevap:** Var. Bilinçliyiz. `select_related` ve `prefetch_related` kullandık:
```python
StudentProfile.objects.select_related("user", "department", "program", "advisor__user")
```
Phase 6'da N+1 problemi için **regresyon testleri** yazdık. Test sayfa açıldığında DB query sayısını sayar, sınırı aşarsa fail eder.

### Q3: Hangi tasarım deseni (Design Pattern) kullandınız?
**Cevap:**
- **MVT (Model-View-Template)** — Django'nun core pattern'i
- **Mixin Pattern** — `core/permissions.py`'de rol bazlı izinler için
- **Middleware Chain Pattern** — request/response pipeline'ı
- **Factory Pattern** — Test'lerde `StudentProfileFactory`, `EnrollmentFactory`
- **Repository Pattern (örtük)** — `Manager.objects.filter(...)` Django ORM bunu sağlıyor
- **Strategy Pattern** — `EMAIL_BACKEND`, `CACHES["BACKEND"]` swap edilebilir
- **Observer Pattern** — Django signals (örn: `post_save` ile audit log)

### Q4: Test yazdınız mı? Coverage ne kadar?
**Cevap:** Evet. Pytest + Django test framework. Coverage eşiği **%75-80**. Test türleri:
- **Unit:** GPA hesabı, validation kuralları
- **Integration:** View + DB
- **Concurrency:** Yarış koşulu testleri (`select_for_update` doğrulaması)
- **RBAC:** Her rolün doğru sayfayı gördüğü/görmediği

### Q5: Kayıt yarış koşulu? (İki öğrenci son kontenjana aynı anda)
**Cevap:** `core/services/enrollment_atomic.py` — Django'nun `transaction.atomic()` + `select_for_update()` ile **veritabanı satır kilidi**. İki kullanıcı aynı saniyede istek atsa bile birincisi kilitler, ikincisi bekler ve sonra "kontenjan dolu" hatasını alır.

### Q6: Performans için ne yaptınız?
**Cevap:**
- Database indeksleri (`indexes = [...]` Meta'da)
- `select_related` / `prefetch_related` N+1 önler
- `LocMemCache` (geliştirme) → Redis (üretim) hazır
- Statik dosyalar S3'te
- Gunicorn 3 worker (Render free tier)
- Sayfa başına query sayısı regresyon testi

### Q7: Bu projeyi gerçek hayatta kullanılabilir mi?
**Cevap:** Evet, küçük ölçekte kullanılabilir. Büyütme için:
1. Redis cache + Celery
2. PostgreSQL replica
3. CDN (CloudFront)
4. Sentry hata izleme
5. KTÜ ile entegrasyon API'si (öğrenci no, akademik takvim)

### Q8: Yeni bir bölüm eklemek istesek (örn: Makine Mühendisliği)?
**Cevap:** **Hiç kod değişikliği gerekmez!** 
- Admin panelinden veya yeni `seed_makine_guz.py` ile bölüm + dersler + programı tanımla
- Sistem OCP gereği yeni veriyi otomatik tanır

### Q9: Mobil uygulama desteği?
**Cevap:** Şu anda yok. Eklemek için:
1. DRF (Django Rest Framework) API katmanı — `/api/v1/`
2. JWT authentication
3. React Native / Flutter ile native app
4. Mevcut view ve servis katmanı API'ye sarılır, **business logic yeniden yazılmaz**

### Q10: Çevrimdışı çalışır mı? (PWA)
**Cevap:** Şu anda hayır. PWA'ya dönüştürmek için:
1. `manifest.json` ekle
2. Service Worker ile statik kaynaklar offline cache
3. IndexedDB ile son yoklama listesi cache
4. Sync API ile bağlantı gelince güncelleme

### Q11: Veritabanı şeması büyürse?
**Cevap:** Django Migration sistemi var:
- `python manage.py makemigrations` → otomatik diff
- `python manage.py migrate` → uygular
- Rollback: `python manage.py migrate app_name 0023`
- CI'da `migration_smoke.sh` ile ileri-geri test edilir

### Q12: Kod kalitesi nasıl ölçülüyor?
**Cevap:**
- **Ruff** — Python linter (PEP-8 + bug avı)
- **Bandit** — Güvenlik açığı taraması
- **pip-audit** — Bağımlılık zafiyet taraması
- **Codecov** — Test coverage izleme
- **detect-secrets** — Sızıntı önleme
- **CycloneDX SBOM** — Tedarik zinciri güvenliği
- Hepsi GitHub Actions CI'da otomatik çalışır

### Q13: Veriler nasıl korunuyor (KVKK/GDPR)?
**Cevap:**
- Şifreler hash'li (PBKDF2)
- Loglarda kişisel veri maskelenir
- Audit log kim/ne zaman/ne yaptı kayıtlı (denetlenebilir)
- HTTPS zorunlu
- Veritabanı yedekleri Render'da otomatik

### Q14: Dağıtım nasıl yapılıyor?
**Cevap:**
- Local: `docker compose up`
- GitHub'a push → CI çalışır (test + lint)
- Tag (v1.x) → GHCR'a Docker image
- Render webhook → otomatik deploy
- `entrypoint.sh` migrate + seed + gunicorn başlatır
- Smoke test'ler doğrular

### Q15: Loglar nerede tutuluyor?
**Cevap:**
- Geliştirme: console (text)
- Üretim: structlog JSON formatında stdout → Render log aggregator
- Audit kayıtları: PostgreSQL `audit_logs_auditevent` tablosu
- Her isteğe **`X-Request-ID`** atanır → log'larda korelasyon için

---

## 🚀 10. Gösterilebilir Demo Akışı

1. **Admin** → bölüm/program/dönem yönet, kullanıcı onayla
2. **Öğrenci** → ders seç, danışman onayını bekle
3. **Danışman** (Musa Arslan veya İ.U. Yılmaz) → öğrencisinin kayıtlarını topluca onayla VEYA gerekçeyle reddet
4. **Reddedilen kayıt** → öğrenci "Ders seçimlerim"de **danışman notunu** görür
5. **Akademisyen** → kendi dersinde yoklama al, harf notu gir (AA/BA/.../FF/I)
6. **Tema değiştirme** → dark ↔ light geçişi sorunsuz
7. **Haftalık program** → öğrenci kayıt yapmamışsa müfredat fallback gösterir

---

## 📊 11. Proje İstatistikleri

| Metrik | Değer |
|--------|-------|
| **Django app sayısı** | 9 (accounts, students, instructors, courses, enrollments, academic, dashboard, audit_logs, core) |
| **Model sayısı** | 20+ ilişkili tablo |
| **View (URL endpoint)** | 80+ |
| **Test sayısı** | 100+ |
| **Coverage** | %75-80 |
| **Bölüm sayısı** | 3 (YZM, INS, ESM) |
| **Seed komut sayısı** | 9 |
| **CI workflow** | 7 |
| **Toplam kod satırı** | ~15.000 (test + doc dahil ~25.000) |

---

## 💡 12. Öne Çıkan Teknik Detaylar

### Çakışma algoritması (Union-Find)
Haftalık programda aynı saatte birden fazla ders varsa, **disjoint-set** algoritması ile çakışma grupları bulunur ve kartlar yan yana dizilir.

📁 `academic/views.py:_assign_columns()` — özellikle hocanız algoritma sorarsa:
```python
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]  # path compression
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
```

### Atomic enrollment (Yarış koşulu önleme)
```python
with transaction.atomic():
    section = CourseSection.objects.select_for_update().get(pk=pk)
    if section.enrollment_count >= section.quota:
        raise CapacityFull()
    Enrollment.objects.create(student=s, section=section)
```

### Idempotent seed
Tüm seed komutları `get_or_create()` ile yazıldı — **defalarca çalıştırılabilir**, dublicate oluşturmaz.

---

## 🎯 13. Sonuç

Akademik 2.0:
- **SOLID prensiplerine sadık** mimari
- **Test edilebilir** servis katmanı
- **Genişletilebilir** plugin yapısı (middleware, seed, validation)
- **Güvenli** (CSRF, XSS, SQL injection, audit)
- **Üretime hazır** (Docker, CI/CD, gözlemlenebilirlik)
- **Eğitim odaklı** ama **gerçek dünya kalitesinde** kod

> "İyi kod bir kez yazılır, defalarca okunur." Projemiz, gelecek geliştiriciler için anlaşılır, genişletilebilir ve sürdürülebilir olacak şekilde tasarlandı.

---

**Sunum sahibi:** Himmet Demir
**Proje deposu:** [github.com/HimmetDemir45/student-course-selection-and-academic-management-program](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program)
**Canlı demo:** [student-course-selection-and-academic.onrender.com](https://student-course-selection-and-academic.onrender.com)
