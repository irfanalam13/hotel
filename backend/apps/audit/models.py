"""
Append-only audit trail.

Captures both HTTP-level events (via middleware) and explicit domain events
(via the service layer). Rows are scoped to an organization where one is known,
and are never updated or deleted through the API.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class AuditLog(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    # Domain event name (e.g. "property.created") or HTTP "<METHOD> <path>".
    action = models.CharField(max_length=120, db_index=True)
    method = models.CharField(max_length=10, blank=True, default="")
    path = models.CharField(max_length=300, blank=True, default="")
    status_code = models.PositiveIntegerField(default=0)

    # Optional target reference.
    object_type = models.CharField(max_length=120, blank=True, default="")
    object_id = models.CharField(max_length=64, blank=True, default="")

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True, default="")
    changes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} ({self.status_code}) @ {self.created_at:%Y-%m-%d %H:%M}"
