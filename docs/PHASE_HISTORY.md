# Phase 1–12 Teknik Geçmiş

Bu belge mimari kararları, önemli dosya yollarını ve fazlar arası bağımlılıkları **teknik** düzeyde özetler. Kullanıcı odaklı özet için `README.md` bölümü «Phase 1–12 Detaylı Yolculuk» kullanılabilir.

---

## Phase 1 — Django iskeleti ve proje omurgası

**Hedef:** Flask sonrası tek gerçek runtime olarak Django 5 tabanı; `config/` paketi, `manage.py`, ASGI/WSGI, merkezi URL ve şablon kökü.

**Önemli artefaktlar:** `config/settings/base.py`, `config/urls.py`, `templates/base.html`, `core/` (genel sayfalar, sağlık kontrolleri).

**Kazanım:** Tutarlı ayırım (MVT → ders gereği MVC benzeri katmanlar); tüm uygulama rotaları `config/urls.py` üzerinden include.

**Sonraki faz etkisi:** Auth ve domain uygulamaları bu iskelete takıldı.

---

## Phase 2 — Kimlik: hesaplar ve oturum

**Hedef:** Kayıt, giriş/çıkış, özelleştirilmiş kullanıcı modeli.

**Önemli artefaktlar:** `accounts/models.py` (`AUTH_USER_MODEL`), `accounts/views.py`, `accounts/forms.py`, `accounts/urls.py`, oturum yönlendirmeleri `config/settings/base.py` (`LOGIN_URL`, `LOGIN_REDIRECT_URL`).

**Kazanım:** Rol alanı ile RBAC temeli; Django güvenli parola doğrulayıcıları.

**Sonraki faz etkisi:** Tüm korumalı view’lar `login_required` / rol mixin’leri ile bu modele dayanır.

---

## Phase 3 — Öğrenci, öğretim üyesi ve ders varlıkları

**Hedef:** İlişkisel şema genişlemesi; CRUD akışları ve liste/detay şablonları.

**Önemli artefaktlar:** `students/`, `instructors/`, `courses/` (modeller, `urls.py`, `views.py`, şablonlar).

**Kazanım:** En az 12 ilişkili tablo hedefi için domain tabanları.

**Sonraki faz etkisi:** Kayıt ve notlandırma bu varlıklara FK ile bağlanır.

---

## Phase 4 — Kayıt kuralları, GPA, transkript ve denetim

**Hedef:** Kapasite, önkoşul, zaman çakışması, add/drop penceresi, GPA; öğrenci transkripti; öğretim üyesi not girişi; audit olayları.

**Önemli artefaktlar:** `core/services/` (iş kuralları), `enrollments/`, `academic/`, `audit_logs/`, `core/test_phase4.py`, `core/fixtures/phase4_seed.json`.

**Kazanım:** Tekrar kullanılabilir servis katmanı; otomatik testlerle doğrulanan iş kuralları.

**Sonraki faz etkisi:** Performans ve eşzamanlılık optimizasyonları bu servislerin etrafında yapıldı.

---

## Phase 5 — Konteyner ve AWS uyumlu dağıtım

**Hedef:** `dev`/`prod` ayrımı, Docker, Gunicorn, RDS + S3, sağlık uçları.

**Önemli artefaktlar:** `docker-compose.yml`, `docker-compose.prod.yml`, `Dockerfile`, `entrypoint.sh`, `config/settings/prod.py`, `.env.production.example`, `core/views.py` (`health_live`, `health_ready`).

**Kazanım:** Yerel ve bulut benzeri çalışma modeli.

**Sonraki faz etkisi:** CI imaj üretimi ve GitHub Actions dağıtım işleri bu yapıyı kullanır.

---

## Phase 6 — Sertleştirme, performans, güvenlik taraması

**Hedef:** N+1 azaltma, indeksler, kısa TTL önbellek, log maskeleme, prod çerez/TLS, test genişlemesi, `.gitignore` politikası.

**Önemli artefaktlar:** `core/services/cached_stats.py`, `core/logging_utils.py`, `core/test_phase6.py`, `SECURITY.md`, `.github/dependabot.yml`, `pyproject.toml` coverage `fail_under = 75`.

**Kazanım:** Ölçülebilir güvenlik ve performans refleksi.

**Sonraki faz etkisi:** Release ve gözlemlenebilirlik üzerine güvenli temel.

---

## Phase 7 — Sürüm, operasyon ve canlıya çıkış

**Hedef:** SemVer, changelog, release/smoke workflow’ları, runbook’lar, istek korelasyonu.

**Önemli artefaktlar:** `RELEASE.md`, `CHANGELOG.md`, `.github/workflows/release.yml`, `.github/workflows/smoke-tests.yml`, `docs/runbooks/*`, `docs/go-live-checklist.md`, `core/middleware/request_id.py` (`X-Request-ID`).

**Kazanım:** Tekrarlanabilir yayın ve olay müdahalesi dokümantasyonu.

**Sonraki faz etkisi:** Otomasyon ve SLO dokümantasyonu bu sürece bağlandı.

---

## Phase 8 — İleri üretim: otomasyon, gözlemlenebilirlik, yarış güvenliği

**Hedef:** Release içinde SSH/ECS dağıtım seçenekleri, Codecov + Bandit SARIF + SBOM, structlog JSON, enrollment `select_for_update`, canary workflow, özellik bayrakları.

**Önemli artefaktlar:** `.github/workflows/release.yml`, `.github/workflows/canary.yml`, `core/services/enrollment_atomic.py`, `core/structlog_config.py`, `core/feature_flags.py`, `docs/deployment/production-automation.md`, `docs/observability.md`, `docs/reliability/concurrency-and-locking.md`, `docs/sre/sli-slo.md`.

**Kazanım:** Üretim operasyonları ile kod tabanı hizası.

**Sonraki faz etkisi:** Daha sıkı CI kapıları ve test ayrıştırması için zemin.

---

## Phase 9 — Gelişmiş CI kapıları ve sürüm runbook’u

**Hedef:** Pytest marker tabanlı test ayrımı, migration apply/rollback smoke, secret tarama (detect-secrets), ayrı release workflow özeti.

**Önemli artefaktlar:** `.github/workflows/phase9-ci.yml`, `.github/workflows/phase9-release.yml`, `Makefile`, `scripts/smoke_migration.sh`, `scripts/synthetic_canary.sh`, `docs/PHASE9_RUNBOOK.md`, `.secrets.baseline`.

**Kazanım:** «Merge öncesi» ve «tag öncesi» için ek güvence katmanı.

**Sonraki faz etkisi:** Gözlemlenebilirlik ve test altyapısı iyileştirmeleri için çerçeve.

---

## Phase 10 — Test altyapısı ve log `service` alanı

**Hedef:** Pytest + MySQL ortamında bağlantı havuzu / zaman aşımı ayarları; loglarda servis adı ayrımı.

**Önemli artefaktlar:** `tests/conftest.py`, `tests/enrollments/test_enrollment_concurrency.py`, `config/settings/base.py` (`LOG_SERVICE_NAME`), `docs/observability.md` (Phase 10 notları).

**Kazanım:** Çok servisli gelecek log senaryolarına uyum.

**Sonraki faz etkisi:** UI ve yönetişim özellikleri için stabil test zemini.

---

## Phase 11 — Kurucu onayı ve arayüz cilası

**Hedef:** Tek kurucu yöneticinin web üzerinden admin talebini onaylaması; Bootstrap üzerinde tutarlı tablo/kart/nav stilleri.

**Önemli artefaktlar:** `accounts/migrations/0002_phase11_founder_adminrequest.py`, `accounts/models.py` (`AdminRequest`, `is_founder_admin`), `dashboard/views.py` (kuyruk/onay/red), `accounts/management/commands/set_founder_admin.py`, `tests/test_admin_request.py`, `static/css/phase11.css`, ilgili şablon sınıfları (`phase11-*`).

**Kazanım:** Güvenli ayrıcalıklı iş akışı ve daha okunur UI.

**Sonraki faz etkisi:** Dokümantasyon ve onboarding (Phase 12) bu özellikleri anlatır.

---

## Phase 12 — Dokümantasyon ve operasyonel tamamlama

**Hedef:** Türkçe üretim kalitesinde README; teknik/operasyonel/kullanıcı odaklı tamamlayıcı `docs/` seti; lisans dosyası.

**Önemli artefaktlar:** `README.md`, `docs/PHASE_HISTORY.md`, `docs/RUNBOOK.md`, `docs/CONTRIBUTING.md`, `docs/TESTING.md`, `docs/SECURITY_OVERVIEW.md`, `LICENSE`.

**Kazanım:** Yeni geliştirici ve operatör için tek giriş noktası; faz geçmişi izlenebilir.

**Sonraki faz etkisi:** Roadmap maddeleri (ör. Redis önbellek, tam ECS pipeline, genişletilmiş i18n) için referans çizgisi.
