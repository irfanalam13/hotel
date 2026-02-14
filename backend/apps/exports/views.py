from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AccountingExportJob
from .serializers import AccountingExportJobSerializer
from .services import run_export_job


class TenantScopedMixin:
    def get_hotel(self):
        return getattr(self.request, "hotel", None) or getattr(self.request, "tenant", None)

    def perform_create(self, serializer):
        serializer.save(hotel=self.get_hotel())


class AccountingExportJobViewSet(TenantScopedMixin, ModelViewSet):
    serializer_class = AccountingExportJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AccountingExportJob.objects.filter(hotel=self.get_hotel()).order_by("-created_at")

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        job = self.get_object()
        run_export_job(job.id)  # production: Celery
        job.refresh_from_db()
        return Response(AccountingExportJobSerializer(job).data)
