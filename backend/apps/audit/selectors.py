from __future__ import annotations

from django.db.models import QuerySet

from .models import AuditLog


def list_events(*, organization) -> QuerySet:
    return (
        AuditLog.objects.filter(organization=organization)
        .select_related("user")
    )
