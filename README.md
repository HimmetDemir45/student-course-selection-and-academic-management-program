# Student Course Selection and Academic Management Program (Django)

## Proje Ozeti

Universite dersi icin **ogrenci ders secimi ve akademik yonetim** platformu. Stack: **Django 5**, **MySQL**, **Docker**, AWS (RDS + S3) ile production hazirligi.

## Teknoloji

- Python 3.12+
- Django 5.1
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

- Tetikleyiciler: `push` / `pull_request` (`main`, `develop`)
- Adimlar: bagimlilik kurulumu, `ruff` ( `config/` + `manage.py` ), `manage.py check`, `migrate`, `test`
- MySQL 8.0 service + `DJANGO_SETTINGS_MODULE=config.settings.ci`

### Deploy (`/.github/workflows/deploy.yml`)

- `main` push veya `workflow_dispatch`
- Docker image build + **GHCR** push (`ghcr.io/<owner>/<repo>:latest` ve SHA etiketi)
- EC2/ECS uzerinde manuel veya ek workflow ile: `docker pull` + `docker compose -f docker-compose.prod.yml up -d`

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
- `DATABASE_URL` — **zorunlu**
- `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` — **zorunlu**
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — opsiyonel (IAM role ile bos)
- `AWS_S3_CUSTOM_DOMAIN` — opsiyonel (CDN)

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

# Docker local
docker compose up --build

# Docker prod stack (RDS + S3 env ile)
docker compose -f docker-compose.prod.yml up -d --build

# Lint (config odakli, CI ile uyumlu)
python -m pip install ruff
python -m ruff check config manage.py
```

---

## Bilinen riskler / TODO

- `SECURE_SSL_REDIRECT=True` yalnizca TLS sonlandiran proxy (ALB/Nginx) arkasında kullanilmali; aksi halde redirect dongusu riski
- MySQL `caching_sha2_password` icin istemcide `cryptography` gerekir (`requirements.txt` icinde)
- Prod’da S3 bucket IAM ve CORS politikalari ayri yapilandirilmalidir
- Tam otomatik EC2 deploy adimi repoya orgutunuze gore eklenmelidir (SSH, ECS task definition, vb.)

---

## Not

Flask’tan Django’ya gecis ve modul genislemesi surmektedir; `migration_notes.md` ve `AGENTS.md` proje kurallari icin bakiniz.
