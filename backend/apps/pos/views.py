from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.db.models import Sum
from decimal import Decimal

from .models import (
    MenuCategory, MenuItem, DiningTable,
    POSOrder, KOTTicket,
    CashDrawerShift, Settlement,
    ApprovalRequest, RoomPost
)
from .serializers import (
    MenuCategorySerializer, MenuItemSerializer, DiningTableSerializer,
    POSOrderSerializer, POSOrderCreateSerializer, POSOrderItemSerializer,
    AddItemSerializer, KOTTicketSerializer,
    CashDrawerShiftSerializer, ShiftCloseSerializer,
    SettlementSerializer,
    RoomPostRequestSerializer, RoomPostSerializer,
    ApprovalRequestSerializer, ApprovalCreateSerializer, ApprovalDecideSerializer
)
from .permissions import IsPOSStaff, IsPOSManager
from .services import add_item_to_order, create_kot_for_order, room_post_order, request_void_order, decide_approval
from .kot_pdf import kot_to_pdf_response

class TenantScopedMixin:
    def get_tenant(self):
        # Assuming middleware sets request.tenant
        return getattr(self.request, "tenant", None)

class MenuCategoryViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsPOSStaff]
    serializer_class = MenuCategorySerializer

    def get_queryset(self):
        return MenuCategory.objects.filter(tenant=self.get_tenant())

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant())

class MenuItemViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsPOSStaff]
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        return MenuItem.objects.select_related("category").filter(tenant=self.get_tenant())

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        category = get_object_or_404(MenuCategory, tenant=tenant, id=serializer.validated_data["category_id"])
        serializer.save(tenant=tenant, category=category)

    def perform_update(self, serializer):
        tenant = self.get_tenant()
        data = serializer.validated_data
        if "category_id" in data:
            category = get_object_or_404(MenuCategory, tenant=tenant, id=data["category_id"])
            serializer.save(category=category)
        else:
            serializer.save()

class DiningTableViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsPOSStaff]
    serializer_class = DiningTableSerializer

    def get_queryset(self):
        return DiningTable.objects.filter(tenant=self.get_tenant())

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant())

class POSOrderViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsPOSStaff]

    def get_queryset(self):
        return POSOrder.objects.filter(tenant=self.get_tenant()).prefetch_related("items__menu_item", "kots")

    def get_serializer_class(self):
        if self.action == "create":
            return POSOrderCreateSerializer
        return POSOrderSerializer

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant(), created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, pk=None):
        order = self.get_object()
        s = AddItemSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        tenant = self.get_tenant()
        menu_item = get_object_or_404(MenuItem, tenant=tenant, id=s.validated_data["menu_item_id"], is_active=True)

        item = add_item_to_order(
            order=order,
            menu_item=menu_item,
            qty=s.validated_data["qty"],
            note=s.validated_data.get("note", ""),
        )
        return Response(POSOrderItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="send-kot")
    def send_kot(self, request, pk=None):
        order = self.get_object()
        station = request.data.get("station", "")
        kot = create_kot_for_order(order=order, user=request.user, station=station)
        return Response(KOTTicketSerializer(kot).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="kots/(?P<kot_id>[^/.]+)/pdf")
    def kot_pdf(self, request, pk=None, kot_id=None):
        order = self.get_object()
        kot = get_object_or_404(KOTTicket, tenant=self.get_tenant(), order=order, id=kot_id)
        return kot_to_pdf_response(kot)

    @action(detail=True, methods=["post"], url_path="request-void")
    def request_void(self, request, pk=None):
        order = self.get_object()
        reason = request.data.get("reason", "")
        idempotency_key = request.data.get("idempotency_key", "")
        approval = request_void_order(order=order, user=request.user, reason=reason, idempotency_key=idempotency_key)
        return Response(ApprovalRequestSerializer(approval).data, status=status.HTTP_201_CREATED)

class CashDrawerShiftViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsPOSStaff]
    serializer_class = CashDrawerShiftSerializer

    def get_queryset(self):
        return CashDrawerShift.objects.filter(tenant=self.get_tenant())

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant(), opened_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="close")
    def close_shift(self, request, pk=None):
        shift = self.get_object()
        s = ShiftCloseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        shift.close(user=request.user, closing_cash=s.validated_data["closing_cash"], notes=s.validated_data.get("notes", ""))
        return Response(CashDrawerShiftSerializer(shift).data)

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        shift = self.get_object()
        qs = shift.settlements.filter(status=Settlement.Status.PAID)
        by_method = qs.values("method").annotate(total=Sum("amount")).order_by("method")
        total_sales = shift.orders.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        return Response({
            "shift_id": shift.id,
            "total_sales": str(total_sales),
            "settlements_by_method": [{"method": x["method"], "total": str(x["total"])} for x in by_method],
        })

class SettlementViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsPOSStaff]
    serializer_class = SettlementSerializer

    def get_queryset(self):
        return Settlement.objects.filter(tenant=self.get_tenant()).select_related("order")

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        order = serializer.validated_data["order"]
        if order.tenant_id != tenant.id:
            raise PermissionError("Cross-tenant access blocked.")
        serializer.save(tenant=tenant, branch=order.branch, received_by=self.request.user)

class RoomPostViewSet(TenantScopedMixin, viewsets.ViewSet):
    permission_classes = [IsPOSStaff]

    @action(detail=False, methods=["post"], url_path="room-post")
    def room_post(self, request):
        s = RoomPostRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        tenant = self.get_tenant()
        order = get_object_or_404(POSOrder, tenant=tenant, id=s.validated_data["order_id"])
        from apps.billing.models import Folio
        folio = get_object_or_404(Folio, tenant=tenant, id=s.validated_data["folio_id"])

        rp = room_post_order(order=order, folio=folio, user=request.user, idempotency_key=s.validated_data["idempotency_key"])
        return Response(RoomPostSerializer(rp).data, status=status.HTTP_201_CREATED)

class ApprovalRequestViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.none()
    permission_classes = [IsPOSManager]
    serializer_class = ApprovalRequestSerializer

    def get_queryset(self):
        return ApprovalRequest.objects.filter(tenant=self.get_tenant())

    def create(self, request, *args, **kwargs):
        # Typically created by POS endpoints (like request_void). Keep manager create optional.
        s = ApprovalCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tenant = self.get_tenant()
        order = get_object_or_404(POSOrder, tenant=tenant, id=s.validated_data["order_id"])
        approval = request_void_order(order=order, user=request.user, reason=s.validated_data["reason"], idempotency_key=s.validated_data["idempotency_key"])
        return Response(ApprovalRequestSerializer(approval).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        approval = self.get_object()
        s = ApprovalDecideSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        approval = decide_approval(approval=approval, manager=request.user, approve=s.validated_data["approve"], note=s.validated_data.get("note", ""))
        return Response(ApprovalRequestSerializer(approval).data)
