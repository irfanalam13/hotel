from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from django.utils.timezone import now

from .permissions import IsTenantOwnerOrManager
from .serializers import DateRangeQuerySerializer, ExportJobSerializer, ExportScheduleSerializer
from .models import ExportJob, ExportSchedule
from . import selectors
from .tasks import run_export_job


def _tenant_id(request):
    # adapt to your tenant middleware
    return str(getattr(request, "tenant_id"))

class KPIView(APIView):
    permission_classes = [IsTenantOwnerOrManager]

    def get(self, request):
        q = DateRangeQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        data = q.validated_data

        payload = selectors.kpi_summary(
            tenant_id=_tenant_id(request),
            property_id=data.get("property_id"),
            start=data["start"],
            end=data["end"],
        )
        return Response(payload)

class RevenueByDepartmentView(APIView):
    permission_classes = [IsTenantOwnerOrManager]

    def get(self, request):
        q = DateRangeQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        d = q.validated_data

        rows = selectors.revenue_by_department(
            tenant_id=_tenant_id(request),
            property_id=d.get("property_id"),
            start=d["start"],
            end=d["end"],
        )
        return Response({"rows": rows})

class CxlNoShowView(APIView):
    permission_classes = [IsTenantOwnerOrManager]

    def get(self, request):
        q = DateRangeQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        d = q.validated_data

        return Response(
            selectors.cancellations_and_noshows(
                tenant_id=_tenant_id(request),
                property_id=d.get("property_id"),
                start=d["start"],
                end=d["end"],
            )
        )

class DiscountRefundAuditView(APIView):
    permission_classes = [IsTenantOwnerOrManager]

    def get(self, request):
        q = DateRangeQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        d = q.validated_data

        return Response(
            selectors.discount_refund_audit(
                tenant_id=_tenant_id(request),
                property_id=d.get("property_id"),
                start=d["start"],
                end=d["end"],
            )
        )

class StockVarianceView(APIView):
    permission_classes = [IsTenantOwnerOrManager]

    def get(self, request):
        q = DateRangeQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        d = q.validated_data

        return Response(
            selectors.stock_variance(
                tenant_id=_tenant_id(request),
                property_id=d.get("property_id"),
                start=d["start"],
                end=d["end"],
            )
        )

class StaffActivityView(APIView):
    permission_classes = [IsTenantOwnerOrManager]

    def get(self, request):
        q = DateRangeQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        d = q.validated_data

        return Response(
            selectors.staff_activity(
                tenant_id=_tenant_id(request),
                property_id=d.get("property_id"),
                start=d["start"],
                end=d["end"],
            )
        )

class ExportJobViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsTenantOwnerOrManager]
    serializer_class = ExportJobSerializer

    def get_queryset(self):
        return ExportJob.objects.filter(tenant_id=_tenant_id(self.request)).order_by("-created_at")

    @action(detail=False, methods=["post"])
    def create_export(self, request):
        """
        POST /api/reports/exports/create_export/
        body: { kind, fmt, start, end, property_id? }
        """
        kind = request.data.get("kind")
        fmt = request.data.get("fmt")
        start = request.data.get("start")
        end = request.data.get("end")
        property_id = request.data.get("property_id")

        job = ExportJob.objects.create(
            tenant_id=_tenant_id(request),
            property_id=property_id,
            kind=kind,
            fmt=fmt,
            params={"start": start, "end": end},
            created_by=request.user,
        )
        run_export_job.delay(str(job.id))
        return Response(ExportJobSerializer(job).data, status=status.HTTP_201_CREATED)

class ExportScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTenantOwnerOrManager]
    serializer_class = ExportScheduleSerializer

    def get_queryset(self):
        return ExportSchedule.objects.filter(tenant_id=_tenant_id(self.request)).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(tenant_id=_tenant_id(self.request), created_by=self.request.user)
