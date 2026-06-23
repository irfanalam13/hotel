from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    """Public self-service registration. Membership in an org is granted separately."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.create_user(**serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """Read / update the authenticated user's own profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Touch last-seen on profile read (cheap heartbeat).
        request.user.last_login_at = timezone.now()
        request.user.save(update_fields=["last_login_at"])
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = services.update_profile(user=request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_password(user=request.user, **serializer.validated_data)
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)
