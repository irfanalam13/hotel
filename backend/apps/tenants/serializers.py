from rest_framework import serializers
from django.db import transaction
from apps.tenants.models import Hotel, Plan, Branch, HotelSettings
from apps.accounts.models import User

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "code", "name", "monthly_price", "max_branches", "max_staff", "max_rooms", "features"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "code", "address", "phone", "is_active", "created_at"]


class HotelSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelSettings
        fields = [
            "vat_percent", "service_charge_percent",
            "receipt_header", "receipt_footer",
            "policies"
        ]


class HotelSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    settings = HotelSettingsSerializer(read_only=True)
    class Meta:
        model = Hotel
        fields = ["id", "name", "hotel_code", "subdomain", "plan", "timezone", "currency", "is_active", "settings"]


class TenantOnboardSerializer(serializers.Serializer):
    # hotel
    hotel_name = serializers.CharField(max_length=120)
    hotel_code = serializers.SlugField(max_length=40)
    subdomain = serializers.SlugField(max_length=40, required=False, allow_null=True, allow_blank=True)

    # plan
    plan_code = serializers.CharField(max_length=32)

    # owner
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(min_length=8, write_only=True)
    owner_full_name = serializers.CharField(max_length=120)

    # first branch
    branch_name = serializers.CharField(max_length=120, default="Main Branch")
    branch_code = serializers.SlugField(max_length=40, default="main")

    def validate_plan_code(self, v):
        if not Plan.objects.filter(code=v).exists():
            raise serializers.ValidationError("Invalid plan_code")
        return v

    @transaction.atomic
    def create(self, validated):
        plan = Plan.objects.get(code=validated["plan_code"])

        hotel = Hotel.objects.create(
            name=validated["hotel_name"],
            hotel_code=validated["hotel_code"],
            subdomain=validated.get("subdomain") or None,
            plan=plan,
        )

        branch = Branch.objects.create(
            hotel=hotel,
            name=validated["branch_name"],
            code=validated["branch_code"],
        )

        HotelSettings.objects.create(
            hotel=hotel,
            policies={
                "check_in_time": "14:00",
                "check_out_time": "12:00",
                "cancellation_hours": 24,
                "no_show_fee_percent": 50
            }
        )

        owner = User.objects.create_user(
            email=validated["owner_email"],
            password=validated["owner_password"],
            full_name=validated["owner_full_name"],
            hotel=hotel,
            branch=branch,
            role="OWNER",
            is_staff=True,
        )

        return {"hotel": hotel, "branch": branch, "owner": owner}
