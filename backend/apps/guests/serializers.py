from __future__ import annotations

from rest_framework import serializers

from .models import Guest, GuestDocument


class GuestDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestDocument
        fields = ("id", "guest", "doc_type", "doc_number", "issued_country", "file", "created_at")
        read_only_fields = ("id", "guest", "created_at")


class GuestSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    documents = GuestDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Guest
        fields = (
            "id", "property", "first_name", "last_name", "full_name",
            "email", "phone", "nationality", "address", "date_of_birth",
            "notes", "documents", "created_at",
        )
        read_only_fields = ("id", "full_name", "documents", "created_at")


class GuestCreateSerializer(serializers.Serializer):
    property = serializers.UUIDField()
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    nationality = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
    address = serializers.CharField(required=False, allow_blank=True, default="")
    date_of_birth = serializers.DateField(required=False, allow_null=True)
