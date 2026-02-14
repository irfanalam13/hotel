from rest_framework import serializers
from django.utils import timezone
from apps.accounts.models import User, StaffInvite, ROLE_CHOICES

class MeSerializer(serializers.ModelSerializer):
    hotel_code = serializers.SerializerMethodField()
    branch_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "hotel_code", "branch_code"]

    def get_hotel_code(self, obj):
        return obj.hotel.hotel_code if obj.hotel else None

    def get_branch_code(self, obj):
        return obj.branch.code if obj.branch else None


class InviteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffInvite
        fields = ["id", "email", "role", "branch", "expires_at"]
        read_only_fields = ["id"]

    def validate_role(self, v):
        roles = [r[0] for r in ROLE_CHOICES]
        if v not in roles:
            raise serializers.ValidationError("Invalid role")
        return v

    def create(self, validated):
        request = self.context["request"]
        validated["hotel"] = request.tenant
        validated["invited_by"] = request.user
        return super().create(validated)


class InviteAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
    full_name = serializers.CharField(max_length=120)
    password = serializers.CharField(min_length=8, write_only=True)

    def save(self):
        token = self.validated_data["token"]
        invite = StaffInvite.objects.select_related("hotel", "branch").filter(token=token).first()
        if not invite or not invite.is_valid:
            raise serializers.ValidationError({"token": "Invite is invalid/expired."})

        # prevent duplicates
        if User.objects.filter(email=invite.email).exists():
            raise serializers.ValidationError({"email": "User already exists."})

        user = User.objects.create_user(
            email=invite.email,
            password=self.validated_data["password"],
            full_name=self.validated_data["full_name"],
            hotel=invite.hotel,
            branch=invite.branch,
            role=invite.role,
            is_staff=True,
        )
        invite.accepted_at = timezone.now()
        invite.save(update_fields=["accepted_at"])
        return user
