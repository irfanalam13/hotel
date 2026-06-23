"""
Tenancy root.

``Organization`` is the tenant: every tenant-scoped row in the system points
back to one. ``Membership`` is the join between a user and an organization,
carrying the user's role (RBAC) and an optional property-level scope.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Organization(BaseModel):
    class Plan(models.TextChoices):
        FREE = "FREE", "Free"
        STARTER = "STARTER", "Starter"
        PRO = "PRO", "Pro"
        ENTERPRISE = "ENTERPRISE", "Enterprise"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    plan = models.CharField(max_length=16, choices=Plan.choices, default=Plan.FREE)
    # Soft quota — enforced in the properties service layer.
    max_properties = models.PositiveIntegerField(default=1)

    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=8, default="USD")
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class Membership(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.ForeignKey(
        "rbac.Role", on_delete=models.PROTECT, related_name="memberships"
    )
    # Empty property scope == access to every property in the organization.
    properties = models.ManyToManyField(
        "properties.Property", blank=True, related_name="member_scopes"
    )

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_memberships",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="uniq_membership_per_org_user"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.organization_id} ({self.role_id})"

    def has_property_scope(self, property_id) -> bool:
        """True if this membership can access the given property."""
        if not self.properties.exists():
            return True
        return self.properties.filter(id=property_id).exists()
