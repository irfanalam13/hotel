from __future__ import annotations

from django.db.models import QuerySet

from .models import Property


def list_properties(*, organization=None) -> QuerySet:
    """
    Properties for a tenant. When ``organization`` is omitted, the tenant-aware
    manager scopes to the active organization bound by the middleware.
    """
    if organization is not None:
        return Property.objects.all_tenants().filter(organization=organization)
    return Property.objects.all()


def get_property(*, organization, property_id) -> Property:
    return Property.objects.all_tenants().get(organization=organization, id=property_id)


def count_properties(*, organization) -> int:
    return Property.objects.all_tenants().filter(organization=organization).count()
