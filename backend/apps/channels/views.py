from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ChannelProvider, ChannelCredential, ChannelRoomMap, ChannelSyncJob
from .serializers import (
    ChannelProviderSerializer, ChannelCredentialSerializer,
    ChannelRoomMapSerializer, ChannelSyncJobSerializer
)
from .services import run_sync_job


class TenantScopedMixin:
    def get_hotel(self):
        return getattr(self.request, "hotel", None) or getattr(self.request, "tenant", None)

    def perform_create(self, serializer):
        serializer.save(hotel=self.get_hotel())


class ChannelProviderViewSet(ReadOnlyModelViewSet):
    queryset = ChannelProvider.objects.filter(is_active=True)
    serializer_class = ChannelProviderSerializer
    permission_classes = [IsAuthenticated]


class ChannelCredentialViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = ChannelCredentialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChannelCredential.objects.filter(hotel=self.get_hotel(), is_active=True).select_related("provider")


class ChannelRoomMapViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = ChannelRoomMapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChannelRoomMap.objects.filter(hotel=self.get_hotel()).select_related("provider", "room_type")


class ChannelSyncJobViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = ChannelSyncJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChannelSyncJob.objects.filter(hotel=self.get_hotel()).select_related("provider").prefetch_related("logs")

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        job = self.get_object()
        # For production: run via Celery; for now run inline
        run_sync_job(job.id)
        job.refresh_from_db()
        return Response(ChannelSyncJobSerializer(job).data)
