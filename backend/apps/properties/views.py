from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

from . import selectors, services
from .serializers import PropertyCreateSerializer, PropertySerializer


class PropertyViewSet(viewsets.ModelViewSet):
    """
    Tenant-scoped property CRUD. The active organization is resolved from the
    ``X-Org-Slug`` header; the tenant-aware manager isolates the queryset.
    """

    serializer_class = PropertySerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    search_fields = ("name", "code", "city")
    ordering_fields = ("name", "created_at")
    required_permissions = {
        "GET": {Perm.PROPERTY_VIEW},
        "POST": {Perm.PROPERTY_MANAGE},
        "PUT": {Perm.PROPERTY_MANAGE},
        "PATCH": {Perm.PROPERTY_MANAGE},
        "DELETE": {Perm.PROPERTY_MANAGE},
    }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return selectors.Property.objects.none()
        return selectors.list_properties(organization=self.request.organization)

    def create(self, request, *args, **kwargs):
        serializer = PropertyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = services.create_property(
            organization=request.organization, **serializer.validated_data
        )
        return Response(PropertySerializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PropertySerializer(instance, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        instance = services.update_property(instance=instance, **serializer.validated_data)
        return Response(PropertySerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        services.archive_property(instance=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
