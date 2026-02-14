from decimal import Decimal
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Folio, FolioItem, Invoice, Payment, RefundRequest, CashierShift, NightAuditRun
from .serializers import (
    FolioSerializer, FolioItemSerializer, InvoiceSerializer,
    PaymentSerializer, RefundRequestSerializer, CashierShiftSerializer, NightAuditRunSerializer
)
from .permissions import IsHotelStaff, IsManagerForRefundApproval
from . import services


class FolioViewSet(viewsets.ModelViewSet):
    queryset = Folio.objects.all().select_related("hotel", "reservation")
    serializer_class = FolioSerializer
    permission_classes = [IsHotelStaff]
    filterset_fields = ["hotel", "status", "reservation"]
    search_fields = ["notes"]
    ordering_fields = ["id", "created_at", "updated_at"]

    @action(detail=True, methods=["post"], url_path="charges")
    def add_charge(self, request, pk=None):
        folio = self.get_object()
        payload = request.data

        item = services.add_charge(
            folio=folio,
            item_type=payload.get("item_type", "other"),
            description=payload.get("description", ""),
            quantity=Decimal(str(payload.get("quantity", "1"))),
            unit_price=Decimal(str(payload.get("unit_price", "0"))),
            tax_rate=Decimal(str(payload.get("tax_rate", "0"))),
            is_tax_inclusive=bool(payload.get("is_tax_inclusive", False)),
            posted_by=request.user,
        )
        return Response(FolioItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="recalc")
    def recalc(self, request, pk=None):
        folio = self.get_object()
        folio.recalc()
        return Response(FolioSerializer(folio).data)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().select_related("hotel", "folio")
    serializer_class = InvoiceSerializer
    permission_classes = [IsHotelStaff]
    filterset_fields = ["hotel", "status"]
    search_fields = ["number"]
    ordering_fields = ["id", "created_at", "issued_at"]

    def create(self, request, *args, **kwargs):
        folio_id = request.data.get("folio")
        number = request.data.get("number")
        folio = Folio.objects.select_related("hotel").get(id=folio_id)
        inv = services.create_invoice(folio=folio, number=number, issued_by=request.user)
        return Response(InvoiceSerializer(inv).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="issue")
    def issue(self, request, pk=None):
        inv = self.get_object()
        inv = services.issue_invoice(invoice=inv, issued_by=request.user)
        return Response(InvoiceSerializer(inv).data)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related("hotel", "folio", "shift")
    serializer_class = PaymentSerializer
    permission_classes = [IsHotelStaff]
    filterset_fields = ["hotel", "method", "folio", "shift"]
    ordering_fields = ["id", "captured_at"]

    def create(self, request, *args, **kwargs):
        folio_id = request.data.get("folio")
        folio = Folio.objects.get(id=folio_id)

        shift_id = request.data.get("shift")
        shift = CashierShift.objects.filter(id=shift_id).first() if shift_id else None

        pay = services.take_payment(
            folio=folio,
            method=request.data.get("method"),
            amount=Decimal(str(request.data.get("amount"))),
            reference=request.data.get("reference", ""),
            captured_by=request.user,
            shift=shift,
        )
        return Response(PaymentSerializer(pay).data, status=status.HTTP_201_CREATED)


class RefundRequestViewSet(viewsets.ModelViewSet):
    queryset = RefundRequest.objects.all().select_related("hotel", "folio", "payment")
    serializer_class = RefundRequestSerializer
    permission_classes = [IsHotelStaff]
    filterset_fields = ["hotel", "status"]
    ordering_fields = ["id", "requested_at"]

    def create(self, request, *args, **kwargs):
        payment_id = request.data.get("payment")
        payment = Payment.objects.get(id=payment_id)
        rr = services.request_refund(
            payment=payment,
            amount=Decimal(str(request.data.get("amount"))),
            reason=request.data.get("reason", ""),
            requested_by=request.user,
        )
        return Response(RefundRequestSerializer(rr).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsManagerForRefundApproval])
    def approve(self, request, pk=None):
        rr = self.get_object()
        rr = services.approve_refund(refund=rr, decided_by=request.user, note=request.data.get("note", ""))
        return Response(RefundRequestSerializer(rr).data)

    @action(detail=True, methods=["post"], url_path="reject", permission_classes=[IsManagerForRefundApproval])
    def reject(self, request, pk=None):
        rr = self.get_object()
        rr = services.reject_refund(refund=rr, decided_by=request.user, note=request.data.get("note", ""))
        return Response(RefundRequestSerializer(rr).data)


class CashierShiftViewSet(viewsets.ModelViewSet):
    queryset = CashierShift.objects.all().select_related("hotel", "cashier")
    serializer_class = CashierShiftSerializer
    permission_classes = [IsHotelStaff]
    filterset_fields = ["hotel", "status", "cashier"]
    ordering_fields = ["id", "opened_at", "closed_at"]

    @action(detail=False, methods=["post"], url_path="open")
    def open_shift(self, request):
        hotel_id = request.data.get("hotel")
        shift = services.open_shift(
            hotel_id and __import__("apps.tenants.models").tenants.models.Hotel.objects.get(id=hotel_id),
            cashier=request.user,
            opening_float=Decimal(str(request.data.get("opening_float", "0"))),
        )
        return Response(CashierShiftSerializer(shift).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="close")
    def close_shift(self, request, pk=None):
        shift = self.get_object()
        shift = services.close_shift(shift=shift, closing_note=request.data.get("closing_note", ""))
        return Response(CashierShiftSerializer(shift).data)


class NightAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NightAuditRun.objects.all().select_related("hotel")
    serializer_class = NightAuditRunSerializer
    permission_classes = [IsHotelStaff]
    filterset_fields = ["hotel", "business_date", "status"]
    ordering_fields = ["business_date", "started_at"]

    @action(detail=False, methods=["post"], url_path="run")
    def run(self, request):
        hotel_id = request.data.get("hotel")
        business_date = request.data.get("business_date") or str(timezone.localdate())

        from apps.tenants.models import Hotel
        hotel = Hotel.objects.get(id=hotel_id)

        audit = services.run_night_audit(
            hotel=hotel,
            business_date=business_date,
            ran_by=request.user,
        )
        return Response(NightAuditRunSerializer(audit).data, status=status.HTTP_201_CREATED)
