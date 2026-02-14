from rest_framework import serializers
from django.db import transaction
from apps.properties.models import RoomType, Room
from apps.guests.models import Guest
from .models import Reservation, ReservationGuest, RoomMoveLog, ReservationCharge

ALLOWED_TRANSITIONS = {
    Reservation.Status.INQUIRY: {Reservation.Status.BOOKED, Reservation.Status.CANCELLED},
    Reservation.Status.BOOKED: {Reservation.Status.CHECKED_IN, Reservation.Status.CANCELLED, Reservation.Status.NO_SHOW},
    Reservation.Status.CHECKED_IN: {Reservation.Status.CHECKED_OUT},
    Reservation.Status.CHECKED_OUT: set(),
    Reservation.Status.CANCELLED: set(),
    Reservation.Status.NO_SHOW: set(),
}

class ReservationChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationCharge
        fields = ["id", "kind", "description", "amount", "posted_on", "created_at"]
        read_only_fields = ["id", "created_at"]

class RoomMoveLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMoveLog
        fields = ["id", "from_room", "to_room", "moved_at", "reason"]

class ReservationSerializer(serializers.ModelSerializer):
    guests = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    guest_details = serializers.SerializerMethodField(read_only=True)

    charges = ReservationChargeSerializer(many=True, read_only=True)
    moves = RoomMoveLogSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "property", "code", "status",
            "room_type", "room",
            "check_in", "check_out",
            "adults", "children",
            "source", "special_requests", "internal_notes",
            "guests", "guest_details",
            "charges", "moves",
            "created_at",
        ]
        read_only_fields = ["id", "property", "code", "created_at"]

    def get_guest_details(self, obj):
        return [
            {"id": str(g.id), "name": f"{g.first_name} {g.last_name}".strip(), "phone": g.phone}
            for g in obj.guests.all()
        ]

    def validate(self, attrs):
        prop = self.context["property"]

        room_type = attrs.get("room_type") or getattr(self.instance, "room_type", None)
        room = attrs.get("room") if "room" in attrs else getattr(self.instance, "room", None)

        if room_type and room_type.property_id != prop.id:
            raise serializers.ValidationError("room_type must belong to the same property.")

        if room:
            if room.property_id != prop.id:
                raise serializers.ValidationError("room must belong to the same property.")
            if room_type and room.room_type_id != room_type.id:
                raise serializers.ValidationError("room must match room_type.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        prop = self.context["property"]
        guest_ids = validated_data.pop("guests", [])

        res = Reservation(**validated_data)
        res.property = prop
        res.full_clean()
        res.save()

        # code generation: RSV-000001 style
        res.code = f"RSV-{str(res.id).split('-')[0].upper()}"
        res.save(update_fields=["code"])

        if guest_ids:
            guests = Guest.objects.filter(id__in=guest_ids, property=prop)
            for idx, g in enumerate(guests):
                ReservationGuest.objects.create(reservation=res, guest=g, is_primary=(idx == 0))
        return res

    @transaction.atomic
    def update(self, instance, validated_data):
        guest_ids = validated_data.pop("guests", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        instance.full_clean()
        instance.save()

        if guest_ids is not None:
            prop = self.context["property"]
            instance.guests.clear()
            guests = Guest.objects.filter(id__in=guest_ids, property=prop)
            for idx, g in enumerate(guests):
                ReservationGuest.objects.create(reservation=instance, guest=g, is_primary=(idx == 0))
        return instance

class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Reservation.Status.choices)

class RoomAssignSerializer(serializers.Serializer):
    room_id = serializers.UUIDField()

class RoomMoveSerializer(serializers.Serializer):
    to_room_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True)

class ChargeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationCharge
        fields = ["kind", "description", "amount", "posted_on"]
