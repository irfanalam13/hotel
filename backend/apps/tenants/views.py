from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from apps.tenants.models import Plan, Branch, HotelSettings
from apps.tenants.serializers import (
    TenantOnboardSerializer, PlanSerializer, BranchSerializer, HotelSettingsSerializer
)
from apps.common.permissions import IsAuthenticatedAndTenant, IsManagerOrOwner

class TenantOnboardView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = TenantOnboardSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        out = ser.save()
        return Response(
            {
                "hotel_id": str(out["hotel"].id),
                "hotel_code": out["hotel"].hotel_code,
                "branch_id": str(out["branch"].id),
                "owner_id": str(out["owner"].id),
            },
            status=status.HTTP_201_CREATED
        )


class PlanViewSet(ModelViewSet):
    queryset = Plan.objects.all().order_by("monthly_price")
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]  # plans are public


class BranchViewSet(ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticatedAndTenant, IsManagerOrOwner]

    def get_queryset(self):
        return Branch.objects.filter(hotel=self.request.tenant).order_by("created_at")

    def perform_create(self, serializer):
        # real-life guard: plan limit
        hotel = self.request.tenant
        current = Branch.objects.filter(hotel=hotel).count()
        if current >= hotel.plan.max_branches:
            raise ValueError("Branch limit reached for current plan.")
        serializer.save(hotel=hotel)


class SettingsView(APIView):
    permission_classes = [IsAuthenticatedAndTenant, IsManagerOrOwner]

    def get(self, request):
        s = request.tenant.settings
        return Response(HotelSettingsSerializer(s).data)

    def patch(self, request):
        s = request.tenant.settings
        ser = HotelSettingsSerializer(s, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
