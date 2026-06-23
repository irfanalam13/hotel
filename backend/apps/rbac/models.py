"""
Role-Based Access Control.

Roles are scoped to an organization (so a tenant can customise them) and carry
a set of permission codes via :class:`RolePermission`. System roles are flagged
``is_system`` and provisioned automatically when an organization is created.
"""
from __future__ import annotations

from django.db import models

from apps.common.models import BaseModel

from .constants import PERMISSION_CATALOG


class Role(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="roles",
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    # System roles are provisioned from templates and cannot be deleted.
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_role_per_org"
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.organization_id})"

    @property
    def permission_codes(self) -> set[str]:
        return set(self.permissions.values_list("permission", flat=True))


class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    permission = models.CharField(
        max_length=64,
        choices=[(code, label) for code, label in PERMISSION_CATALOG.items()],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"], name="uniq_permission_per_role"
            )
        ]

    def __str__(self) -> str:
        return f"{self.role.code}:{self.permission}"
