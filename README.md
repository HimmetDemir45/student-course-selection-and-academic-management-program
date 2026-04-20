# Öğrenci Ders Seçimi ve Akademik Yönetim Sistemi

[![codecov](https://codecov.io/gh/HimmetDemir45/student-course-selection-and-academic-management-program/graph/badge.svg)](https://codecov.io/gh/HimmetDemir45/student-course-selection-and-academic-management-program)
[![CI](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/actions/workflows/ci.yml/badge.svg)](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/actions/workflows/ci.yml)

Üniversite dersi kapsamında geliştirilen, **rol tabanlı yetkilendirme**, **kayıt (enrollment) iş kuralları**, **GPA / transkript** ve **denetim günlükleri** içeren modern bir web uygulamasıdır. Depo Flask’tan Django’ya geçişi tamamlar nitelikte tutulmuş; yeni özellikler Django üzerinden ilerler (`migration_notes.md`, `AGENTS.md`).

---

## 1) Proje Özeti

| Başlık | İçerik |
|--------|--------|
| **Amaç** | Öğrencilerin bölüm/dönem kurallarına uygun ders kaydı; öğretim üyelerinin not girişi; yöneticilerin gözetimi ve kurucu onaylı admin yükseltmesi |
| **Kullanıcı rolleri** | Öğrenci, öğretim üyesi, admin; ayrıca tek **kurucu yönetici** (`is_founder_admin`) |
| **Veri** | MySQL üzerinde ilişkisel şema (çoklu uygulama modelleri, FK ilişkileri) |
| **Dağıtım hedefi** | Docker + AWS uyumlu (RDS, S3, ALB/EC2 veya ECS) |

---

## 2) Temel Özellikler

- Hesap yaşam döngüsü: kayıt, giriş/çıkış, rol atamaları; girişe yönelik **brute-force sınırlama**
- Ders ve bölüm yönetimi: kurslar, bölümler, zaman çizelgesi ile kayıt uygunluğu
- Kayıt kuralları: kapasite, önkoşul, çakışma, add/drop penceresi, GPA eşikleri (servis katmanında)
- Akademik: notlar, transkript görünümü, duyurular (`academic`)
- **Kurucu onayı**: kullanıcıların admin talebi açması; yalnızca kurucunun web arayüzünden onay/red (`dashboard`, `accounts.AdminRequest`)
- Denetim: `audit_logs` ile seçili işlemlerin izlenebilirliği
- Sağlık uçları: `/health/live/`, `/health/ready/` (readiness’te DB kontrolü)
- İstek korelasyonu: yanıt başlığı **`X-Request-ID`**

---

## 3) Mimari ve App Yapısı

İstek akışı: `HTTP` → `config/urls.py` → `app/urls.py` → view → (servis) → ORM → şablon yanıtı.

| Django app | Sorumluluk |
|------------|------------|
| `config` | Ayarlar (`settings/*`), kök URL, WSGI/ASGI |
| `accounts` | Kullanıcı modeli, formlar, giriş/kayıt, admin talebi |
| `core` | Ana sayfa, sağlık, hata işleyicileri, ortak middleware/servisler, önbellekli istatistik |
| `students` | Öğrenci profilleri ve öğrenci odaklı rotalar |
| `instructors` | Öğretim üyesi rotaları |
| `courses` | Ders ve ilgili listeler |
| `enrollments` | Bölüm kayıt akışları, kapasite yarışında atomik servis |
| `academic` | Not, transkript, akademik içerik |
| `dashboard` | Yönetim özeti, kurucu kuyruğu |
| `audit_logs` | Denetim kayıtları listesi |

Şablonlar `templates/` altında ortak düzen: `templates/base.html`.

---

## 4) Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Dil | Python **3.12+** |
| Web | **Django 5** (sürüm pin’leri `requirements.txt`) |
| Veritabanı | **MySQL 8** (`PyMySQL`, `cryptography`) |
| Ortam | `django-environ`, `.env` |
| Üretim medya/statik | `django-storages`, `boto3`, S3 |
| Sunucu | Gunicorn |
| Konteyner | Docker, `docker-compose` |
| CI | GitHub Actions (Ruff, pip-audit, Bandit JSON artifact, test, Codecov, SBOM) |
| Yapılandırılmış log | `structlog` (JSON mod opsiyonel) |

---

## 5) Kurulum (Local)

**Ön koşullar:** Python 3.12+, MySQL (yerel veya Docker), Git.

```powershell
cd "student course selection and academic management program"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

`.env` içinde veritabanı alanlarını düzenleyin. Linux/macOS için `source .venv/bin/activate` ve `cp .env.example .env`.

Geliştirici araçları (lint, coverage, pytest):

```powershell
pip install -r requirements-dev.txt
```

---

## 6) Environment Variables

Örnek şablon: **`.env.example`**. Aşağıda yerel geliştirme için **kopyala-yapıştır** iskeleti (gerçek sırları repoya koymayın):

```env
# --- Django ---
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=yerel-gelistirme-icin-rastgele-uzun-dize
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=

LOG_LEVEL=INFO
# DJANGO_LOG_JSON=False
# LOG_SERVICE_NAME=student-academic-mgmt

# Rate limit (geliştirme/CI genelde kapalı; prod için dokümana bakın)
# RATELIMIT_ENABLE=True
# FEATURE_ENROLLMENT_RATELIMIT=True

# --- MySQL (ayrık alanlar) ---
DB_NAME=university_db
DB_USER=root
DB_PASSWORD=CHANGE_ME
DB_HOST=127.0.0.1
DB_PORT=3306

# Tek satır alternatif:
# DATABASE_URL=mysql://user:CHANGE_ME@127.0.0.1:3306/university_db
```

**Üretim** için `.env.production.example` dosyasına bakın: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` zorunlu alanlar arasındadır.

---

## 7) Veritabanı Kurulumu ve Migration

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"
python manage.py migrate
```

Yeni şema değişikliği sonrası:

```powershell
python manage.py makemigrations
python manage.py migrate
```

**Not:** Phase 9 kapıları migration ileri-geri duman testi içerir (`scripts/smoke_migration.sh`, `make migration-smoke` — bash ortamı).

---

## 8) Seed / Test Verisi

```powershell
python manage.py loaddata phase4_seed
```

Fixture: `core/fixtures/phase4_seed.json`. Seed kullanıcı parolası ders dokümantasyonunda **`seedpass123`** olarak geçer (`AGENTS.md`).

Kurucu yönetici atama (tek hesap):

```powershell
python manage.py set_founder_admin <kullanici_adi>
```

---

## 9) Uygulamayı Çalıştırma

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.dev"
python manage.py runserver
```

Tarayıcı: `http://127.0.0.1:8000`

**Docker (yerel tam yığın):**

```bash
docker compose up --build
```

Web: `http://localhost:8000` — MySQL portu compose dosyasında tanımlıdır; **üretimde** varsayılan şifreleri kullanmayın.

---

## 10) Test Stratejisi ve Test Komutları

| Komut | Açıklama |
|--------|-----------|
| `python manage.py test` | Django test keşfi (`core/test_phase4.py`, `core/test_phase6.py`, …) |
| `coverage run manage.py test` + `coverage report` | CI ile aynı coverage kaynağı; eşik **%75** (`pyproject.toml`) |
| `make ci` | Güvenlik + migration smoke + pytest + **%80** coverage (Linux/WSL, `Makefile`) |
| `pytest -m "unit"` vb. | Phase 9 iş akışı ile hizalı işaretli testler |

Ayrıntı: **`docs/TESTING.md`**.

---

## 11) Güvenlik Özeti

- **RBAC:** `User.role` + view/mixin kontrolleri; kurucu için `FounderAdminRequiredMixin` (`core/permissions.py`)
- **CSRF:** etkin; formlarda token
- **SQLi:** ORM kullanımı
- **XSS:** şablon kaçışı
- **Brute-force:** `LoginBruteForceMiddleware`
- **Throttling:** enrollment POST (`django-ratelimit`, ortam bayrakları ile)
- **Audit:** `audit_logs`
- **Gizli bilgi:** log maskeleme; `.gitignore` / secret tarama (Phase 9)

Özet belge: **`docs/SECURITY_OVERVIEW.md`** — politika: **`SECURITY.md`**.

---

## 12) CI/CD ve Release Akışı

| Workflow | Tetik | Amaç |
|----------|--------|------|
| `ci.yml` | `push`/`pull_request` (`main`, `develop`), `workflow_call` | Ruff, pip-audit, Bandit (JSON artifact), MySQL’de migrate + test + Codecov (`fail_ci_if_error: true`) + SBOM |
| `phase9-ci.yml` | Aynı | Ek kapılar: pytest marker, migration smoke, detect-secrets |
| `deploy.yml` | `main` / manuel | GHCR imaj üretimi |
| `release.yml` | Tag `v*` | Kalite kapısı → imaj → isteğe bağlı SSH/ECS deploy → smoke |
| `canary.yml` | Zamanlanmış + manuel | Uç sağlık kontrolleri (`CANARY_BASE_URL`) |
| `smoke-tests.yml` | Manuel | Canlı taban URL ile HTTP duman testi |

Sürüm numaralandırma ve adımlar: **`RELEASE.md`**, değişiklik günlüğü: **`CHANGELOG.md`**.

---

## 13) Gözlemlenebilirlik

- **Metin veya JSON log:** `DJANGO_LOG_JSON`; alan referansı `docs/observability.md`
- **`request_id`:** middleware + `request_finished` satırları
- **`service`:** `LOG_SERVICE_NAME` (Phase 10)
- **Canary:** GitHub Actions + harici sentetik (`make canary`)
- **SLO / alarm checklist:** `docs/sre/sli-slo.md`, `docs/operations/monitoring-and-alerting-checklist.md`

---

## 14) Rollback ve Incident Mini Rehberi

1. **Uygulama:** Önceki GHCR etiketi (`sha-…` veya semver) ile container’ı yeniden çalıştırın.
2. **Veritabanı:** Kritik migrasyonlarda önce snapshot; geri dönüş genelde snapshot veya kontrollü `migrate <app> <önceki>` ile.
3. **Olay:** `X-Request-ID` toplayın; `docs/runbooks/incident-response.md` ve **`docs/RUNBOOK.md`** özetine bakın.

---

## 15) Phase 1–12 Detaylı Yolculuk

Aşağıdaki sıra, depo evriminin **kronolojik** özetidir. Teknik derinlik: **`docs/PHASE_HISTORY.md`**.

## Phase 1

### Hedef

Django 5 proje omurgası; `config/` paketi, kök URL, şablon kökü, `core` iskeleti.

### Yapılan Çalışmalar

`manage.py`, `config/settings/base.py`, `config/urls.py`, paylaşımlı `templates/base.html`, Flask’tan miras kararların `migration_notes.md` ile belgelenmesi.

### Teknik Kazanımlar

Tek runtime olarak Django; modüler URL include düzeni.

### Operasyonel Etki

Geliştiriciler için tek `runserver` ve ayar modülü sözleşmesi.

### Notlar

Eski Flask dosyaları referans için tutulabilir; yeni kod Django’da yazılır.

## Phase 2

### Hedef

Kimlik: kayıt, oturum, özelleştirilmiş kullanıcı.

### Yapılan Çalışmalar

`accounts` uygulaması, `AUTH_USER_MODEL`, formlar, giriş/çıkış rotaları, parola doğrulayıcıları.

### Teknik Kazanımlar

Rol alanı ile RBAC temeli; Django auth ile uyum.

### Operasyonel Etki

Tüm korumalı ekranlar için tutarlı `LOGIN_URL` yönlendirmesi.

### Notlar

Admin / öğrenci / öğretim üyesi ayrımı sonraki fazlarda sıkılaştırıldı.

## Phase 3

### Hedef

Öğrenci, öğretim üyesi ve ders domain’i.

### Yapılan Çalışmalar

`students`, `instructors`, `courses` modelleri ve CRUD / liste şablonları.

### Teknik Kazanımlar

FK ağı genişledi; ders seçimi için veri temeli oluştu.

### Operasyonel Etki

İçerik yönetimi uygulama URL’leri üzerinden erişilebilir hale geldi.

### Notlar

İlişkisel şema, ders gereksinimi olan «en az 12 ilişkili tablo» hedefini destekler.

## Phase 4

### Hedef

Kayıt iş kuralları, GPA, transkript, öğretim notu, denetim (audit).

### Yapılan Çalışmalar

`core/services/` kuralları, `enrollments`, `academic`, `audit_logs`, `phase4_seed`, `core/test_phase4.py`.

### Teknik Kazanımlar

İş mantığının servis katmanında toplanması; otomatik testle doğrulanan kurallar.

### Operasyonel Etki

Öğrenci ve öğretim akışları üretim mantığına yaklaştı.

### Notlar

Bu fazdan sonra performans ve eşzamanlılık optimizasyonları anlamlı hale geldi.

## Phase 5

### Hedef

Docker ve AWS uyumlu dağıtım.

### Yapılan Çalışmalar

`docker-compose.yml`, `docker-compose.prod.yml`, Gunicorn, `entrypoint`, `prod` ayarları, S3/RDS ortam sözleşmesi, sağlık uçları.

### Teknik Kazanımlar

Ortam değişkeni ile aynı kodda dev/prod ayrımı.

### Operasyonel Etki

Buluta taşınabilir çalışma birimi (konteyner imajı).

### Notlar

TLS sonlandıran proxy arkasında `SECURE_SSL_REDIRECT` kullanın; aksi halde yönlendirme döngüsü riski.

## Phase 6

### Hedef

Performans, güvenlik sertleştirmesi, test ve coverage disiplini.

### Yapılan Çalışmalar

`select_related` / `prefetch_related`, indeksler, kısa TTL önbellek, log maskeleme, prod güvenlik başlıkları, `core/test_phase6.py`, Dependabot, `SECURITY.md`, coverage eşiği %75.

### Teknik Kazanımlar

N+1 bilinci; CI’da güvenlik kapıları (`pip-audit`, Bandit).

### Operasyonel Etki

Daha öngörülebilir yük ve log hijyeni.

### Notlar

`pip-audit --strict` başarısızken merge önerilmez.

## Phase 7

### Hedef

Sürüm disiplini ve operasyon dokümantasyonu.

### Yapılan Çalışmalar

`RELEASE.md`, `CHANGELOG.md`, `release.yml`, `smoke-tests.yml`, runbook’lar, go-live checklist, `X-Request-ID` middleware.

### Teknik Kazanımlar

SemVer ve tag tabanlı yayın; destek için istek korelasyonu.

### Operasyonel Etki

Sınıfta veya ekipte tekrarlanabilir yayın töreni.

### Notlar

`HEALTHCHECK_BASE_URL` secret ile deploy sonrası doğrulama yapılabilir.

## Phase 8

### Hedef

İleri üretim: dağıtım otomasyonu, gözlemlenebilirlik, kayıt yarış güvenliği.

### Yapılan Çalışmalar

Release içinde SSH/ECS seçenekleri, Codecov + Bandit JSON artifact + CycloneDX SBOM, structlog JSON, `enrollment_atomic` ve `select_for_update`, canary workflow, özellik bayrakları.

### Teknik Kazanımlar

Kapasite yarışında tutarlı kayıt; yapılandırılmış log çıktısı.

### Operasyonel Etki

Daha az manuel adımla dağıtım ve doğrulama.

### Notlar

`docs/observability.md`, `docs/reliability/concurrency-and-locking.md` referans alınmalıdır.

## Phase 9

### Hedef

Sıkı CI kapıları ve release runbook birleşimi.

### Yapılan Çalışmalar

`phase9-ci.yml`, `phase9-release.yml`, `Makefile`, migration smoke script, `detect-secrets` baseline, `docs/PHASE9_RUNBOOK.md`.

### Teknik Kazanımlar

Pytest marker ayrımı; migrasyon ileri–geri duman testi; secret baseline denetimi.

### Operasyonel Etki

«Tag atmadan önce» kontrol listesi otomasyonla desteklenir.

### Notlar

`make ci` coverage eşiği %80; ana `ci.yml` ile fark bilinçli yönetilmelidir.

## Phase 10

### Hedef

Test altyapısı iyileştirmesi ve loglarda servis adı ayrımı.

### Yapılan Çalışmalar

`tests/conftest.py`, eşzamanlılık testleri, `LOG_SERVICE_NAME`, ilgili dokümantasyon güncellemeleri.

### Teknik Kazanımlar

CI MySQL ortamında daha stabil bağlantı ve zaman aşımı ayarları.

### Operasyonel Etki

Çoklu servis log ayrıştırmasına hazırlık.

### Notlar

Ayrıntı: `docs/observability.md` içindeki Phase 10 notları.

## Phase 11

### Hedef

Kurucu onaylı admin yükseltmesi ve Bootstrap üzerinde arayüz cilası.

### Yapılan Çalışmalar

`AdminRequest` modeli, dashboard kuyruk/onay/red, `set_founder_admin` komutu, `phase11.css`, tablo/kart şablon sınıfları, `tests/test_admin_request.py`.

### Teknik Kazanımlar

Ayrıcalıklı iş akışında `select_for_update` ve audit entegrasyonu.

### Operasyonel Etki

Admin rolünün dağıtımı kontrollü hale geldi.

### Notlar

Kurucu yönetici sayısı iş kuralı olarak tek tutulur.

## Phase 12

### Hedef

Türkçe, üretim kalitesinde README; teknik, operasyonel ve kullanıcı odaklı tamamlayıcı `docs/` seti; küçük destekleyici düzenlemeler (büyük refactor yok).

### Yapılan Çalışmalar

Bu README; `docs/PHASE_HISTORY.md`, `docs/RUNBOOK.md`, `docs/CONTRIBUTING.md`, `docs/TESTING.md`, `docs/SECURITY_OVERVIEW.md`, `LICENSE`.

### Teknik Kazanımlar

Tek giriş noktasından mimari, operasyon, güvenlik ve test anlatımının birleştirilmesi.

### Operasyonel Etki

Yeni geliştirici ve operatör için onboarding sürtünmesinin azalması.

### Notlar

Enrollment, GPA ve transkript iş kurallarına dokunulmadan dokümantasyon odaklı fazdır.

---

## 16) Roadmap (Phase 13+ önerileri)

- Redis önbellek ve açık invalidation stratejisi (yüksek yazma senaryoları)
- Tam ECS/ECR pipeline (task definition otomatik güncelleme)
- Genişletilmiş **i18n** (`.mo` üretim pipeline’ı Windows/WSL)
- API katmanı (DRF) yalnızca gereksinim netleşince; şu an sunucu taraflı şablon odaklı
- Gelişmiş raporlama ve dışa aktarma (CSV/PDF) rol bazlı

---

## Phase 16 (Kalite ve sürdürülebilirlik)

- Ortak template parçaları eklendi: `includes/alert_messages.html`, `includes/form_errors.html`, `includes/empty_state.html`, `includes/table_toolbar.html`.
- Liste sayfalarında arama/filtre/sıralama + pagination davranışı aynı pattern'e çekildi.
- Dashboard operasyon kartları role göre genişletildi (admin kritik olaylar, instructor bekleyen notlar, student sonraki adım önerisi).
- Audit metadata alanları standartlaştırıldı (`event_type`, `actor_id`, `target`, `status`, `request_id`).
- RBAC görünürlük, kullanılabilirlik smoke ve query count regresyon testleri genişletildi.

---

## 17) Katkı Rehberi

Dal adlandırma, commit formatı ve PR checklist: **`docs/CONTRIBUTING.md`**. PR açılırken `.github/pull_request_template.md` doldurulmalıdır.

---

## 18) Lisans

Bu proje **MIT Lisansı** ile sunulmaktadır — ayrıntılar `LICENSE` dosyasında.

---

## Bu projeyi 5 dakikada ayağa kaldır

1. `python -m venv .venv` → sanal ortamı açın  
2. `pip install -r requirements.txt`  
3. `copy .env.example .env` → `DB_PASSWORD` ve gerekirse `DB_NAME` düzenleyin; MySQL’de veritabanını oluşturun  
4. `python manage.py migrate`  
5. `python manage.py loaddata phase4_seed` (isteğe bağlı, hızlı demo)  
6. `python manage.py runserver` → `http://127.0.0.1:8000`  

Docker ile: `docker compose up --build` (MySQL dahil).

---

## Sık karşılaşılan hatalar (FAQ / Troubleshooting)

| Belirti | Olası neden | Çözüm |
|---------|-------------|--------|
| `OperationalError` (MySQL) | DB yok veya şifre yanlış | MySQL’de veritabanı oluşturun; `.env` `DB_*` kontrol |
| `django.db.utils.NotSupportedError` / auth plugin | `caching_sha2_password` | `requirements.txt` içinde `cryptography` kurulu olduğundan emin olun |
| CSRF başarısız (403) | HTTPS/proxy | `DJANGO_CSRF_TRUSTED_ORIGINS` değerlerini tam origin olarak ekleyin |
| Coverage CI’da düşük | Yeni kod yolları | Test ekleyin veya `pyproject.toml` eşiğini bilinçli güncelleyin (ekip kararı) |
| `make: command not found` | Windows | `docs/TESTING.md` içindeki `ruff` / `manage.py` komutlarını doğrudan çalıştırın veya WSL kullanın |
| Phase 9 secret scan fail | Baseline uyumsuzluğu | `docs/PHASE9_RUNBOOK.md` detect-secrets adımları |

---

## Ek referanslar

| Belge | Konu |
|-------|------|
| `AGENTS.md` | Ajan/geliştirici kuralları ve komut özeti |
| `migration_notes.md` | Flask → Django eşlemesi |
| `docs/deployment/production-automation.md` | Üretim otomasyonu |
| `docs/runbooks/deployment-runbook.md` | Dağıtım ayrıntısı |
| `docs/runbooks/rollback-runbook.md` | Geri alma ayrıntısı |
