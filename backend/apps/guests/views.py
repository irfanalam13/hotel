from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound as DRFNotFound
from rest_framework.response import Response

from apps.properties.models import Property
from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

from . import selectors, services
from .models import Guest
from .serializers import GuestCreateSerializer, GuestSerializer


class GuestViewSet(viewsets.ModelViewSet):
    serializer_class = GuestSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    search_fields = ("first_name", "last_name", "email", "phone")
    filterset_fields = ("property",)
    required_permissions = {
        "GET": {Perm.GUEST_VIEW},
        "POST": {Perm.GUEST_MANAGE},
        "PUT": {Perm.GUEST_MANAGE},
        "PATCH": {Perm.GUEST_MANAGE},
        "DELETE": {Perm.GUEST_MANAGE},
    }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Guest.objects.none()
        return selectors.list_guests(
            organization=self.request.organization,
            property_id=self.request.query_params.get("property"),
            search=self.request.query_params.get("search"),
        )

    def create(self, request, *args, **kwargs):
        s = GuestCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        prop = Property.all_objects.filter(
            organization=request.organization, id=data.pop("property")
        ).first()
        if prop is None:
            raise DRFNotFound("Property not found in this organization.")
        guest = services.create_guest(organization=request.organization, property=prop, **data)
        return Response(GuestSerializer(guest).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        guest = self.get_object()
        serializer = GuestSerializer(guest, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        guest = services.update_guest(guest=guest, **serializer.validated_data)
        return Response(GuestSerializer(guest).data)
