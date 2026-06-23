from __future__ import annotations

from collections.abc import Iterable

from django.db import transaction

from apps.common.exceptions import ConflictError, ValidationError

from .constants import ALL_PERMISSIONS, SYSTEM_ROLE_TEMPLATES
from .models import Role, RolePermission


@transaction.atomic
def provision_default_roles(*, organization) -> list[Role]:
    """
    Create the system roles for a freshly created organization. Idempotent:
    re-running only fills in roles/permissions that are missing.
    """
    roles: list[Role] = []
    for code, (name, perms) in SYSTEM_ROLE_TEMPLATES.items():
        role, _ = Role.objects.get_or_create(
            organization=organization,
            code=code,
            defaults={"name": name, "is_system": True},
        )
        _sync_permissions(role, perms)
        roles.append(role)
    return roles


def _sync_permissions(role: Role, permissions: Iterable[str]) -> None:
    desired = set(permissions)
    unknown = desired - ALL_PERMISSIONS
    if unknown:
        raise ValidationError(f"Unknown permission(s): {sorted(unknown)}")
    existing = set(role.permissions.values_list("permission", flat=True))
    to_add = desired - existing
    to_remove = existing - desired
    if to_remove:
        role.permissions.filter(permission__in=to_remove).delete()
    if to_add:
        RolePermission.objects.bulk_create(
            [RolePermission(role=role, permission=p) for p in to_add]
        )


@transaction.atomic
def create_role(*, organization, code: str, name: str, permissions: Iterable[str] = ()) -> Role:
    code = code.strip().upper()
    if Role.objects.filter(organization=organization, code=code).exists():
        raise ConflictError(f"Role '{code}' already exists.")
    role = Role.objects.create(organization=organization, code=code, name=name, is_system=False)
    _sync_permissions(role, permissions)
    return role


@transaction.atomic
def set_role_permissions(*, role: Role, permissions: Iterable[str]) -> Role:
    _sync_permissions(role, permissions)
    return role


@transaction.atomic
def delete_role(*, role: Role) -> None:
    if role.is_system:
        raise ValidationError("System roles cannot be deleted.")
    role.delete()
