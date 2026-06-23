"""Managers and querysets for the shared model bases."""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from .context import get_current_organization


class TenantQuerySet(models.QuerySet):
    """Queryset with soft-delete semantics for tenant-scoped rows."""

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

    def delete(self):
        # Bulk soft delete.
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class TenantManager(models.Manager):
    """
    Default manager for tenant-scoped models.

    Transparently filters by the active Organization (bound by the tenant
    middleware) and hides soft-deleted rows. When no tenant is bound — e.g.
    in the Django admin, management commands or cross-tenant reporting — no
    tenant filter is applied, so callers must scope explicitly.
    """

    def get_queryset(self) -> TenantQuerySet:
        qs = TenantQuerySet(self.model, using=self._db).filter(is_deleted=False)
        organization = get_current_organization()
        if organization is not None:
            qs = qs.filter(organization=organization)
        return qs

    def all_tenants(self) -> TenantQuerySet:
        """Bypass the tenant filter (still hides soft-deleted rows)."""
        return TenantQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Unfiltered escape hatch: includes soft-deleted rows and all tenants."""

    def get_queryset(self) -> TenantQuerySet:
        return TenantQuerySet(self.model, using=self._db)
