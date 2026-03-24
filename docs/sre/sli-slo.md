# SLI / SLO (ornek hedefler — org’a gore degistirin)

## SLI tanimlari

| SLI | Olcum |
|-----|--------|
| **Availability** | Basarili `health/ready` synthetic / ALB health |
| **Error rate** | HTTP 5xx / tum istekler (ALB veya app metric) |
| **Latency** | ALB `TargetResponseTime` p95 |

## Ornek aylik SLO

| SLO | Hedef | Not |
|-----|-------|-----|
| Uptime | 99.5% | ~3.6 saat ayda izinli downtime |
| 5xx orani | < 0.5% | Trafik spike haric |
| API p95 latency | < 2s | Agir rapor sayfalari haric tutulabilir |

## Incident sirasinda bakilacaklar

1. CloudWatch / ALB dashboard: 4xx/5xx, latency, target health.
2. Uygulama loglari: `request_id` ile kullanici bildirimi eslestirme (`docs/observability.md`).
3. RDS: baglanti sayisi, CPU, depolama.
4. Son deploy / migration: release workflow ozeti.

## Rollback karar kriterleri (kisa)

- SLO ihlali + son 30 dk icinde deploy → **once imaj rollback** dusun.
- Migration supheli → snapshot / runbook (`rollback-runbook.md`).

## Maliyet / SLO dengesi

- Daha siki SLO → daha fazla replika, daha sik canary, daha uzun log retention → maliyet artar.
- Ayda bir SLO error budget tuketimini gozden gecirin.
