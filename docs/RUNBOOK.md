# Operasyonel Kısa Rehber (Deploy / Rollback / Incident)

Bu dosya üretim ve ders ortamı için **tek sayfalık** özet sağlar. Ayrıntılar: `docs/runbooks/deployment-runbook.md`, `docs/runbooks/rollback-runbook.md`, `docs/runbooks/incident-response.md`, `docs/PHASE9_RUNBOOK.md`, `RELEASE.md`.

## Ön koşullar

| Öğe | Not |
|-----|-----|
| İmaj | `ghcr.io/HimmetDemir45/student-course-selection-and-academic-management-program:<tag>` |
| Ortam | `DJANGO_SETTINGS_MODULE=config.settings.prod`, `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, S3 `AWS_*` |
| Sağlık | `GET /health/live/`, `GET /health/ready/` (503 = DB sorunu) |

## Dağıtım (özet)

1. **Ön kontrol**: `python manage.py check` (CI ile aynı ayar modülü tercih edilir).
2. **Migrasyon**: `python manage.py migrate --noinput` (kritik sürümlerde önce RDS snapshot).
3. **Statik**: `collectstatic` (Docker `entrypoint` ile otomatik; bare metal’de ayrı adım).
4. **Trafik**: Yeni görev/instance sağlıklı olunca load balancer’a ekle.
5. **Doğrulama**: `docs/post-release-verification.md` veya GitHub **Smoke tests** workflow (`workflow_dispatch` + `base_url`).

## Rollback (uygulama)

1. Önceki **immutability etiketli** imaja dön (`sha-…` veya son stabil semver).
2. `docker compose -f docker-compose.prod.yml pull && up -d` (veya ECS task definition önceki revision).
3. Migrasyon geri alma gerekiyorsa: `python manage.py migrate <app> <önceki_migration>` — **veri kaybı riski**; tercih genelde snapshot restore.
4. `/health/ready/` ve kritik kullanıcı akışları (giriş, ders listesi, kayıt sayfası).

## Rollback (veritabanı)

- Tercih: **RDS snapshot restore** (RPO/RTO planına göre).
- Küçük adımlar: migration `reverse` yalnızca geri dönüşü güvenli olduğunda; yedekleme/DR: `docs/operations/backup-restore-and-dr.md`.

## Incident (L1 triage)

| Belirti | İlk adım |
|---------|----------|
| 503 `/health/ready/` | DB bağlantısı, güvenlik grubu, `DATABASE_URL` |
| 403 toplu | `CSRF_TRUSTED_ORIGINS`, proxy TLS başlıkları, oturum çerezi |
| 5xx artışı | Son deploy mü? `X-Request-ID` ile log korelasyonu |
| Brute-force / kilit | `LoginBruteForceMiddleware` eşikleri, IP/ kullanıcı logları |

Yükseltme: `docs/runbooks/incident-response.md`, `SECURITY.md` (secret sızıntısı).

## Canary ve sentetik kontrol

- Zamanlanmış: `.github/workflows/canary.yml` (`CANARY_BASE_URL` secret).
- Yerel/özel: `make canary` (`scripts/synthetic_canary.sh`).

## İletişim ve kayıt

- Olay zaman çizelgesi, etkilenen sürüm, rollback kararı ve kök neden — dahili wiki veya ders günlüğüne yazın.
