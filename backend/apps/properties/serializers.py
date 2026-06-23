from __future__ import annotations

from rest_framework import serializers

from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = (
            "id", "name", "code", "address", "city", "country",
            "phone", "email", "timezone", "currency", "star_rating",
            "is_active", "created_at",
        )
        read_only_fields = ("id", "code", "created_at")


class PropertyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    code = serializers.SlugField(max_length=50, required=False)
    address = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField(required=False, allow_blank=True, default="")
    country = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    timezone = serializers.CharField(required=False, allow_blank=True, default="")
    currency = serializers.CharField(required=False, allow_blank=True, default="")
    star_rating = serializers.IntegerField(required=False, min_value=0, max_value=5, default=0)
