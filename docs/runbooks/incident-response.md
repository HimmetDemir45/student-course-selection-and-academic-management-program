# Incident response

## Severity (examples)

| Level | Meaning | Examples | Response target |
|-------|---------|----------|-----------------|
| **SEV1** | Production down or data breach | Site unreachable, DB exposed, auth bypass | Page on-call immediately; war room |
| **SEV2** | Major degradation | Persistent 5xx, payment/registration blocked | Eng owner < 30 min |
| **SEV3** | Minor / workaround exists | Single feature broken, elevated errors | Next business day / backlog |

Adjust labels to your org.

## First 15 minutes (on-call)

1. **Acknowledge** the alert / ticket; set status to *investigating*.
2. **Stabilize**: if deploy just happened → consider **rollback** (`rollback-runbook.md`).
3. **Scope**: which region, which service (app vs RDS vs ALB), user impact %.
4. **Communicate** internally (template below); avoid public speculation.
5. **Evidence**: save logs, request IDs (`X-Request-ID` response header), CloudWatch/metric screenshots.
6. **Escalation**: if SEV1 unresolved in 15 min → escalate to tech lead / instructor / vendor (AWS).

## Internal communication template

```
Subject: [SEVx] <product> — <short title>
Impact: <who/what broken>
Since: <UTC time>
Actions: investigating | mitigating | monitoring
Next update: <+30 min>
```

## Customer / stakeholder template (if applicable)

```
We are aware of an issue affecting <area>. Our team is working on it.
Updates: <status page or email>
```

## Root cause analysis (RCA) — after resolution

- **Timeline**: detection → mitigation → fix.
- **Root cause**: technical + any process gap.
- **What went well / poorly**
- **Action items**: owners + dates (monitoring, test gap, runbook update).
- Store with incident ID; link from `SECURITY.md` if security-related.

## Security-specific incidents

See `SECURITY.md` (secret leak, vulnerability disclosure) and escalate per course/org policy.
