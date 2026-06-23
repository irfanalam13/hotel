from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors, services
from .constants import Perm
from .models import Role
from .permissions import HasOrgPermission
from .serializers import (
    PermissionCatalogSerializer,
    RoleSerializer,
    RoleWriteSerializer,
)


class PermissionCatalogView(APIView):
    """List every permission code the system understands."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(PermissionCatalogSerializer.catalog())


class RoleViewSet(viewsets.ModelViewSet):
    """CRUD for organization-scoped roles. System roles are read/edit-only."""

    serializer_class = RoleSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    required_permissions = {
        "GET": {Perm.ROLE_VIEW},
        "POST": {Perm.ROLE_MANAGE},
        "PUT": {Perm.ROLE_MANAGE},
        "PATCH": {Perm.ROLE_MANAGE},
        "DELETE": {Perm.ROLE_MANAGE},
    }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Role.objects.none()
        return selectors.list_roles(self.request.organization)

    def create(self, request, *args, **kwargs):
        writer = RoleWriteSerializer(data=request.data)
        writer.is_valid(raise_exception=True)
        role = services.create_role(organization=request.organization, **writer.validated_data)
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        role: Role = self.get_object()
        writer = RoleWriteSerializer(data=request.data, partial=kwargs.get("partial", False))
        writer.is_valid(raise_exception=True)
        data = writer.validated_data
        if "name" in data:
            role.name = data["name"]
        if "description" in data:
            role.description = data["description"]
        role.save(update_fields=["name", "description", "updated_at"])
        if "permissions" in data:
            services.set_role_permissions(role=role, permissions=data["permissions"])
        return Response(RoleSerializer(role).data)

    def destroy(self, request, *args, **kwargs):
        services.delete_role(role=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
