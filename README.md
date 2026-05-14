# Akademik 2.0 — Üniversite Ders Kaydı ve Akademik Yönetim Sistemi

[![codecov](https://codecov.io/gh/HimmetDemir45/student-course-selection-and-academic-management-program/graph/badge.svg)](https://codecov.io/gh/HimmetDemir45/student-course-selection-and-academic-management-program)
[![CI](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/actions/workflows/ci.yml/badge.svg)](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

KTÜ OF Teknoloji Fakültesi için geliştirilen, **rol tabanlı yetkilendirme**, **danışman onay akışı**, **devamsızlık & not yönetimi** ve **haftalık ders programı** içeren modern bir web uygulaması. Django 5 ve MySQL üzerinde çalışır, Docker + Render uyumlu olarak dağıtılır.

> 🎓 **Bölümler:** Yazılım Mühendisliği · İnşaat Mühendisliği · Enerji Sistemleri Mühendisliği

---

## 🚀 5 Dakikada Ayağa Kaldır

```bash
# 1. Sanal ortam + bağımlılıklar
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Ortam değişkenleri
cp .env.example .env        # Windows: copy .env.example .env
# .env içinde DB_PASSWORD ve DB_NAME değerlerini düzenleyin

# 3. Veritabanı + seed
python manage.py migrate
python manage.py seed_comprehensive      # Kapsamlı demo veri
python manage.py seed_danishman          # Danışman atamaları
python manage.py seed_yzm_weekly         # YZM Güz programı
python manage.py seed_yzm_bahar          # YZM Bahar programı
python manage.py seed_ins_guz            # İnşaat Güz
python manage.py seed_ins_bahar          # İnşaat Bahar
python manage.py seed_esm_bahar          # Enerji Bahar

# 4. Çalıştır
python manage.py runserver
```

Tarayıcı: <http://127.0.0.1:8000>

**Docker ile (MySQL dahil):**
```bash
docker compose up --build
```

---

## ✨ Temel Özellikler

### Öğrenci
- Ders kaydı (kapasite + çakışma + önkoşul kontrolü)
- Onay durumu takibi (PENDING / ENROLLED / DROPPED)
- **Danışman red notu** öğrenciye gösterilir
- Transkript, müfredat planı, GPA hesabı
- Devamsızlık görüntüleme
- **Haftalık ders programı** (kayıt yoksa müfredat fallback)

### Öğretim Üyesi (Akademisyen)
- Kendi şubelerinin yoklamasını alma (sadece ENROLLED öğrenciler)
- Not girişi: harf notu (AA, BA, BB, CB, CC, DC, DD, FD, FF, I) + sayısal
- Alternatif ders önerisi
- Ders programı görüntüleme

### Danışman (sadece `is_advisor=True`)
- Danışöğrenci listesi
- **Tümünü onayla** akışı (toplu onay)
- Reddetme + gerekçe notu (öğrenciye iletilir)
- Bekleyen kayıtlar paneli

### Admin
- Kullanıcı, bölüm, program, müfredat yönetimi
- Dönem aç/kapat, kullanıcı onay kuyruğu
- Audit log incelemesi
- Kurucu yönetici (`is_founder_admin`) atama

---

## 🏗️ Mimari

| Django App | Sorumluluk |
|------------|------------|
| `config` | Ayarlar, kök URL, WSGI/ASGI |
| `accounts` | Kullanıcı modeli, kimlik akışı, admin talebi |
| `core` | Sağlık uçları, ortak servisler, middleware |
| `students` | Öğrenci profili, transkript, müfredat, devamsızlık |
| `instructors` | Akademisyen alanı, danışman ekranları |
| `courses` | Ders, şube, derslik, seçmeli havuz |
| `enrollments` | Kayıt akışları, atomik kapasite servisleri |
| `academic` | Not, dönem, müfredat, yoklama, **haftalık program** |
| `dashboard` | Yönetim özeti, kurucu kuyruğu, onay akışları |
| `audit_logs` | Denetim kayıtları |

İstek akışı: `HTTP` → `config/urls.py` → `app/urls.py` → view → (servis) → ORM → template

---

## ⚙️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Dil | Python **3.12+** |
| Framework | **Django 5** |
| Veritabanı | **MySQL 8** (PyMySQL + cryptography) |
| Frontend | Tailwind CSS + Lucide ikonlar + vanilla JS |
| Sunucu | Gunicorn |
| Konteyner | Docker / docker-compose |
| Dağıtım | Render.com / AWS (S3 + RDS) |
| CI | GitHub Actions (Ruff, pip-audit, Bandit, coverage, SBOM) |
| Log | structlog (JSON modu opsiyonel) |

---

## 📋 Environment Variables

Ana kontrol değişkenleri:

```env
# Django
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=<random-uzun-dize>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# MySQL
DB_NAME=university_db
DB_USER=root
DB_PASSWORD=CHANGE_ME
DB_HOST=127.0.0.1
DB_PORT=3306

# Veya tek satır
# DATABASE_URL=mysql://user:CHANGE_ME@127.0.0.1:3306/university_db

# Log
LOG_LEVEL=INFO
# DJANGO_LOG_JSON=False
```

**Üretim** için: `.env.production.example` dosyasına bakın.

---

## 🌱 Seed Komutları

| Komut | Açıklama |
|-------|----------|
| `seed_demo_users` | Demo kullanıcılar (admin/öğrenci/akademisyen) |
| `seed_comprehensive` | Kapsamlı veri: bölüm + program + kullanıcı + müfredat |
| `seed_real_data` | Şube + zaman dilimi + kayıt akışı verisi |
| `seed_students_transcripts` | Öğrenci profili + transkript |
| **`seed_danishman`** | Musa Arslan + İbrahim Uğur Yılmaz → `is_advisor=True` |
| **`seed_yzm_weekly`** | YZM 2025-2026 **Güz** programı (derslikler dahil) |
| **`seed_yzm_bahar`** | YZM 2025-2026 **Bahar** programı |
| **`seed_ins_guz`** | İnşaat 2025-2026 Güz |
| **`seed_ins_bahar`** | İnşaat 2025-2026 Bahar |
| **`seed_esm_bahar`** | Enerji Sistemleri 2025-2026 Bahar |
| `set_active_semester --year=2025-2026 --term=fall` | Aktif dönemi ayarla |
| `set_founder_admin <kullanıcı>` | Kurucu yönetici atama |

Tümü **idempotent** — tekrar tekrar çalıştırılabilir.

---

## 🚢 Render Deploy

`entrypoint.sh` env değişkenleriyle deploy esnasında seed çalıştırır. Shell gerekmez.

Render Dashboard → Environment → ekleyin:

| Env Var | Açıklama |
|---------|----------|
| `SEED_COMPREHENSIVE=1` | İlk deploy için kapsamlı veri |
| `SEED_DANISHMAN=1` | Danışman atamaları |
| `SEED_YZM_WEEKLY=1` | YZM Güz |
| `SEED_YZM_BAHAR=1` | YZM Bahar |
| `SEED_INS_GUZ=1` | İnşaat Güz |
| `SEED_INS_BAHAR=1` | İnşaat Bahar |
| `SEED_ESM_BAHAR=1` | Enerji Bahar |
| `SET_ACTIVE_SEMESTER=1` | Aktif dönem ayarla |
| `FOUNDER_ADMIN_EMAIL=<email>` | Kurucu admin oluştur |

Deploy sonrası env'leri `0` yapın veya silin.

---

## 🧪 Test

```bash
python manage.py test                              # Django test runner
coverage run manage.py test && coverage report     # Coverage (eşik: %75)
pytest -m unit                                     # Pytest markerlı
make ci                                            # Linux/WSL: full kapı (security + tests + %80)
```

Ayrıntı: [`docs/TESTING.md`](docs/TESTING.md)

---

## 🔒 Güvenlik

- **RBAC:** `User.role` + view mixin'leri + `FounderAdminRequiredMixin`
- **Danışman kısıtı:** `InstructorProfile.is_advisor` boolean
- **CSRF + XSS:** Django'nun standart koruması
- **SQLi:** ORM kullanımı
- **Brute-force:** `LoginBruteForceMiddleware`
- **Throttling:** enrollment POST için `django-ratelimit`
- **Audit:** kritik olaylar `audit_logs` tablosunda
- **Secret tarama:** detect-secrets (Phase 9)

Politika: [`SECURITY.md`](SECURITY.md) · Özet: [`docs/SECURITY_OVERVIEW.md`](docs/SECURITY_OVERVIEW.md)

---

## 📅 Yeni Özellikler (Mayıs 2026)

- ✅ **`is_advisor` boolean alanı** — danışman olmayan hocalar danışmanlık akışına giremez
- ✅ **Sidebar rol-bazlı menü** — danışman olmayanlar sadece Devamsızlık + Kayıtlar/Notlar görür
- ✅ **Reddetme not akışı** — danışman red gerekçesi öğrenciye gösterilir
- ✅ **Devamsızlık güvenliği** — sadece ENROLLED öğrenciler; gelecek tarih bloku
- ✅ **Not validasyonu** — geçersiz harf notu (`Z`, `XX` vb.) ve 0-100 dışı sayısal reddedilir
- ✅ **Müfredat tabanlı program fallback** — kayıt yapmamış öğrenci programının müfredatını görür
- ✅ **Haftalık program overlap fix** — union-find ile çakışma grubu hesaplaması
- ✅ **Dark + Light tema kontrastı** — dropdown ve form alanları her iki temada okunabilir
- ✅ **3 yeni bölüm × 2 dönem ders programı** seed'i

---

## 🛠️ CI/CD

| Workflow | Tetik | Amaç |
|----------|-------|------|
| `ci.yml` | push/PR | Ruff + pip-audit + Bandit + test + Codecov + SBOM |
| `phase9-ci.yml` | push/PR | Marker testleri + migration smoke + detect-secrets |
| `deploy.yml` | main | GHCR imaj üretimi |
| `release.yml` | tag `v*` | İmaj + isteğe bağlı SSH/ECS deploy + smoke |
| `canary.yml` | cron / manuel | Üretim sentetik kontrolleri |

Sürüm akışı: [`RELEASE.md`](RELEASE.md) · Değişiklikler: [`CHANGELOG.md`](CHANGELOG.md)

---

## 🩺 Sağlık & Gözlemlenebilirlik

- `/health/live/` — uygulama ayakta mı?
- `/health/ready/` — DB hazır mı?
- Yanıt başlığı: `X-Request-ID` (istek korelasyonu)
- Log alanları: `request_id`, `service`, `event_type`, `actor_id`
- Ayrıntı: [`docs/observability.md`](docs/observability.md)

---

## 🆘 Sık Karşılaşılan Hatalar

| Belirti | Sebep | Çözüm |
|---------|-------|-------|
| `OperationalError` (MySQL) | DB yok / şifre yanlış | DB oluştur + `.env` `DB_*` kontrol |
| `auth plugin caching_sha2_password` | MySQL 8 plugin | `cryptography` kurulu olmalı |
| CSRF 403 | HTTPS / proxy | `DJANGO_CSRF_TRUSTED_ORIGINS` ekle |
| Dropdown beyaz/beyaz | CSS cache | Tarayıcıyı hard refresh (`Ctrl+Shift+R`) |
| YZM öğrenci ders programını görmüyor | Aktif dönem yok | `SET_ACTIVE_SEMESTER=1` çalıştır |
| Danışman menüsü görünmüyor | `is_advisor=False` | `seed_danishman` çalıştır |
| Program kartları üst üste | Eski algoritma cache | Sunucuyu yeniden başlat |

---

## 📚 Ek Belgeler

| Belge | İçerik |
|-------|--------|
| [`AGENTS.md`](AGENTS.md) | Geliştirici kuralları, mimari sözleşmeler |
| [`docs/PHASE_HISTORY.md`](docs/PHASE_HISTORY.md) | Phase 1–12 kronolojik gelişim |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Katkı rehberi |
| [`docs/TESTING.md`](docs/TESTING.md) | Test stratejisi |
| [`docs/runbooks/RUNBOOK.md`](docs/runbooks/RUNBOOK.md) | Operasyon runbook'u |
| [`docs/deployment/production-automation.md`](docs/deployment/production-automation.md) | Üretim otomasyonu |
| [`docs/runbooks/rollback-runbook.md`](docs/runbooks/rollback-runbook.md) | Geri alma |

---

## 🗺️ Roadmap

- Redis önbellek + invalidation stratejisi
- Tam ECS/ECR pipeline (task definition otomatik güncelleme)
- Genişletilmiş **i18n** (en/tr çift dil)
- DRF API katmanı (mobil istemci için)
- CSV/PDF rapor dışa aktarımı (rol bazlı)
- Çakışma uyarısı önizleme (ders seçim ekranında)

---

## 🤝 Katkı

PR açmadan önce: [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) okuyun ve [`.github/pull_request_template.md`](.github/pull_request_template.md) doldurun.

```bash
# Branch
git checkout -b feature/yeni-ozellik

# Pre-commit kontrolleri
ruff check .
python manage.py test
coverage report
```

---

## 📜 Lisans

MIT — ayrıntılar: [`LICENSE`](LICENSE)

---

**Geliştirici:** [Himmet Demir](https://github.com/HimmetDemir45) · KTÜ OF Teknoloji Fakültesi · Yazılım Mühendisliği Lisans
