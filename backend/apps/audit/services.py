"""Recording helpers for the audit trail."""
from __future__ import annotations

from typing import Any

from .models import AuditLog

SENSITIVE_KEYS = {"password", "current_password", "new_password", "token", "refresh", "access", "secret"}


def redact(data: Any) -> Any:
    """Mask sensitive values in a (possibly nested) dict/list before storing."""
    if isinstance(data, dict):
        return {k: ("***" if k in SENSITIVE_KEYS else redact(v)) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    return data


def record_event(
    *,
    action: str,
    organization=None,
    user=None,
    object_type: str = "",
    object_id: str = "",
    changes: dict | None = None,
    method: str = "",
    path: str = "",
    status_code: int = 0,
    ip: str | None = None,
    user_agent: str = "",
) -> AuditLog:
    """Persist a single audit row. Never raises on bad input it can avoid."""
    return AuditLog.objects.create(
        action=action,
        organization=organization,
        user=user if (user is not None and getattr(user, "is_authenticated", False)) else None,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        changes=redact(changes or {}),
        method=method,
        path=path[:300],
        status_code=status_code or 0,
        ip=ip,
        user_agent=(user_agent or "")[:300],
    )
