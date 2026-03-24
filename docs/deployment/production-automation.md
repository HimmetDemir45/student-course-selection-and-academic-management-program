# Production automation (release workflow)

## Mimari (metin akis)

```
git tag vX.Y.Z && git push
    -> workflow: quality-gate (CI: lint, bandit+SARIF, pip-audit, test+coverage+Codecov+SBOM)
    -> build-and-push (GHCR: semver + sha- etiketleri)
    -> deploy-prod (opsiyonel: SSH veya ECS, Environment "production" onayi)
    -> post-release-smoke (HEALTHCHECK_BASE_URL)
    -> notify-rollback-hint (herhangi bir failure ise ozet)
```

## GitHub Environment: production

**Settings → Environments → production**

- Required reviewers: en az 1 kisi (release manager).
- Deployment branches: `protected branches` veya tag pattern (org politikasına gore).

`deploy-prod` job’u `environment: production` kullanir; onay gelmeden SSH/ECS adimlari calismaz.

## Repository variables (plaintext)

| Variable | Ornek | Aciklama |
|----------|-------|----------|
| `DEPLOY_MODE` | `skip` / `ssh` / `ecs` | `skip`: yalnizca imaj push |
| `EC2_DEPLOY_PATH` | `/opt/student-app` | SSH modunda `cd` hedefi |
| `AWS_REGION` | `eu-central-1` | ECS modu |
| `ECS_CLUSTER` | `prod-cluster` | ECS |
| `ECS_SERVICE` | `web-service` | ECS |

## Secrets (placeholder isimleri)

| Secret | Kullanim |
|--------|----------|
| `EC2_HOST` | SSH hedef IP/DNS |
| `EC2_USER` | SSH kullanici |
| `EC2_SSH_KEY` | Private key (PEM icerigi) |
| `AWS_ACCESS_KEY_ID` | ECS modu (tercihen OIDC + role) |
| `AWS_SECRET_ACCESS_KEY` | ECS modu |
| `HEALTHCHECK_BASE_URL` | Deploy sonrasi smoke (`https://...`) |
| `CANARY_BASE_URL` | Ayri secret olarak canary workflow (opsiyonel) |

**Gerçek degerleri repoya yazmayin.**

## SSH modu (MODE 1)

Sunucuda `docker compose -f docker-compose.prod.yml` kullanildigi varsayilir. Compose dosyasinin imaj etiketini `IMAGE_TAG` veya `.env` ile `${{ github.ref_name }}` ile hizalayin (ornek: `image: ghcr.io/org/repo:${IMAGE_TAG:-latest}`).

## ECS modu (MODE 2)

- Task definition’da imaj URI’sini yeni tag ile guncellemek icin genelde ayri bir adim (render JSON + `aws ecs register-task-definition`) gerekir; bu workflow **force-new-deployment** ile mevcut task def’taki imaji ceker — imaj tag’i ECS’te zaten guncellenmis olmali (CI’dan ECR push veya manuel).
- Tam otomasyon icin: build sonrasi ECR push + task def guncelleme adimini genisletin (Phase 9 adayi).

## Rollback karar kriterleri

- Smoke veya health basarisiz → onceki `v*` veya `sha-*` imajina don.
- Migration geri alinamazsa → DB snapshot runbook (`docs/runbooks/rollback-runbook.md`).

## Zero-downtime migrations (expand/contract)

1. **Expand**: Yeni kolon/tablo ekle (nullable veya default ile); eski kod calismaya devam eder.
2. **Migrate data**: Arka plan job ile doldur.
3. **Deploy** yeni uygulama kodu yeni alani kullanir.
4. **Contract**: Eski kolonu kaldiran migration (eski surum kapali iken).

Kirici migration’lari maintenance window ile yapin.
