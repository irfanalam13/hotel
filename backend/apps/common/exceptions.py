"""
Domain exceptions + a consistent DRF error envelope.

Service-layer code raises :class:`DomainError` (or subclasses) to signal
business-rule violations without coupling to HTTP. The custom exception
handler maps those — and DRF's own exceptions — to a uniform JSON shape::

    {"error": {"type": "...", "detail": ..., "status_code": 400}}
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


class DomainError(Exception):
    """Base class for business-rule violations raised by the service layer."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A domain error occurred."

    def __init__(self, detail: str | None = None, *, code: str | None = None):
        self.detail = detail or self.default_detail
        self.code = code
        super().__init__(self.detail)


class ValidationError(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation failed."


class PermissionDenied(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."


class NotFound(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found."


class ConflictError(DomainError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state."


def drf_exception_handler(exc, context):
    """DRF EXCEPTION_HANDLER: normalise domain + framework errors."""
    if isinstance(exc, DomainError):
        return Response(
            {
                "error": {
                    "type": exc.__class__.__name__,
                    "code": exc.code,
                    "detail": exc.detail,
                    "status_code": exc.status_code,
                }
            },
            status=exc.status_code,
        )

    response = drf_default_handler(exc, context)
    if response is not None:
        response.data = {
            "error": {
                "type": exc.__class__.__name__,
                "detail": response.data,
                "status_code": response.status_code,
            }
        }
    return response
