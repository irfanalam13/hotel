from rest_framework import serializers
from .models import Property, Amenity, RoomType, Room

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "name", "code", "timezone", "currency", "created_at"]

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["id", "property", "name"]
        read_only_fields = ["property"]

class RoomTypeSerializer(serializers.ModelSerializer):
    amenities = serializers.PrimaryKeyRelatedField(many=True, required=False, read_only=False, queryset=Amenity.objects.all())

    class Meta:
        model = RoomType
        fields = ["id", "property", "name", "code", "max_adults", "max_children", "base_rate", "amenities"]
        read_only_fields = ["property"]

    def validate_amenities(self, amenities):
        prop = self.context["property"]
        for a in amenities:
            if a.property_id != prop.id:
                raise serializers.ValidationError("Amenity must belong to the same property.")
        return amenities

class RoomSerializer(serializers.ModelSerializer):
    room_type_detail = RoomTypeSerializer(source="room_type", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "property", "room_type", "room_type_detail",
            "number", "floor", "is_active", "housekeeping_status", "notes"
        ]
        read_only_fields = ["property"]

    def validate_room_type(self, room_type):
        prop = self.context["property"]
        if room_type.property_id != prop.id:
            raise serializers.ValidationError("Room type must belong to the same property.")
        return room_type
