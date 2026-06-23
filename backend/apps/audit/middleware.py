"""
Audit middleware.

Records mutating HTTP requests (POST/PUT/PATCH/DELETE) as audit events. Runs
after the tenant resolver so ``request.organization`` is available, and is
defensive: a logging failure must never break the actual response.

Note: JWT auth happens at view dispatch, so the user is only reliably attached
to the DRF request. We best-effort read ``request.user`` here; precise user
attribution for token requests is done in the service layer via
``record_event(user=...)``.
"""
from __future__ import annotations

import json

from .services import record_event

AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def _request_body(request) -> dict:
    try:
        data = getattr(request, "_audit_body", None)
        if data is None and request.body:
            data = json.loads(request.body.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capture the body before the view consumes the stream.
        body = _request_body(request) if request.method in AUDITED_METHODS else {}
        response = self.get_response(request)

        if request.method in AUDITED_METHODS:
            try:
                user = getattr(request, "user", None)
                record_event(
                    action=f"{request.method} {request.path}",
                    organization=getattr(request, "organization", None),
                    user=user,
                    method=request.method,
                    path=request.path,
                    status_code=getattr(response, "status_code", 0),
                    ip=_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    changes={"body": body} if body else {},
                )
            except Exception:  # noqa: BLE001 — auditing must never break responses
                pass

        return response
