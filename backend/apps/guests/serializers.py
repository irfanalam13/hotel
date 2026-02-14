from rest_framework import serializers
from .models import Guest, GuestDocument

class GuestDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestDocument
        fields = [
            "id", "property", "guest",
            "doc_type", "doc_number", "issued_country",
            "file", "uploaded_at"
        ]
        read_only_fields = ["property", "uploaded_at"]

class GuestSerializer(serializers.ModelSerializer):
    documents = GuestDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Guest
        fields = [
            "id", "property",
            "first_name", "last_name",
            "phone", "email",
            "nationality", "address",
            "created_at",
            "documents",
        ]
        read_only_fields = ["property", "created_at"]
