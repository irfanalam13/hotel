from rest_framework import serializers
from .models import (
    Folio, FolioItem, Invoice, Payment, RefundRequest, CashierShift, NightAuditRun
)

class FolioItemSerializer(serializers.ModelSerializer):
    line_subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    line_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    line_base = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FolioItem
        fields = [
            "id","folio","item_type","description","quantity","unit_price",
            "tax_rate","is_tax_inclusive","is_void","void_reason",
            "posted_by","posted_at","currency",
            "line_base","line_subtotal","line_tax",
        ]
        read_only_fields = ["posted_by","posted_at","currency"]


class FolioSerializer(serializers.ModelSerializer):
    items = FolioItemSerializer(many=True, read_only=True)

    class Meta:
        model = Folio
        fields = [
            "id","hotel","reservation","status","notes",
            "subtotal","tax_total","total","balance_due","currency",
            "created_at","updated_at","items",
        ]
        read_only_fields = ["subtotal","tax_total","total","balance_due","created_at","updated_at","currency"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id","hotel","folio","number","status","issued_at","issued_by",
            "subtotal","tax_total","total","currency","pdf_file","created_at"
        ]
        read_only_fields = ["issued_at","issued_by","subtotal","tax_total","total","currency","pdf_file","created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id","hotel","folio","method","amount","reference","status",
            "captured_by","captured_at","currency","shift"
        ]
        read_only_fields = ["status","captured_by","captured_at","currency"]


class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = [
            "id","hotel","folio","payment","amount","reason","status",
            "requested_by","requested_at","decided_by","decided_at","decision_note","currency"
        ]
        read_only_fields = ["status","requested_by","requested_at","decided_by","decided_at","decision_note","currency"]


class CashierShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashierShift
        fields = ["id","hotel","cashier","status","opened_at","closed_at","opening_float","closing_note"]
        read_only_fields = ["status","opened_at","closed_at"]


class NightAuditRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = NightAuditRun
        fields = ["id","hotel","business_date","status","started_at","finished_at","totals","errors","ran_by"]
        read_only_fields = ["status","started_at","finished_at","totals","errors","ran_by"]
