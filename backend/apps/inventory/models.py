from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


# 🔁 string-based relations (avoid circular imports)
TENANT_MODEL = "tenants.Tenant"
ROOM_MODEL = "properties.Room"
FOLIO_MODEL = "billing.Folio"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class InventoryLocation(TimeStampedModel):
    """
    Real-life: separate stores to reduce leakage (Main Store, Minibar Store, Kitchen Store)
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="inv_locations")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "code")]
        indexes = [models.Index(fields=["tenant", "code"])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Unit(TimeStampedModel):
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="units")
    name = models.CharField(max_length=60)      # e.g. Bottle, Pc, Kg
    symbol = models.CharField(max_length=16)    # e.g. bt, pc, kg

    class Meta:
        unique_together = [("tenant", "name")]
        indexes = [models.Index(fields=["tenant", "name"])]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class ItemCategory(TimeStampedModel):
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="item_categories")
    name = models.CharField(max_length=80)

    class Meta:
        unique_together = [("tenant", "name")]
        indexes = [models.Index(fields=["tenant", "name"])]

    def __str__(self):
        return self.name


class Item(TimeStampedModel):
    """
    Item master.
    leakage prevention:
    - reorder_level
    - cost tracking
    - minibar flag
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="items")
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=180)
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    # stock controls
    reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    expiry_tracking = models.BooleanField(default=False)

    # pricing
    default_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    minibar_sell_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    # used in minibar
    is_minibar_item = models.BooleanField(default=False)

    class Meta:
        unique_together = [("tenant", "sku")]
        indexes = [
            models.Index(fields=["tenant", "sku"]),
            models.Index(fields=["tenant", "name"]),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Supplier(TimeStampedModel):
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("tenant", "name")]
        indexes = [models.Index(fields=["tenant", "name"])]

    def __str__(self):
        return self.name


class PurchaseOrder(TimeStampedModel):
    STATUS_DRAFT = "draft"
    STATUS_SENT = "sent"
    STATUS_APPROVED = "approved"
    STATUS_CLOSED = "closed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SENT, "Sent"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="purchase_orders")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    po_number = models.CharField(max_length=50)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_pos")

    class Meta:
        unique_together = [("tenant", "po_number")]
        indexes = [models.Index(fields=["tenant", "po_number", "status"])]

    def __str__(self):
        return self.po_number


class PurchaseOrderLine(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    class Meta:
        indexes = [models.Index(fields=["po", "item"])]

    @property
    def line_total(self):
        return (self.qty_ordered or 0) * (self.unit_cost or 0)


class GRN(TimeStampedModel):
    """
    Goods Received Note
    Creates StockMovements (IN) and batches.
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="grns")
    po = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="grns")
    grn_number = models.CharField(max_length=50)
    received_date = models.DateField(default=timezone.now)
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_grns")

    class Meta:
        unique_together = [("tenant", "grn_number")]
        indexes = [models.Index(fields=["tenant", "grn_number"])]

    def __str__(self):
        return self.grn_number


class ItemBatch(TimeStampedModel):
    """
    Expiry control happens here (per GRN line).
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="batches")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)
    batch_code = models.CharField(max_length=80, blank=True, default="")
    expiry_date = models.DateField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "item", "location"]),
            models.Index(fields=["tenant", "expiry_date"]),
        ]

    def __str__(self):
        return f"{self.item.sku} batch:{self.batch_code or '-'}"

    def on_hand(self):
        val = self.stock_moves.aggregate(s=Sum("qty"))["s"]
        return val or Decimal("0")


class StockMovement(TimeStampedModel):
    """
    The source of truth for stock.
    qty positive = IN, qty negative = OUT/ISSUE/ADJUSTMENT.
    """
    TYPE_IN = "in"
    TYPE_OUT = "out"
    TYPE_ADJUST = "adjust"
    TYPE_TRANSFER = "transfer"

    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="stock_moves")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)
    batch = models.ForeignKey(ItemBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_moves")

    movement_type = models.CharField(max_length=16, choices=[
        (TYPE_IN, "IN"),
        (TYPE_OUT, "OUT"),
        (TYPE_ADJUST, "ADJUST"),
        (TYPE_TRANSFER, "TRANSFER"),
    ])

    qty = models.DecimalField(max_digits=12, decimal_places=3)  # +in, -out
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    reference = models.CharField(max_length=80, blank=True, default="")  # e.g. GRN-0001, ISSUE-0002
    note = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_stock_moves")

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "item", "location"]),
            models.Index(fields=["tenant", "movement_type"]),
            models.Index(fields=["tenant", "reference"]),
        ]


class StockIssue(TimeStampedModel):
    """
    Issue stock to departments (Kitchen/Housekeeping) — leakage killer:
    - requires approved_by
    - issues reduce stock (negative movements)
    """
    STATUS_DRAFT = "draft"
    STATUS_APPROVED = "approved"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="stock_issues")
    issue_number = models.CharField(max_length=50)
    from_location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name="issues_from")
    department = models.CharField(max_length=40, default="kitchen")  # kitchen/housekeeping/maintenance/other
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_issues")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_issues")
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("tenant", "issue_number")]
        indexes = [models.Index(fields=["tenant", "issue_number", "status"])]

    def __str__(self):
        return self.issue_number

    def approve_and_post(self, user):
        if self.status != self.STATUS_DRAFT:
            raise ValueError("Only draft issues can be approved.")
        self.status = self.STATUS_APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at"])

        # post stock movements
        for line in self.lines.all():
            # Negative qty = out
            StockMovement.objects.create(
                tenant=self.tenant,
                item=line.item,
                location=self.from_location,
                batch=line.batch,
                movement_type=StockMovement.TYPE_OUT,
                qty=-abs(line.qty),
                unit_cost=line.unit_cost,
                reference=self.issue_number,
                note=f"Issue to {self.department}",
                created_by=user,
            )


class StockIssueLine(models.Model):
    issue = models.ForeignKey(StockIssue, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(ItemBatch, on_delete=models.SET_NULL, null=True, blank=True)
    qty = models.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    class Meta:
        indexes = [models.Index(fields=["issue", "item"])]


class StockCount(TimeStampedModel):
    """
    Cycle count / variance check:
    - count lines store "counted_qty"
    - system_qty computed
    - approve → creates adjustment movements
    """
    STATUS_DRAFT = "draft"
    STATUS_POSTED = "posted"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_POSTED, "Posted"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="stock_counts")
    count_number = models.CharField(max_length=50)
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    counted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="counted_stockcounts")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_stockcounts")
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("tenant", "count_number")]
        indexes = [models.Index(fields=["tenant", "count_number", "status"])]

    def __str__(self):
        return self.count_number

    def post_adjustments(self, user):
        if self.status != self.STATUS_DRAFT:
            raise ValueError("Only draft counts can be posted.")
        with transaction.atomic():
            for line in self.lines.all():
                system_qty = line.system_qty()
                variance = (line.counted_qty or Decimal("0")) - system_qty
                if variance == 0:
                    continue
                StockMovement.objects.create(
                    tenant=self.tenant,
                    item=line.item,
                    location=self.location,
                    batch=line.batch,
                    movement_type=StockMovement.TYPE_ADJUST,
                    qty=variance,  # positive add, negative remove
                    unit_cost=line.unit_cost,
                    reference=self.count_number,
                    note=f"Stock count variance ({line.reason})",
                    created_by=user,
                )
            self.status = self.STATUS_POSTED
            self.approved_by = user
            self.approved_at = timezone.now()
            self.save(update_fields=["status", "approved_by", "approved_at"])


class StockCountLine(models.Model):
    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(ItemBatch, on_delete=models.SET_NULL, null=True, blank=True)
    counted_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    reason = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["count", "item"])]

    def system_qty(self):
        qs = StockMovement.objects.filter(
            tenant=self.count.tenant,
            item=self.item,
            location=self.count.location,
            batch=self.batch,
        ).aggregate(s=Sum("qty"))["s"]
        return qs or Decimal("0")


# ---------------------- MINIBAR ----------------------

class MinibarTemplate(TimeStampedModel):
    """
    Setup what SHOULD be in each room's minibar by default.
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="minibar_templates")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "name")]
        indexes = [models.Index(fields=["tenant", "name"])]

    def __str__(self):
        return self.name


class MinibarTemplateLine(models.Model):
    template = models.ForeignKey(MinibarTemplate, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, limit_choices_to={"is_minibar_item": True})
    par_level = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1"))  # expected qty

    class Meta:
        unique_together = [("template", "item")]
        indexes = [models.Index(fields=["template", "item"])]


class RoomMinibar(TimeStampedModel):
    """
    Connect a room to a template and a stock location (minibar store).
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="room_minibars")
    room = models.OneToOneField(ROOM_MODEL, on_delete=models.CASCADE, related_name="minibar")
    template = models.ForeignKey(MinibarTemplate, on_delete=models.PROTECT)
    stock_location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)  # where minibar stock comes from
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "is_active"])]

    def __str__(self):
        return f"Minibar - Room {self.room_id}"


class MinibarCount(TimeStampedModel):
    """
    Housekeeping does count.
    If consumed > 0, we:
      1) reduce stock from minibar location (OUT)
      2) auto-post charge to Folio (if provided)
    """
    tenant = models.ForeignKey(TENANT_MODEL, on_delete=models.CASCADE, related_name="minibar_counts")
    room_minibar = models.ForeignKey(RoomMinibar, on_delete=models.CASCADE, related_name="counts")
    counted_on = models.DateField(default=timezone.now)
    counted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="minibar_counts_done")

    # optional: link to folio (front desk)
    folio = models.ForeignKey(FOLIO_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "counted_on"]),
            models.Index(fields=["tenant", "posted_at"]),
        ]


class MinibarCountLine(models.Model):
    count = models.ForeignKey(MinibarCount, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    expected_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    actual_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    sell_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    class Meta:
        indexes = [models.Index(fields=["count", "item"])]

    @property
    def consumed_qty(self):
        diff = (self.expected_qty or 0) - (self.actual_qty or 0)
        return diff if diff > 0 else Decimal("0")
