from __future__ import annotations

from rest_framework import serializers

from .models import RatePlan, Room, RoomType


class RoomTypeSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoomType
        fields = (
            "id", "property", "name", "code", "description",
            "max_adults", "max_children", "base_rate", "capacity", "created_at",
        )
        read_only_fields = ("id", "code", "capacity", "created_at")


class RoomTypeCreateSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    name = serializers.CharField(max_length=120)
    code = serializers.SlugField(max_length=40, required=False)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    max_adults = serializers.IntegerField(min_value=1, default=2)
    max_children = serializers.IntegerField(min_value=0, default=0)
    base_rate = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, default=0)


class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = Room
        fields = (
            "id", "property", "room_type", "room_type_name", "number",
            "floor", "status", "is_active", "notes", "created_at",
        )
        read_only_fields = ("id", "created_at", "room_type_name")


class RoomCreateSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    room_type = serializers.UUIDField()
    number = serializers.CharField(max_length=20)
    floor = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class RoomStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Room.Status.choices)


class RatePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlan
        fields = (
            "id", "property", "room_type", "name", "code",
            "nightly_rate", "is_default", "is_active", "created_at",
        )
        read_only_fields = ("id", "code", "created_at")


class RatePlanCreateSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    room_type = serializers.UUIDField()
    name = serializers.CharField(max_length=120)
    code = serializers.SlugField(max_length=40, required=False)
    nightly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    is_default = serializers.BooleanField(default=False)
