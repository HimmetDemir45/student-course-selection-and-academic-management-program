import logging

from audit_logs.models import AuditLog

logger = logging.getLogger(__name__)


def log_event(event_type, actor=None, target_type="", target_id="", metadata=None):
    # Rollback: logger.exception bloğunu kaldırıp yalnızca try/except pass'e dönülmesi önerilmez.
    try:
        AuditLog.objects.create(
            event_type=event_type,
            actor=actor if getattr(actor, "is_authenticated", False) else actor,
            target_type=target_type or "",
            target_id=str(target_id) if target_id else "",
            metadata=metadata or {},
        )
    except Exception:
        logger.exception(
            "AuditLog yazimi basarisiz",
            extra={
                "audit_event_type": event_type,
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
    return log_event(event_type=event_type, actor=actor, metadata=metadata)
