from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Membership, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "id", "name", "slug", "is_active", "plan",
            "max_properties", "timezone", "currency", "settings", "created_at",
        )
        read_only_fields = ("id", "slug", "is_active", "created_at")


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=64, required=False)
    plan = serializers.ChoiceField(
        choices=Organization.Plan.choices, default=Organization.Plan.FREE
    )
    timezone = serializers.CharField(required=False, default="UTC")
    currency = serializers.CharField(required=False, default="USD")


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role_code = serializers.CharField(source="role.code", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = Membership
        fields = (
            "id", "user", "role_code", "role_name",
            "is_active", "is_default", "created_at",
        )


class MemberInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role_code = serializers.CharField()
    full_name = serializers.CharField(required=False, allow_blank=True, default="")


class MemberRoleUpdateSerializer(serializers.Serializer):
    role_code = serializers.CharField()
