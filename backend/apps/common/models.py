"""Abstract model bases shared across every domain app."""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from .managers import AllObjectsManager, TenantManager


class UUIDModel(models.Model):
    """Primary key is a non-guessable UUID (safe to expose in URLs/APIs)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """UUID pk + created/updated timestamps. Use for non-tenant entities."""

    class Meta:
        abstract = True


class TenantScopedModel(BaseModel):
    """
    Base for every row that belongs to a tenant (Organization).

    Bundles tenant ownership + soft delete behind a single tenant-aware
    manager so subclasses get row-level isolation for free:

    * ``objects``     → filtered by active tenant, excludes soft-deleted rows.
    * ``all_objects`` → unfiltered escape hatch (admin, migrations, reports).
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete by default."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["is_deleted", "deleted_at", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
