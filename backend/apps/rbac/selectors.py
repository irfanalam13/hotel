from __future__ import annotations

from django.db.models import QuerySet

from .models import Role


def list_roles(organization) -> QuerySet:
    return Role.objects.filter(organization=organization).prefetch_related("permissions")


def get_role(organization, code: str) -> Role:
    return Role.objects.get(organization=organization, code=code)


def permissions_for_role(role: Role) -> set[str]:
    return role.permission_codes
