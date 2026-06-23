from __future__ import annotations

from rest_framework import serializers

from .models import Reservation, ReservationCharge, ReservationRoom


class ReservationRoomSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source="room.number", read_only=True, default=None)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = ReservationRoom
        fields = (
            "id", "room_type", "room_type_name", "room", "room_number",
            "nightly_rate", "nights", "amount", "adults", "children",
        )


class ReservationChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationCharge
        fields = ("id", "kind", "description", "amount", "posted_on", "created_at")
        read_only_fields = ("id", "created_at")


class ReservationSerializer(serializers.ModelSerializer):
    rooms = ReservationRoomSerializer(many=True, read_only=True)
    charges = ReservationChargeSerializer(many=True, read_only=True)
    nights = serializers.IntegerField(read_only=True)
    folio_total = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            "id", "code", "status", "property", "primary_guest",
            "check_in", "check_out", "nights", "adults", "children",
            "source", "special_requests", "internal_notes",
            "currency", "total_amount", "folio_total", "rooms", "charges",
            "checked_in_at", "checked_out_at", "created_at",
        )
        read_only_fields = fields

    def get_folio_total(self, obj: Reservation):
        extra = sum((c.amount for c in obj.charges.all()), 0)
        return obj.total_amount + extra


# --- write payloads ---------------------------------------------------------

class RoomRequestSerializer(serializers.Serializer):
    room_type_id = serializers.UUIDField()
    room_id = serializers.UUIDField(required=False, allow_null=True)
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    nightly_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False, allow_null=True
    )


class ReservationCreateSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    primary_guest = serializers.UUIDField(required=False, allow_null=True)
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    source = serializers.CharField(required=False, allow_blank=True, default="front_desk")
    special_requests = serializers.CharField(required=False, allow_blank=True, default="")
    rooms = RoomRequestSerializer(many=True)

    def validate(self, data):
        if data["check_out"] <= data["check_in"]:
            raise serializers.ValidationError("check_out must be after check_in.")
        if not data["rooms"]:
            raise serializers.ValidationError("At least one room is required.")
        return data


class ReservationModifySerializer(serializers.Serializer):
    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)
    adults = serializers.IntegerField(min_value=1, required=False)
    children = serializers.IntegerField(min_value=0, required=False)
    special_requests = serializers.CharField(required=False, allow_blank=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True)


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class ChargeCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=ReservationCharge.Kind.choices, default=ReservationCharge.Kind.EXTRA)
    description = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class AvailabilitySearchSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()

    def validate(self, data):
        if data["check_out"] <= data["check_in"]:
            raise serializers.ValidationError("check_out must be after check_in.")
        return data
