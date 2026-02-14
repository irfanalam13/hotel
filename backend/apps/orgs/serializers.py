from rest_framework import serializers
from .models import HotelGroup, GroupHotel


class HotelGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelGroup
        fields = ["id", "name", "owner", "is_active", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]


class GroupHotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupHotel
        fields = ["id", "group", "hotel", "role"]
        read_only_fields = ["id"]
