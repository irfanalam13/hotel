from __future__ import annotations

from rest_framework import mixins, viewsets

from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

from . import selectors
from .serializers import AuditLogSerializer


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only audit trail for the active organization (needs AUDIT_VIEW)."""

    serializer_class = AuditLogSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    filterset_fields = ("action", "method", "status_code")
    search_fields = ("action", "path")
    ordering_fields = ("created_at", "status_code")
    required_permissions = {"GET": {Perm.AUDIT_VIEW}}

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return selectors.AuditLog.objects.none()
        return selectors.list_events(organization=self.request.organization)
