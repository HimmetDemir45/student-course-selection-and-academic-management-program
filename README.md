# Student Course Selection and Academic Management Program (Django)

[![codecov](https://codecov.io/gh/HimmetDemir45/student-course-selection-and-academic-management-program/graph/badge.svg)](https://codecov.io/gh/HimmetDemir45/student-course-selection-and-academic-management-program)
[![CI](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/actions/workflows/ci.yml/badge.svg)](https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/actions/workflows/ci.yml)

## Proje Ozeti

Universite dersi icin **ogrenci ders secimi ve akademik yonetim** platformu. Stack: **Django 5**, **MySQL**, **Docker**, AWS (RDS + S3) ile production hazirligi.

## Teknoloji

- Python 3.12+
- Django 5.1 LTS patchline (pins: `requirements.txt`)
- MySQL (PyMySQL + `cryptography`)
- django-environ, django-storages, boto3, Gunicorn
- Docker / docker-compose
- GitHub Actions (CI + GHCR image)

## Hizli baslangic (yerel, venv)

1. `python -m venv .venv` ve aktivasyon
2. `pip install -r requirements.txt`
3. `.env.example` dosyasini `.env` olarak kopyalayin ve DB bilgilerini duzenleyin
4. `python manage.py migrate`
5. (Istege bagli) `python manage.py loaddata phase4_seed` — seed sifreleri dokumanda
6. `python manage.py runserver`

Varsayilan ayar modulu: `config.settings.dev` (`manage.py` / `wsgi.py`).

## Settings yapisi

| Modul | Kullanim |
|--------|----------|
| `config.settings.base` | Ortak ayarlar (DB URL veya DB\_\*, logging, apps) |
| `config.settings.dev` | Yerel gelistirme (`DEBUG=True`) |
| `config.settings.prod` | Production (S3, guvenlik basliklari, `DEBUG=False`) |
| `config.settings.ci` | GitHub Actions + MySQL servis konteyneri |
| `config.settings.development` | Eski import yolu; `dev` ile ayni |
| `config.settings.production` | Eski import yolu; `prod` ile ayni |

Ortam degiskeni: `DJANGO_SETTINGS_MODULE` (ornegin `config.settings.prod`).

---

## Phase 6 — Hardening, Performance, Security (ozet)

Bu fazda odak:

- **Performans**: `select_related` / `prefetch_related` ve list annotate (or. section doluluk), DB indexleri (`idx_enrollment_section_status`, `idx_timeslot_section_weekday`), ana sayfada dusuk TTL cache (`core/services/cached_stats.py`), agir sorgu notlari (`enrollment_rules` docstring).
- **Guvenlik**: Log satirlarinda hassas pattern maskeleme (`core/logging_utils.RedactingFormatter`), prod cookie/tls ayarlari (`config/settings/prod.py`), CI `pip-audit --strict`, Django guncel pin, `SECURITY.md`, Dependabot (`/.github/dependabot.yml`).
- **Test/coverage**: RBAC, CSRF, enrollment HTTP kenarlari, GPA baglam testleri (`core/test_phase6.py`); `pyproject.toml` icinde `fail_under = 75`.
- **`.gitignore`**: `.env`, `.env.*`, `*.sql`, anahtar dosyalari, coverage artefactlari vb. (tam liste dosyada).

GitHub repo ayarlari (org izin veriyorsa): **Dependabot alerts**, **Dependabot security updates**, **Secret scanning**, **Push protection** acilmali. Detay: `SECURITY.md`.

### .gitignore politikasi

- `.env` ve `.env.*` **commitlenmez**; ornekler `.env.example` ve `.env.production.example` ile tutulur.
- `media/`, `staticfiles/`, `*.sql`, `*.pem` vb. disarida tutulur; tam pattern `/.gitignore` icinde.

### Hassas dosya yanlislikla commit edildiyse (acil)

1. Dosyayi indexten cikar (depo kokunden): `git rm --cached <dosya-yolu>`
2. `.gitignore` satirinin dosyayi kapsadigindan emin ol.
3. Commit: `git commit -m "chore: remove sensitive tracked files"`
4. **Gecmis** hala hassas veri tasiyorsa: GitHub “secret scanning” uyarisini izleyin; gerekirse `git filter-repo` / profesyonel destek ile tarih temizligi ve **sifre/anahtar rotasyonu** yapin (`SECURITY.md` runbook).

### Guvenlik kontrol listesi (kisa)

- [ ] Prod `DEBUG=False`, `DJANGO_SECRET_KEY` yalnizca ortamda
- [ ] `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` HTTPS ile dolduruldu
- [ ] RDS/S3 kimlik bilgileri repoda yok; IAM role tercih edildi mi?
- [ ] `pip-audit` / Dependabot uyarıları kapatılmadan merge yok
- [ ] Push protection + secret scanning acik

### Performance checklist (kisa)

- [ ] Yeni list/detail view’larda N+1 kontrolu (`select_related` / `prefetch_related` / `annotate`)
- [ ] Sik filtrelenen FK/status alanlarinda index (migration ile)
- [ ] Agregat sayimlar icin cache veya annotate (TTL kisa tutulur, invalidation stratejisi bilinir)
- [ ] Yerel profil icin (yalniz dev): `django-debug-toolbar` — `pip install django-debug-toolbar`, `INSTALLED_APPS` + `MIDDLEWARE` ve `INTERNAL_IPS` ekleyin; **prod’da acmayin.**

### Branch protection onerisi (GitHub)

`main` (ve gerekiyorsa `develop`) icin:

- Required status checks: **lint**, **security**, **test** (workflow job isimleri)
- Require pull request reviews (en az 1 onay)
- Dismiss stale approvals when new commits are pushed
- Block force pushes; uygunsa “require linear history”
- Opsiyonel: **CODEOWNERS** ile kritik yollar; sablon `CODEOWNERS` dosyasinda (placeholder yorumlari).

---

## Phase 7 — Release readiness, operations, go-live

- **SemVer + changelog**: `RELEASE.md`, `CHANGELOG.md` (Keep a Changelog); tag ornegi `v1.0.0`, oncesi `v1.0.0-rc.1`.
- **Workflows**: `/.github/workflows/release.yml` (tag `v*` → CI → GHCR imaji semver + `sha-` + opsiyonel uzak smoke icin `HEALTHCHECK_BASE_URL` secret); `smoke-tests.yml` (`workflow_dispatch` ile canli URL).
- **Runbooklar**: `docs/runbooks/` — deployment, rollback, incident response.
- **Operasyon**: `docs/operations/` — backup/restore/DR, monitoring & alerting checklist.
- **UAT / canli**: `docs/go-live-checklist.md`; deploy sonrasi `docs/post-release-verification.md`.
- **Istek korelasyonu**: yanit basligi `X-Request-ID` (`core/middleware/request_id.py`).

---

## Phase 8 — Advanced production hardening, reliability, observability

- **Release otomasyonu**: `release.yml` — `quality-gate` (CI) → GHCR → **deploy-prod** (`vars.DEPLOY_MODE`: `ssh` | `ecs` | ayarlanmazsa atlanir) → **GitHub Environment `production`** (manuel onay) → smoke. Detay: `docs/deployment/production-automation.md`.
- **Codecov + SARIF**: Coverage `codecov-action`; Bandit SARIF → Code Scanning; SBOM CycloneDX artifact. Rehber: `docs/security/code-scanning-and-secrets.md`.
- **JSON loglama**: `DJANGO_LOG_JSON=True` + structlog (`core/structlog_config.py`); dev’de metin + `request_id`. Alanlar: `docs/observability.md`.
- **Enrollment yarisi**: `select_for_update` + `transaction.atomic` (`core/services/enrollment_atomic.py`); MySQL concurrency testi; POST rate limit (`django-ratelimit`). Detay: `docs/reliability/concurrency-and-locking.md`.
- **Canary**: `.github/workflows/canary.yml` (15 dk, `CANARY_BASE_URL` secret); PagerDuty/CloudWatch zinciri `docs/observability.md`.
- **SLO / dry-run / maliyet**: `docs/sre/sli-slo.md`, `docs/operations/backup-restore-dry-run.md`, `docs/observability.md` son bolum.
- **Feature flags**: `FEATURE_FLAGS` / `FEATURE_ENROLLMENT_RATELIMIT`, `RATELIMIT_ENABLE` (`config/settings/base.py`); yardimci `core/feature_flags.py`.

### Coverage + SARIF nasil okunur?

- **Codecov**: PR’da diff ve proje sayfasinda trend; dusuk coverage yeni kod yollarinda risk isareti.
- **Security tab**: Bandit SARIF uyarıları; “dismiss” veya `.bandit` ile exclude (dikkatli).

---

## Phase 5 — Deployment Overview

Bu fazda hedeflenenler:

- **Ayar ayrimi**: `dev` / `prod`, env tabanli gizli bilgiler
- **Docker**: Gunicorn, migrate + collectstatic entrypoint
- **AWS**: RDS (`DATABASE_URL`), S3 (static + media, `django-storages`)
- **Guvenlik**: HTTPS, HSTS, guvenli cerezler, CSRF trusted origins
- **Health**: `/health/live/`, `/health/ready/`
- **Logging**: stdout (CloudWatch agent / container log driver ile toplanabilir)
- **CI/CD**: GitHub Actions — lint (config), test (MySQL), deploy pipeline (GHCR push)

---

## Local Docker Development

Gereksinimler: Docker Desktop.

```bash
docker compose up --build
```

- Web: `http://localhost:8000`
- MySQL: host `localhost:3306` (varsayilan sifreler `docker-compose.yml` icinde; uretimde kullanmayin)
- Ortam: `DJANGO_SETTINGS_MODULE=config.settings.dev`, `DATABASE_URL` compose icinde `db` servisine isaret eder

Durdurma:

```bash
docker compose down
```

---

## Production Deployment (AWS)

Tipik mimari:

1. **RDS MySQL**: baglanti `DATABASE_URL` ile (kullanici/sifre URL-encode edilmeli).
2. **S3 bucket**: static + media; IAM kullanicisi veya EC2 instance profile ile `AWS_*` (anahtar bos birakilabilir, boto3 zinciri kullanilir).
3. **EC2 (veya ECS)**: Docker image calistirma, `.env.production` veya Secrets Manager.
4. **ALB / Nginx**: TLS sonlandirma; `SECURE_PROXY_SSL_HEADER` prod ayarinda tanimli.

Ornek prod compose:

```bash
cp .env.production.example .env.production
# .env.production dosyasini doldurun (commit etmeyin)
docker compose -f docker-compose.prod.yml up -d --build
```

Container icinde:

- `migrate` ve `collectstatic --noinput` `entrypoint.sh` ile calisir
- Gunicorn `0.0.0.0:8000`

**CloudWatch logging**: Uygulama stdout’a yazar; EC2’de CloudWatch agent veya ECS `awslogs` driver ile akis toplanir (detay AWS dokumaninda).

---

## GitHub Actions CI/CD

### CI (`/.github/workflows/ci.yml`)

- Tetikleyiciler: `push` / `pull_request` (`main`, `develop`), `workflow_call` (release)
- **lint**: `ruff check .`
- **security**: `pip-audit --strict` + **Bandit** SARIF → Code Scanning upload
- **test**: MySQL, `coverage run manage.py test`, `coverage report`, **Codecov** upload (`CODECOV_TOKEN` opsiyonel), **SBOM** artifact (CycloneDX)
- `permissions: security-events: write` (SARIF)

### Deploy (`/.github/workflows/deploy.yml`)

- `main` push veya `workflow_dispatch`
- Docker image build + **GHCR** push (`ghcr.io/<owner>/<repo>:latest` ve SHA etiketi)
- EC2/ECS uzerinde manuel veya ek workflow ile: `docker pull` + `docker compose -f docker-compose.prod.yml up -d`

### Release (`/.github/workflows/release.yml`)

- Tetikleyici: **tag** `v*`
- **quality-gate**: reusable CI
- **build-and-push**: GHCR (semver + `sha-`)
- **deploy-prod**: `vars.DEPLOY_MODE` = `ssh` (appleboy/ssh-action + `EC2_*`) veya `ecs` (`aws ecs update-service` + wait); **Environment `production`** onayi
- **post-release-smoke**: `HEALTHCHECK_BASE_URL`
- **notify-rollback-hint**: herhangi bir job `failure` ise ozet

### Canary (`/.github/workflows/canary.yml`)

- `cron: */15 * * * *` + `workflow_dispatch`; secret `CANARY_BASE_URL`

### Smoke tests (`/.github/workflows/smoke-tests.yml`)

- Yalnizca **workflow_dispatch**; `base_url` girerek canli/dogru ortamda health, login sayfasi, ana sayfa ve ders listesi HTTP kontrolleri.

### Onerilen GitHub Secrets / degiskenler

| Secret / degisken | Aciklama |
|-------------------|----------|
| `GITHUB_TOKEN` | GHCR push icin (varsayilan, `packages: write` gerekir) |
| `DJANGO_SECRET_KEY` | Prod ortamda container/env inject (Actions icinde opsiyonel) |
| `DATABASE_URL` | RDS baglantisi (Actions deploy scriptinde kullanilacaksa) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 erisimi (IAM role tercih edilebilir) |
| `AWS_STORAGE_BUCKET_NAME` / `AWS_S3_REGION_NAME` | Bucket bilgisi |
| `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` | SSH ile sunucu deploy otomasyonu eklerseniz |
| `HEALTHCHECK_BASE_URL` | Deploy sonrasi `curl` icin public URL (manuel script) |

---

## Required Environment Variables

### Development (`dev`)

- `DJANGO_SECRET_KEY` (veya geriye donuk `SECRET_KEY`)
- `DJANGO_DEBUG` (veya `DEBUG`)
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL` **veya** `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `LOG_LEVEL` (opsiyonel)

### Production (`prod`)

- `DJANGO_SECRET_KEY` — **zorunlu**, kod icinde sabit yok
- `DJANGO_ALLOWED_HOSTS` — **zorunlu**
- `DJANGO_CSRF_TRUSTED_ORIGINS` — HTTPS origin listesi (bos liste mumkun, form tabanli POST icin genelde doldurulmali)
- `DJANGO_USE_X_FORWARDED_HOST` — opsiyonel (varsayilan `True`); reverse proxy arkasi icin
- `DATABASE_URL` — **zorunlu**
- `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` — **zorunlu**
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — opsiyonel (IAM role ile bos)
- `AWS_S3_CUSTOM_DOMAIN` — opsiyonel (CDN)

Guvenlik detaylari: `SECURITY.md`.

---

## Health Checks

| Endpoint | Amac |
|----------|------|
| `GET /health/live/` | Surec ayakta (load balancer Liveness) |
| `GET /health/ready/` | Veritabani baglantisi (Readiness); basarisizsa **503** |

Ornek:

```bash
curl -fsS http://localhost:8000/health/ready/
```

---

## Rollback Strategy

1. **Onceki image**: GHCR’da SHA etiketli imajlari saklayin; `docker pull ghcr.io/OWNER/REPO:<onceki-sha>` + `docker compose up -d`
2. **Veritabani**: Kritik migration oncesi RDS snapshot; geri donuste migration `reverse` veya snapshot restore
3. **Static**: S3 surumleme bucket policy / object versioning ile eski static geri alinabilir
4. **Hizli trafik kesme**: ALB target group’tan instance cikarip eski surume donun

---

## Phase 4 ozeti (is kurallari)

- Kayit kurallari: `core/services/` (kapasite, onkosul, cakisma, pencereler, GPA, audit)
- Ogrenci: `/enrollments/sections/`, `/students/transcript/`
- Ogretim uyesi: `/academic/instructor/enrollments/`
- Brute-force: `LoginBruteForceMiddleware`

---

## Calistirma komutlari (ozet)

```bash
# Yerel
python manage.py migrate
python manage.py test
python manage.py runserver

# Dev tooling (lint, coverage, pip-audit)
python -m pip install -r requirements-dev.txt

# Lint (CI ile ayni kapsam)
python -m ruff check .

# Coverage (esik pyproject.toml)
coverage erase
coverage run manage.py test
coverage report
coverage html   # istege bagli: htmlcov/
# Windows PowerShell 5.1 tek satir (&& yerine ; kullanin) veya PowerShell 7+ ile &&:
# python -m coverage erase; python -m coverage run manage.py test; python -m coverage report

# Bagimlilik guvenlik taramasi (CI ile ayni politika)
python -m pip_audit -r requirements.txt --strict

# Docker local
docker compose up --build

# Docker prod stack (RDS + S3 env ile)
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Bilinen riskler / TODO

- `SECURE_SSL_REDIRECT=True` yalnizca TLS sonlandiran proxy (ALB/Nginx) arkasında kullanilmali; aksi halde redirect dongusu riski
- MySQL `caching_sha2_password` icin istemcide `cryptography` gerekir (`requirements.txt` icinde)
- Prod’da S3 bucket IAM ve CORS politikalari ayri yapilandirilmalidir
- Tam otomatik EC2 deploy adimi repoya orgutunuze gore eklenmelidir (SSH, ECS task definition, vb.)
- **ECS tam otomasyon**: Task definition imaj guncelleme + ECR push zinciri genisletilebilir (Phase 9).
- **Cache invalidation**: Ana sayfa önbelleği kısa TTL ile sınırlıdır; yoğun yazma senaryolarında Redis + explicit invalidation düşünülebilir.

---

## Not

Flask’tan Django’ya gecis ve modul genislemesi surmektedir; `migration_notes.md` ve `AGENTS.md` proje kurallari icin bakiniz.
