from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound as DRFNotFound
from rest_framework.response import Response

from apps.guests.models import Guest
from apps.properties.models import Property
from apps.rbac.constants import Perm
from apps.rbac.permissions import HasOrgPermission

from . import selectors, services
from .models import Reservation
from .serializers import (
    AvailabilitySearchSerializer,
    CancelSerializer,
    ChargeCreateSerializer,
    ReservationChargeSerializer,
    ReservationCreateSerializer,
    ReservationModifySerializer,
    ReservationSerializer,
)

# Map viewset action -> required permission codes.
_ACTION_PERMS = {
    "list": {Perm.RESERVATION_VIEW},
    "retrieve": {Perm.RESERVATION_VIEW},
    "availability": {Perm.RESERVATION_VIEW},
    "create": {Perm.RESERVATION_MANAGE},
    "partial_update": {Perm.RESERVATION_MANAGE},
    "update": {Perm.RESERVATION_MANAGE},
    "cancel": {Perm.RESERVATION_MANAGE},
    "add_charge": {Perm.RESERVATION_MANAGE},
    "check_in": {Perm.RESERVATION_OPERATE},
    "check_out": {Perm.RESERVATION_OPERATE},
}


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [HasOrgPermission]
    lookup_field = "id"
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ("status", "property")
    search_fields = ("code",)
    ordering_fields = ("created_at", "check_in")

    def get_required_permissions(self) -> set[str]:
        return _ACTION_PERMS.get(self.action, {Perm.RESERVATION_VIEW})

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Reservation.objects.none()
        return selectors.list_reservations(
            organization=self.request.organization,
            property_id=self.request.query_params.get("property"),
            status=self.request.query_params.get("status"),
        )

    # --- helpers ---
    def _get_property(self, property_id) -> Property:
        obj = Property.all_objects.filter(
            organization=self.request.organization, id=property_id
        ).first()
        if obj is None:
            raise DRFNotFound("Property not found in this organization.")
        return obj

    def _get_guest(self, guest_id):
        if guest_id is None:
            return None
        guest = Guest.objects.all_tenants().filter(
            organization=self.request.organization, id=guest_id
        ).first()
        if guest is None:
            raise DRFNotFound("Guest not found in this organization.")
        return guest

    # --- CRUD ---
    def create(self, request, *args, **kwargs):
        s = ReservationCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        reservation = services.create_reservation(
            organization=request.organization,
            property=self._get_property(data["property"]),
            check_in=data["check_in"],
            check_out=data["check_out"],
            primary_guest=self._get_guest(data.get("primary_guest")),
            adults=data["adults"],
            children=data["children"],
            source=data["source"],
            special_requests=data["special_requests"],
            room_requests=data["rooms"],
            by_user=request.user,
        )
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        s = ReservationModifySerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        reservation = services.modify_reservation(
            reservation=self.get_object(), by_user=request.user, **s.validated_data
        )
        return Response(ReservationSerializer(reservation).data)

    # --- lifecycle actions ---
    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        s = CancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        reservation = services.cancel_reservation(
            reservation=self.get_object(), by_user=request.user, reason=s.validated_data["reason"]
        )
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, id=None):
        reservation = services.check_in(reservation=self.get_object(), by_user=request.user)
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"], url_path="check-out")
    def check_out(self, request, id=None):
        reservation = services.check_out(reservation=self.get_object(), by_user=request.user)
        return Response(ReservationSerializer(reservation).data)

    @action(detail=True, methods=["post"])
    def add_charge(self, request, id=None):
        s = ChargeCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        charge = services.add_charge(reservation=self.get_object(), **s.validated_data)
        return Response(ReservationChargeSerializer(charge).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def availability(self, request):
        s = AvailabilitySearchSerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        summary = selectors.availability_summary(
            organization=request.organization,
            property=self._get_property(data["property"]),
            check_in=data["check_in"],
            check_out=data["check_out"],
        )
        return Response(summary)
