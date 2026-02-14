from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date

from apps.common.permissions import IsPropertyStaff, HasPropertyObjectAccess
from apps.properties.models import Property, Room
from .models import Reservation, RoomMoveLog, ReservationCharge
from .serializers import (
    ReservationSerializer, StatusUpdateSerializer,
    RoomAssignSerializer, RoomMoveSerializer,
    ChargeCreateSerializer
)
from .services import availability_by_room_type, available_rooms, ACTIVE_STATUSES

def get_property_from_header(request):
    prop_id = request.headers.get("X-PROPERTY-ID")
    return Property.objects.get(id=prop_id)

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsPropertyStaff, HasPropertyObjectAccess]
    search_fields = ["code", "source", "internal_notes"]
    ordering_fields = ["created_at", "check_in", "status"]
    filterset_fields = ["status", "room_type", "room"]

    def get_queryset(self):
        prop = get_property_from_header(self.request)
        return (
            Reservation.objects.filter(property=prop)
            .select_related("room_type", "room")
            .prefetch_related("guests", "charges", "moves")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["property"] = get_property_from_header(self.request)
        return ctx

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["POST"])
    def set_status(self, request, pk=None):
        reservation = self.get_object()
        ser = StatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_status = ser.validated_data["status"]

        allowed = {
            s for s in
            __import__("apps.reservations.serializers", fromlist=["ALLOWED_TRANSITIONS"]).ALLOWED_TRANSITIONS[reservation.status]
        }
        if new_status not in allowed:
            return Response(
                {"detail": f"Invalid transition from {reservation.status} to {new_status}"},
                status=400
            )

        # Real-life rules:
        # - Cannot check-in without room assignment (recommended). If no room, still allow if you want.
        if new_status == Reservation.Status.CHECKED_IN and reservation.room_id is None:
            return Response({"detail": "Assign a room before check-in."}, status=400)

        reservation.status = new_status
        reservation.full_clean()
        reservation.save(update_fields=["status"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["POST"])
    def assign_room(self, request, pk=None):
        reservation = self.get_object()
        ser = RoomAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        room_id = ser.validated_data["room_id"]

        if reservation.status not in [Reservation.Status.BOOKED, Reservation.Status.INQUIRY]:
            return Response({"detail": "Room can be assigned only for inquiry/booked."}, status=400)

        prop = get_property_from_header(request)
        room = Room.objects.get(id=room_id, property=prop)

        if room.room_type_id != reservation.room_type_id:
            return Response({"detail": "Room type mismatch."}, status=400)

        # Ensure room not already reserved for overlapping dates (only checks assigned rooms)
        conflict = Reservation.objects.filter(
            property=prop,
            status__in=ACTIVE_STATUSES,
            room=room,
            check_in__lt=reservation.check_out,
            check_out__gt=reservation.check_in,
        ).exclude(id=reservation.id).exists()
        if conflict:
            return Response({"detail": "Room is not available for those dates."}, status=400)

        reservation.room = room
        reservation.full_clean()
        reservation.save(update_fields=["room"])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["POST"])
    def move_room(self, request, pk=None):
        reservation = self.get_object()
        ser = RoomMoveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        if reservation.status != Reservation.Status.CHECKED_IN:
            return Response({"detail": "Room move allowed only after check-in."}, status=400)

        prop = get_property_from_header(request)
        to_room = Room.objects.get(id=ser.validated_data["to_room_id"], property=prop)

        if to_room.room_type_id != reservation.room_type_id:
            return Response({"detail": "Room type mismatch."}, status=400)

        conflict = Reservation.objects.filter(
            property=prop,
            status__in=ACTIVE_STATUSES,
            room=to_room,
            check_in__lt=reservation.check_out,
            check_out__gt=reservation.check_in,
        ).exclude(id=reservation.id).exists()
        if conflict:
            return Response({"detail": "Target room is not available."}, status=400)

        old_room = reservation.room
        reservation.room = to_room
        reservation.full_clean()
        reservation.save(update_fields=["room"])

        RoomMoveLog.objects.create(
            property=prop,
            reservation=reservation,
            from_room=old_room,
            to_room=to_room,
            reason=ser.validated_data.get("reason", "")
        )
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=["POST"])
    def add_charge(self, request, pk=None):
        reservation = self.get_object()
        ser = ChargeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ReservationCharge.objects.create(reservation=reservation, **ser.validated_data)
        return Response(self.get_serializer(reservation).data, status=201)

class AvailabilityViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsPropertyStaff]

    def list(self, request):
        """
        GET /api/reservations/availability/?start=YYYY-MM-DD&end=YYYY-MM-DD
        Optional: room_type=<uuid> to list available rooms for that type
        """
        prop = get_property_from_header(request)
        start = parse_date(request.query_params.get("start", ""))
        end = parse_date(request.query_params.get("end", ""))

        if not start or not end or start >= end:
            return Response({"detail": "Provide valid start and end dates."}, status=400)

        room_type_id = request.query_params.get("room_type")
        if room_type_id:
            qs = available_rooms(prop.id, room_type_id, start, end)
            return Response({
                "start": str(start),
                "end": str(end),
                "room_type": room_type_id,
                "rooms": [{"id": str(r.id), "number": r.number, "hk": r.housekeeping_status} for r in qs],
            })

        data = availability_by_room_type(prop.id, start, end)
        return Response({"start": str(start), "end": str(end), "by_room_type": data})
