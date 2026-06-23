from __future__ import annotations

from rest_framework import serializers

from .constants import ALL_PERMISSIONS, PERMISSION_CATALOG
from .models import Role


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ("id", "code", "name", "description", "is_system", "permissions", "created_at")
        read_only_fields = ("id", "is_system", "created_at")

    def get_permissions(self, obj: Role) -> list[str]:
        return sorted(obj.permission_codes)


class RoleWriteSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    name = serializers.CharField(max_length=80)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    permissions = serializers.ListField(child=serializers.CharField(), default=list)

    def validate_permissions(self, value):
        unknown = set(value) - set(ALL_PERMISSIONS)
        if unknown:
            raise serializers.ValidationError(f"Unknown permissions: {sorted(unknown)}")
        return value


class PermissionCatalogSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()

    @staticmethod
    def catalog() -> list[dict]:
        return [{"code": c, "label": label} for c, label in PERMISSION_CATALOG.items()]
