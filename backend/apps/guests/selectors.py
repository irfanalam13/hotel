from __future__ import annotations

from django.db.models import Q, QuerySet

from .models import Guest


def list_guests(*, organization, property_id=None, search: str | None = None) -> QuerySet:
    qs = Guest.objects.filter(organization=organization)
    if property_id:
        qs = qs.filter(property_id=property_id)
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )
    return qs
