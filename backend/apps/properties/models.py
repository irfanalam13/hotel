"""
Properties — the physical hotels/branches a tenant operates.

A ``Property`` is tenant-scoped: it inherits ``organization`` ownership, soft
delete and tenant-aware managers from :class:`TenantScopedModel`, so reads are
automatically isolated to the active organization.
"""
from __future__ import annotations

from django.db import models

from apps.common.models import TenantScopedModel


class Property(TenantScopedModel):
    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=50)  # unique per organization

    # Location.
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=120, blank=True, default="")
    country = models.CharField(max_length=120, blank=True, default="")

    # Contact.
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    # Operational defaults (fall back to the organization's settings).
    timezone = models.CharField(max_length=64, blank=True, default="")
    currency = models.CharField(max_length=8, blank=True, default="")
    star_rating = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "properties"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_property_code_per_org"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.code}]"
