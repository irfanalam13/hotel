from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound as DRFNotFound
from rest_framework.response import Response

from apps.properties.models import Property
from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

from . import selectors, services
from .models import RatePlan, Room, RoomType
from .serializers import (
    RatePlanCreateSerializer,
    RatePlanSerializer,
    RoomCreateSerializer,
    RoomSerializer,
    RoomStatusSerializer,
    RoomTypeCreateSerializer,
    RoomTypeSerializer,
)

_RW = {
    "GET": {Perm.ROOM_VIEW},
    "POST": {Perm.ROOM_MANAGE},
    "PUT": {Perm.ROOM_MANAGE},
    "PATCH": {Perm.ROOM_MANAGE},
    "DELETE": {Perm.ROOM_MANAGE},
}


def _get_property(request, property_id) -> Property:
    obj = Property.all_objects.filter(organization=request.organization, id=property_id).first()
    if obj is None:
        raise DRFNotFound("Property not found in this organization.")
    return obj


def _get_room_type(request, room_type_id) -> RoomType:
    obj = RoomType.all_objects.filter(organization=request.organization, id=room_type_id).first()
    if obj is None:
        raise DRFNotFound("Room type not found in this organization.")
    return obj


class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    required_permissions = _RW
    search_fields = ("name", "code")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RoomType.objects.none()
        return selectors.list_room_types(
            organization=self.request.organization,
            property_id=self.request.query_params.get("property"),
        )

    def create(self, request, *args, **kwargs):
        s = RoomTypeCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        prop = _get_property(request, data.pop("property"))
        obj = services.create_room_type(organization=request.organization, property=prop, **data)
        return Response(RoomTypeSerializer(obj).data, status=status.HTTP_201_CREATED)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    required_permissions = _RW
    search_fields = ("number", "floor")
    filterset_fields = ("status", "room_type", "property")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Room.objects.none()
        return selectors.list_rooms(
            organization=self.request.organization,
            property_id=self.request.query_params.get("property"),
            room_type_id=self.request.query_params.get("room_type"),
        )

    def create(self, request, *args, **kwargs):
        s = RoomCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        prop = _get_property(request, data.pop("property"))
        room_type = _get_room_type(request, data.pop("room_type"))
        obj = services.create_room(
            organization=request.organization, property=prop, room_type=room_type, **data
        )
        return Response(RoomSerializer(obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, id=None):
        s = RoomStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        room = services.set_room_status(room=self.get_object(), status=s.validated_data["status"])
        return Response(RoomSerializer(room).data)


class RatePlanViewSet(viewsets.ModelViewSet):
    serializer_class = RatePlanSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    required_permissions = _RW
    filterset_fields = ("room_type", "property", "is_active")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RatePlan.objects.none()
        return selectors.list_rate_plans(
            organization=self.request.organization,
            property_id=self.request.query_params.get("property"),
        )

    def create(self, request, *args, **kwargs):
        s = RatePlanCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        prop = _get_property(request, data.pop("property"))
        room_type = _get_room_type(request, data.pop("room_type"))
        obj = services.create_rate_plan(
            organization=request.organization, property=prop, room_type=room_type, **data
        )
        return Response(RatePlanSerializer(obj).data, status=status.HTTP_201_CREATED)
