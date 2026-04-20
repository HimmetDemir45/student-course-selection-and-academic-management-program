import logging

from audit_logs.models import AuditLog

logger = logging.getLogger(__name__)


def _build_standard_metadata(
    event_type,
    actor=None,
    target_type="",
    target_id="",
    metadata=None,
    request=None,
):
    payload = dict(metadata or {})
    actor_id = getattr(actor, "pk", None)
    request_id = ""
    if request is not None:
        request_id = (
            getattr(request, "request_id", "")
            or request.META.get("HTTP_X_REQUEST_ID", "")
            or ""
        )
    payload.setdefault("event_type", event_type)
    payload.setdefault("actor_id", actor_id)
    payload.setdefault(
        "target",
        f"{target_type}:{target_id}" if target_type or target_id else "",
    )
    payload.setdefault("status", payload.get("status") or "success")
    payload.setdefault("request_id", request_id)
    return payload


def log_event(
    event_type,
    actor=None,
    target_type="",
    target_id="",
    metadata=None,
    request=None,
):
    # Rollback: logger.exception bloğunu kaldırıp yalnızca try/except pass'e dönülmesi önerilmez.
    try:
        AuditLog.objects.create(
            event_type=event_type,
            actor=actor if getattr(actor, "is_authenticated", False) else actor,
            target_type=target_type or "",
            target_id=str(target_id) if target_id else "",
            metadata=_build_standard_metadata(
                event_type=event_type,
                actor=actor,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata,
                request=request,
            ),
        )
    except Exception:
        logger.exception(
            "AuditLog yazimi basarisiz",
            extra={
                "audit_event_type": event_type,
                "audit_actor_id": getattr(actor, "pk", None),
                "audit_target_type": target_type,
                "audit_target_id": str(target_id) if target_id else "",
            },
        )
        return None


def log_auth_event(event_type, actor=None, request=None, description="", **kwargs):
    metadata = {"description": description}
    if request:
        metadata["ip"] = request.META.get("REMOTE_ADDR", "")
        metadata["user_agent"] = request.META.get("HTTP_USER_AGENT", "")

    # Geriye donuk uyumluluk: user=... gonderildiyse actor olarak kabul et.
    actor = actor or kwargs.get("user")
    return log_event(
        event_type=event_type,
        actor=actor,
        metadata=metadata,
        request=request,
    )
