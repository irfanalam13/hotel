from __future__ import annotations

from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = (
            "id", "action", "method", "path", "status_code",
            "object_type", "object_id", "user_email", "ip",
            "changes", "created_at",
        )
        read_only_fields = fields
