from rest_framework import serializers
from .models import (
    Unit, ItemCategory, Item, Supplier, InventoryLocation,
    PurchaseOrder, PurchaseOrderLine,
    GRN, ItemBatch, StockMovement,
    StockIssue, StockIssueLine,
    StockCount, StockCountLine,
    MinibarTemplate, MinibarTemplateLine,
    RoomMinibar, MinibarCount, MinibarCountLine
)
from .services import post_minibar_consumption, receive_grn_to_stock


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "name", "symbol", "created_at"]


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ["id", "name"]


class InventoryLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLocation
        fields = ["id", "name", "code", "is_default", "is_active"]


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            "id","sku","name","category","unit","is_active",
            "reorder_level","expiry_tracking","default_cost",
            "is_minibar_item","minibar_sell_price",
        ]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id","name","phone","email","address"]


class POLineSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ["id","item","qty_ordered","unit_cost","line_total"]


class POSerializer(serializers.ModelSerializer):
    lines = POLineSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id","po_number","supplier","status","expected_date","notes","lines","created_at"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        po = PurchaseOrder.objects.create(**validated)
        for ln in lines:
            PurchaseOrderLine.objects.create(po=po, **ln)
        return po

    def update(self, instance, validated):
        lines = validated.pop("lines", None)
        for k,v in validated.items():
            setattr(instance, k, v)
        instance.save()

        if lines is not None:
            instance.lines.all().delete()
            for ln in lines:
                PurchaseOrderLine.objects.create(po=instance, **ln)
        return instance


class GRNLineInputSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    qty_received = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    batch_code = serializers.CharField(required=False, allow_blank=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)


class GRNSerializer(serializers.ModelSerializer):
    receive_lines = GRNLineInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = GRN
        fields = ["id","grn_number","po","received_date","location","notes","created_at","receive_lines"]

    def create(self, validated):
        receive_lines = validated.pop("receive_lines", [])
        grn = GRN.objects.create(**validated)
        if receive_lines:
            receive_grn_to_stock(grn, receive_lines, self.context["request"].user)
        return grn


class ItemBatchSerializer(serializers.ModelSerializer):
    on_hand = serializers.SerializerMethodField()

    class Meta:
        model = ItemBatch
        fields = ["id","item","location","batch_code","expiry_date","unit_cost","on_hand"]

    def get_on_hand(self, obj):
        return obj.on_hand()


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id","item","location","batch","movement_type","qty","unit_cost","reference","note","created_at"]


class StockIssueLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockIssueLine
        fields = ["id","item","batch","qty","unit_cost"]


class StockIssueSerializer(serializers.ModelSerializer):
    lines = StockIssueLineSerializer(many=True)

    class Meta:
        model = StockIssue
        fields = [
            "id","issue_number","from_location","department","status",
            "requested_by","approved_by","approved_at","notes","lines","created_at"
        ]
        read_only_fields = ["approved_by","approved_at","status"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        issue = StockIssue.objects.create(**validated)
        for ln in lines:
            StockIssueLine.objects.create(issue=issue, **ln)
        return issue


class StockCountLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCountLine
        fields = ["id","item","batch","counted_qty","unit_cost","reason"]


class StockCountSerializer(serializers.ModelSerializer):
    lines = StockCountLineSerializer(many=True)

    class Meta:
        model = StockCount
        fields = ["id","count_number","location","status","counted_by","approved_by","approved_at","notes","lines","created_at"]
        read_only_fields = ["status","approved_by","approved_at"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        obj = StockCount.objects.create(**validated)
        for ln in lines:
            StockCountLine.objects.create(count=obj, **ln)
        return obj


# ---------------- MINIBAR ----------------

class MinibarTemplateLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = MinibarTemplateLine
        fields = ["id","item","par_level"]


class MinibarTemplateSerializer(serializers.ModelSerializer):
    lines = MinibarTemplateLineSerializer(many=True)

    class Meta:
        model = MinibarTemplate
        fields = ["id","name","is_active","lines"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        t = MinibarTemplate.objects.create(**validated)
        for ln in lines:
            MinibarTemplateLine.objects.create(template=t, **ln)
        return t


class RoomMinibarSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMinibar
        fields = ["id","room","template","stock_location","is_active"]


class MinibarCountLineSerializer(serializers.ModelSerializer):
    consumed_qty = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = MinibarCountLine
        fields = ["id","item","expected_qty","actual_qty","sell_price","consumed_qty"]


class MinibarCountSerializer(serializers.ModelSerializer):
    lines = MinibarCountLineSerializer(many=True)

    class Meta:
        model = MinibarCount
        fields = ["id","room_minibar","counted_on","counted_by","folio","posted_at","lines","created_at"]
        read_only_fields = ["posted_at"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        obj = MinibarCount.objects.create(**validated)
        for ln in lines:
            MinibarCountLine.objects.create(count=obj, **ln)
        return obj
