import logging

from .middleware import get_current_user, get_current_ip

logger = logging.getLogger(__name__)


def _resolve_valid_user(user):
    candidate = user or get_current_user()
    if candidate is None:
        return None

    user_pk = getattr(candidate, "pk", None)
    if not user_pk:
        return None

    try:
        if candidate.__class__.objects.filter(pk=user_pk).exists():
            return candidate
    except Exception:
        logger.exception("Failed to validate current user for activity logging")
    return None


def log_activity(action: str, module: str, description: str,
                 user=None, ip_address: str | None = None) -> None:
    """Record a single activity log entry.

    Swallows all exceptions so that a logging failure never breaks the
    main application flow.
    """
    try:
        from .models import ActivityLog
        ActivityLog.objects.create(
            user=_resolve_valid_user(user),
            action=action,
            module=module,
            description=description[:500],
            ip_address=ip_address or get_current_ip(),
        )
    except Exception:
        logger.exception("Failed to write activity log: action=%s module=%s", action, module)
