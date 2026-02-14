from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Unit, ItemCategory, Item, Supplier, InventoryLocation,
    PurchaseOrder, GRN, ItemBatch, StockMovement,
    StockIssue, StockCount,
    RoomMinibar, MinibarTemplate, MinibarCount
)
from .serializers import (
    UnitSerializer, ItemCategorySerializer, ItemSerializer, SupplierSerializer, InventoryLocationSerializer,
    POSerializer, GRNSerializer, ItemBatchSerializer, StockMovementSerializer,
    StockIssueSerializer, StockCountSerializer,
    RoomMinibarSerializer, MinibarTemplateSerializer, MinibarCountSerializer
)
from .permissions import IsTenantStaff, IsManagerOrReadOnly
from .services import post_minibar_consumption


# ✅ You must already enforce tenant isolation like:
# qs = qs.filter(tenant=request.tenant) OR request.user.tenant
def tenant_id_from_request(request):
    # Change this to your Month-1 tenant resolver
    return getattr(request, "tenant_id", None) or getattr(getattr(request, "tenant", None), "id", None) or getattr(request.user, "tenant_id", None)


class TenantScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTenantStaff]

    def get_queryset(self):
        tenant_id = tenant_id_from_request(self.request)
        return self.queryset.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = tenant_id_from_request(self.request)
        serializer.save(tenant_id=tenant_id)


class UnitViewSet(TenantScopedViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class ItemCategoryViewSet(TenantScopedViewSet):
    queryset = ItemCategory.objects.all()
    serializer_class = ItemCategorySerializer


class InventoryLocationViewSet(TenantScopedViewSet):
    queryset = InventoryLocation.objects.all()
    serializer_class = InventoryLocationSerializer


class ItemViewSet(TenantScopedViewSet):
    queryset = Item.objects.select_related("unit", "category").all()
    serializer_class = ItemSerializer

    @action(detail=False, methods=["get"])
    def alerts(self, request):
        """
        Alerts: low stock + expiry soon + expired
        """
        tenant_id = tenant_id_from_request(request)

        # Low stock (on-hand <= reorder_level)
        # on-hand per item across locations
        item_onhand = (
            StockMovement.objects
            .filter(tenant_id=tenant_id)
            .values("item_id")
            .annotate(on_hand=Sum("qty"))
        )
        low_ids = []
        for row in item_onhand:
            low_ids.append(row["item_id"])

        items = Item.objects.filter(tenant_id=tenant_id, is_active=True)

        # expiry soon
        today = timezone.now().date()
        soon = today + timedelta(days=30)

        expiring_batches = ItemBatch.objects.filter(
            tenant_id=tenant_id,
            expiry_date__isnull=False
        ).filter(Q(expiry_date__lte=soon))

        return Response({
            "low_stock_hint": "Compute low stock in UI by comparing on_hand vs reorder_level per item (see /stock/movements/ summary).",
            "expiring_batches": ItemBatchSerializer(expiring_batches[:200], many=True).data,
        })


class SupplierViewSet(TenantScopedViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseOrderViewSet(TenantScopedViewSet):
    queryset = PurchaseOrder.objects.select_related("supplier").prefetch_related("lines").all()
    serializer_class = POSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        po = self.get_object()
        if po.status not in [PurchaseOrder.STATUS_DRAFT, PurchaseOrder.STATUS_SENT]:
            return Response({"detail": "PO cannot be approved in current status."}, status=400)
        po.status = PurchaseOrder.STATUS_APPROVED
        po.save(update_fields=["status"])
        return Response({"ok": True, "status": po.status})


class GRNViewSet(TenantScopedViewSet):
    queryset = GRN.objects.select_related("po", "location").all()
    serializer_class = GRNSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]


class StockMovementViewSet(TenantScopedViewSet):
    queryset = StockMovement.objects.select_related("item", "location", "batch").all()
    serializer_class = StockMovementSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        tenant_id = tenant_id_from_request(request)
        location = request.query_params.get("location")
        qs = StockMovement.objects.filter(tenant_id=tenant_id)
        if location:
            qs = qs.filter(location_id=location)

        data = (
            qs.values("item_id")
            .annotate(on_hand=Sum("qty"))
            .order_by("item_id")[:5000]
        )
        return Response({"results": list(data)})


class StockIssueViewSet(TenantScopedViewSet):
    queryset = StockIssue.objects.prefetch_related("lines").all()
    serializer_class = StockIssueSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        issue = self.get_object()
        issue.approve_and_post(request.user)
        return Response({"ok": True, "status": issue.status})


class StockCountViewSet(TenantScopedViewSet):
    queryset = StockCount.objects.prefetch_related("lines").all()
    serializer_class = StockCountSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):
        count = self.get_object()
        count.post_adjustments(request.user)
        return Response({"ok": True, "status": count.status})


class MinibarTemplateViewSet(TenantScopedViewSet):
    queryset = MinibarTemplate.objects.prefetch_related("lines").all()
    serializer_class = MinibarTemplateSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]


class RoomMinibarViewSet(TenantScopedViewSet):
    queryset = RoomMinibar.objects.select_related("template", "stock_location").all()
    serializer_class = RoomMinibarSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]


class MinibarCountViewSet(TenantScopedViewSet):
    queryset = MinibarCount.objects.select_related("room_minibar", "folio").prefetch_related("lines").all()
    serializer_class = MinibarCountSerializer
    permission_classes = [IsTenantStaff, IsManagerOrReadOnly]

    @action(detail=True, methods=["post"])
    def post_to_folio(self, request, pk=None):
        obj = self.get_object()
        post_minibar_consumption(obj, request.user)
        return Response({"ok": True, "posted_at": obj.posted_at})
