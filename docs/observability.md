# Observability (Phase 8)

## Log fields reference

### Text mode (default, `DJANGO_LOG_JSON=False`)

| Field | Source |
|-------|--------|
| `request_id` | `X-Request-ID` veya uretilen UUID (`core.middleware.request_id`) |
| `http_path` / `http_method` | Context filter (`core.request_context`) |
| `request` logger | `request_finished status=... duration_ms=... user_id=...` |

### JSON mode (`DJANGO_LOG_JSON=True`)

Structlog + stdlib bridge (`core/structlog_config.py`). Her satir JSON; tipik alanlar:

| Field | Aciklama |
|-------|----------|
| `timestamp` | ISO8601 |
| `level` | info, warning, error |
| `logger` | django / request / ... |
| `event` | Mesaj veya `request_finished` |
| `request_id` | Baglam (merge_contextvars) |
| `http_path`, `http_method` | Istek basinda baglanir |
| `status_code`, `duration_ms`, `user_id` | `request_finished` satirinda |

Parola/token benzeri anahtarlar maskelemeye tabidir (`_redact_event_dict`).

## Ornek log satiri (JSON)

```json
{"timestamp":"2026-03-24T12:00:00.123456Z","level":"info","logger":"request","event":"request_finished","request_id":"a1b2c3d4-...","http_path":"/enrollments/enroll/","http_method":"POST","status_code":302,"duration_ms":45.2,"user_id":42}
```

## CloudWatch Logs Insights (ornek)

```
fields @timestamp, request_id, status_code, duration_ms
| filter event = "request_finished"
| stats avg(duration_ms), pct(duration_ms, 95) by bin(5m)
```

## Loki / LogQL (ornek)

```logql
{job="django"} |= "request_finished" | json | duration_ms > 2000
```

## ELK / Kibana

`request_id` keyword alani ile filtre; `@timestamp` histogram.

## Canary + PagerDuty

1. **GitHub Actions**: `.github/workflows/canary.yml` — `CANARY_BASE_URL` secret; 15 dk’da bir `/health/*`.
2. **AWS**: CloudWatch Alarm (metric math veya synthetic canary) → SNS topic → PagerDuty **Events API v2** veya email entegrasyonu.
3. Alarm mesaj govdesine runbook linki ekleyin: `https://github.com/<org>/<repo>/blob/main/docs/runbooks/incident-response.md`

Onerilen alarmlar: health check basarisiz (2 ardisik), ALB 5xx orani, TargetResponseTime p95.

## Maliyet farkindaligi

- Log retention: prod 30–90 gun; debug seviyesini prod’da acmayin.
- Canary: GitHub scheduled dakika basina dakika — org kotasina dikkat; AWS Lambda 1 dk + CloudWatch daha ucuz olabilir.
- JSON log satiri boyutu: gereksiz alan eklemeyin.
