from rest_framework import serializers
from decimal import Decimal
from .models import (
    MenuCategory, MenuItem, DiningTable,
    POSOrder, POSOrderItem,
    KOTTicket, CashDrawerShift,
    Settlement, ApprovalRequest, RoomPost
)

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ["id", "name", "is_active", "sort_order"]

class MenuItemSerializer(serializers.ModelSerializer):
    category = MenuCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "category", "category_id", "name", "sku", "price", "tax_rate", "kitchen_station", "is_alcohol", "is_active"]

class DiningTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningTable
        fields = ["id", "name", "area", "seats", "is_active"]

class POSOrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = POSOrderItem
        fields = ["id", "menu_item", "menu_item_name", "qty", "unit_price", "tax_rate", "notes"]

class POSOrderSerializer(serializers.ModelSerializer):
    items = POSOrderItemSerializer(many=True, read_only=True)
    table_name = serializers.CharField(source="table.name", read_only=True)

    class Meta:
        model = POSOrder
        fields = [
            "id", "branch", "table", "table_name", "source", "status",
            "waiter_name", "notes", "reservation", "folio", "cash_shift",
            "subtotal", "tax_total", "total",
            "created_by", "created_at", "items",
        ]
        read_only_fields = ["created_by", "created_at", "subtotal", "tax_total", "total", "status"]

class POSOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSOrder
        fields = ["branch", "table", "source", "waiter_name", "notes", "cash_shift"]

class AddItemSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True)

class KOTTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = KOTTicket
        fields = ["id", "order", "kot_no", "created_at", "station"]

class CashDrawerShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashDrawerShift
        fields = ["id", "branch", "opened_by", "opened_at", "opening_float", "is_closed", "closed_by", "closed_at", "closing_cash", "notes"]
        read_only_fields = ["opened_by", "opened_at", "is_closed", "closed_by", "closed_at"]

class ShiftCloseSerializer(serializers.Serializer):
    closing_cash = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)

class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = ["id", "order", "method", "status", "amount", "reference", "received_by", "received_at", "cash_shift"]
        read_only_fields = ["status", "received_by", "received_at"]

class RoomPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomPost
        fields = ["id", "order", "folio", "folio_item", "posted_by", "posted_at", "amount", "idempotency_key"]
        read_only_fields = ["folio_item", "posted_by", "posted_at", "amount"]

class RoomPostRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    folio_id = serializers.IntegerField()
    idempotency_key = serializers.CharField(max_length=120)

class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = [
            "id", "request_type", "status",
            "order", "settlement",
            "reason", "requested_by", "requested_at",
            "decided_by", "decided_at", "decision_note",
            "idempotency_key",
        ]
        read_only_fields = ["status", "requested_by", "requested_at", "decided_by", "decided_at", "decision_note"]

class ApprovalCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField()
    idempotency_key = serializers.CharField(max_length=120)

class ApprovalDecideSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    note = serializers.CharField(required=False, allow_blank=True)
