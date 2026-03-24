# Monitoring and alerting checklist (production)

## Application

| Signal | What to watch | Suggested alarm (tune to traffic) |
|--------|----------------|-----------------------------------|
| HTTP **5xx** rate | ALB `HTTPCode_Target_5XX_Count` / app logs | > N/min or > 1% of requests for 5 min |
| **Latency p95** | ALB `TargetResponseTime` p95 | > 2–5 s for 10 min (adjust per SLA) |
| **Health** | Synthetic or canary `GET /health/ready/` | 2 consecutive failures |
| **Gunicorn/workers** | Process count, worker restarts in container logs | Workers = 0 or crash loop |

## Database (RDS MySQL)

| Signal | Metric / log | Suggested threshold (indicative) |
|--------|--------------|----------------------------------|
| Connections | `DatabaseConnections` vs `max_connections` | > 80% sustained 10 min |
| CPU | `CPUUtilization` | > 85% 15 min |
| Storage | `FreeStorageSpace` | < 15% free |
| Replication lag | If read replicas | > 30 s |

## Compute / host (EC2 or ECS)

| Signal | Notes |
|--------|--------|
| CPU / memory | ECS `CPUUtilization`, `MemoryUtilization`; EC2 standard alarms |
| Disk / I/O | Root volume free space; `DiskQueueDepth` on RDS |

## Logs and correlation

- **ALB access logs**: include target status, request processing time.
- **App logs** (stdout → CloudWatch): use same time window as metrics.
- **`X-Request-ID`**: response header set by `RequestIdMiddleware`; configure reverse proxy to log it (or forward as `X-Request-ID` to upstream) so support can tie user report → log line.
- Optional next step (Phase 8): structured JSON logs + `request_id` field in every log record (e.g. `django-structlog` or contextvars filter).

## CloudWatch alarm naming (examples)

- `prod-alb-5xx-high`
- `prod-rds-connections-high`
- `prod-app-health-ready-failed`

## Dashboards

- One dashboard: ALB (requests, 4xx/5xx, latency) + RDS (CPU, connections, storage) + custom health check metric (if published).
