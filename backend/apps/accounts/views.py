from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.serializers import MeSerializer, InviteCreateSerializer, InviteAcceptSerializer
from apps.accounts.models import StaffInvite
from apps.common.permissions import IsAuthenticatedAndTenant, IsManagerOrOwner

class MeView(APIView):
    permission_classes = [IsAuthenticatedAndTenant]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class InviteViewSet(ModelViewSet):
    serializer_class = InviteCreateSerializer
    permission_classes = [IsAuthenticatedAndTenant, IsManagerOrOwner]

    def get_queryset(self):
        return StaffInvite.objects.filter(hotel=self.request.tenant).order_by("-created_at")


class InviteAcceptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = InviteAcceptSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"detail": "Invite accepted", "user_id": str(user.id)}, status=status.HTTP_201_CREATED)


class AuthTokenView(TokenObtainPairView):
    """
    JWT login. Tenant is resolved by middleware (subdomain / X-Hotel-Code).
    """
    pass


class AuthRefreshView(TokenRefreshView):
    pass
