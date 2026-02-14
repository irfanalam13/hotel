from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid

class MenuCategory(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_menu_categories")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("tenant", "name")]
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_menu_items")
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64, blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))  # percent
    is_active = models.BooleanField(default=True)

    # kitchen routing (real-life)
    kitchen_station = models.CharField(max_length=80, blank=True, default="")  # e.g. "GRILL", "BAR", "MAIN"
    is_alcohol = models.BooleanField(default=False)

    class Meta:
        unique_together = [("tenant", "category", "name")]
        ordering = ["category__sort_order", "name"]

    def __str__(self):
        return self.name

    @property
    def tax_amount_per_unit(self) -> Decimal:
        return (self.price * self.tax_rate / Decimal("100.00")).quantize(Decimal("0.01"))


class DiningTable(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_tables")
    name = models.CharField(max_length=60)  # "T1", "Table 5"
    area = models.CharField(max_length=60, blank=True, default="")  # "Rooftop", "Hall"
    seats = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("tenant", "name")]
        ordering = ["area", "name"]

    def __str__(self):
        return self.name


class CashDrawerShift(models.Model):
    """
    Real-life: each cashier opens a drawer shift with opening float.
    Orders/settlements link to this shift for audit & night audit.
    """
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_cash_shifts")
    branch = models.ForeignKey("properties.Branch", on_delete=models.PROTECT, related_name="pos_cash_shifts")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_shifts_opened")
    opened_at = models.DateTimeField(default=timezone.now)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="pos_shifts_closed")
    closed_at = models.DateTimeField(null=True, blank=True)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    is_closed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"POS Shift {self.id} ({self.branch})"

    def close(self, user, closing_cash: Decimal, notes: str = ""):
        if self.is_closed:
            return
        self.is_closed = True
        self.closed_by = user
        self.closed_at = timezone.now()
        self.closing_cash = closing_cash
        self.notes = notes
        self.save(update_fields=["is_closed", "closed_by", "closed_at", "closing_cash", "notes"])


class POSOrder(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        SENT_TO_KITCHEN = "sent", "Sent to kitchen"
        SERVED = "served", "Served"
        CLOSED = "closed", "Closed"
        VOIDED = "voided", "Voided"

    class Source(models.TextChoices):
        DINE_IN = "dine_in", "Dine in"
        TAKEAWAY = "takeaway", "Takeaway"
        ROOM_SERVICE = "room_service", "Room service"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_orders")
    branch = models.ForeignKey("properties.Branch", on_delete=models.PROTECT, related_name="pos_orders")
    table = models.ForeignKey(DiningTable, on_delete=models.PROTECT, null=True, blank=True, related_name="orders")

    source = models.CharField(max_length=20, choices=Source.choices, default=Source.DINE_IN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_orders_created")
    created_at = models.DateTimeField(default=timezone.now)

    waiter_name = models.CharField(max_length=80, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    # room posting link (optional)
    reservation = models.ForeignKey("reservations.Reservation", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_orders")
    folio = models.ForeignKey("billing.Folio", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_orders")

    # drawer shift
    cash_shift = models.ForeignKey(CashDrawerShift, on_delete=models.PROTECT, null=True, blank=True, related_name="orders")

    # totals (stored for speed / audit)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    external_ref = models.CharField(max_length=64, blank=True, default="")  # optional POS ref
    idempotency_key = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"POS Order {self.id}"

    def recompute_totals(self):
        items = list(self.items.all())
        subtotal = sum((i.line_subtotal for i in items), Decimal("0.00"))
        tax_total = sum((i.line_tax for i in items), Decimal("0.00"))
        total = (subtotal + tax_total).quantize(Decimal("0.01"))
        self.subtotal = subtotal.quantize(Decimal("0.01"))
        self.tax_total = tax_total.quantize(Decimal("0.01"))
        self.total = total
        self.save(update_fields=["subtotal", "tax_total", "total"])


class POSOrderItem(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_order_items")
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="order_items")

    qty = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    notes = models.CharField(max_length=200, blank=True, default="")  # e.g. "no onion"

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["id"]

    @property
    def line_subtotal(self) -> Decimal:
        return (self.qty * self.unit_price).quantize(Decimal("0.01"))

    @property
    def line_tax(self) -> Decimal:
        return (self.line_subtotal * self.tax_rate / Decimal("100.00")).quantize(Decimal("0.01"))


class KOTTicket(models.Model):
    """
    Kitchen Order Ticket (KOT) groups items; used for printing.
    """
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_kots")
    branch = models.ForeignKey("properties.Branch", on_delete=models.PROTECT, related_name="pos_kots")
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="kots")

    kot_no = models.CharField(max_length=30)  # unique per branch/day optionally
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_kots_created")

    station = models.CharField(max_length=80, blank=True, default="")  # optional station

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"KOT {self.kot_no} (Order {self.order_id})"


class KOTLine(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_kot_lines")
    kot = models.ForeignKey(KOTTicket, on_delete=models.CASCADE, related_name="lines")
    order_item = models.ForeignKey(POSOrderItem, on_delete=models.PROTECT, related_name="kot_lines")

    qty = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    note = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["id"]


class ApprovalRequest(models.Model):
    class Type(models.TextChoices):
        VOID_ORDER = "void_order", "Void order"
        REFUND = "refund", "Refund"
        DISCOUNT = "discount", "Discount"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_approvals")
    branch = models.ForeignKey("properties.Branch", on_delete=models.PROTECT, related_name="pos_approvals")

    request_type = models.CharField(max_length=30, choices=Type.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    order = models.ForeignKey(POSOrder, on_delete=models.PROTECT, null=True, blank=True, related_name="approvals")
    settlement = models.ForeignKey("pos.Settlement", on_delete=models.PROTECT, null=True, blank=True, related_name="approvals")

    reason = models.TextField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_approvals_requested")
    requested_at = models.DateTimeField(default=timezone.now)

    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="pos_approvals_decided")
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True, default="")

    idempotency_key = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-requested_at"]


class Settlement(models.Model):
    """
    Payment record for a POS order.
    For room-post, settlement can be "room" and amount=0 because charge goes to folio.
    """
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        QR = "qr", "QR"
        ROOM = "room", "Room posting"
        COMPLIMENTARY = "comp", "Complimentary"

    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        VOIDED = "voided", "Voided"
        REFUNDED = "refunded", "Refunded"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_settlements")
    branch = models.ForeignKey("properties.Branch", on_delete=models.PROTECT, related_name="pos_settlements")
    order = models.ForeignKey(POSOrder, on_delete=models.PROTECT, related_name="settlements")

    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reference = models.CharField(max_length=100, blank=True, default="")  # card/qr ref
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_settlements_received")
    received_at = models.DateTimeField(default=timezone.now)

    cash_shift = models.ForeignKey(CashDrawerShift, on_delete=models.PROTECT, null=True, blank=True, related_name="settlements")

    void_reason = models.TextField(blank=True, default="")
    idempotency_key = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-received_at"]


class RoomPost(models.Model):
    """
    Tracks the exact posting to Folio to prevent duplicate postings.
    """
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="pos_room_posts")
    branch = models.ForeignKey("properties.Branch", on_delete=models.PROTECT, related_name="pos_room_posts")
    order = models.OneToOneField(POSOrder, on_delete=models.PROTECT, related_name="room_post")
    folio = models.ForeignKey("billing.Folio", on_delete=models.PROTECT, related_name="room_posts")

    folio_item = models.ForeignKey("billing.FolioItem", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_room_posts")
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_room_posts_by")
    posted_at = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    idempotency_key = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["-posted_at"]
