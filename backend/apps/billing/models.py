from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


# ✅ Adapt these imports to your project
# Month 1 tenants app should have Hotel (tenant)
# Month 2 reservations should have Reservation / Stay (checked-in/out states)
from apps.tenants.models import Hotel
from apps.reservations.models import Reservation  # adjust if your model name differs


class MoneyMixin(models.Model):
    currency = models.CharField(max_length=10, default="NPR")
    class Meta:
        abstract = True


class DayLock(models.Model):
    """Prevents edits after night audit close."""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="day_locks")
    business_date = models.DateField()
    locked_at = models.DateTimeField(auto_now_add=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = [("hotel", "business_date")]
        indexes = [models.Index(fields=["hotel", "business_date"])]

    def __str__(self):
        return f"{self.hotel} locked {self.business_date}"


class Folio(MoneyMixin):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_VOID = "void"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_VOID, "Void"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="folios")
    reservation = models.ForeignKey(
        Reservation, on_delete=models.PROTECT, related_name="folios"
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    notes = models.TextField(blank=True, default="")

    # computed snapshots
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["hotel", "status"]),
            models.Index(fields=["hotel", "created_at"]),
        ]

    def __str__(self):
        return f"Folio #{self.id} - {self.hotel}"

    def clean(self):
        if self.status == self.STATUS_CLOSED and self.balance_due != Decimal("0.00"):
            raise ValidationError("Cannot close folio with balance due.")

    def recalc(self):
        items = self.items.filter(is_void=False)
        subtotal = Decimal("0.00")
        tax_total = Decimal("0.00")

        for it in items:
            subtotal += it.line_subtotal
            tax_total += it.line_tax

        total = subtotal + tax_total
        paid = self.payments.filter(status=Payment.STATUS_CAPTURED).aggregate(
            s=models.Sum("amount")
        )["s"] or Decimal("0.00")

        self.subtotal = subtotal
        self.tax_total = tax_total
        self.total = total
        self.balance_due = total - paid
        self.save(update_fields=["subtotal", "tax_total", "total", "balance_due", "updated_at"])


class FolioItem(MoneyMixin):
    TYPE_ROOM = "room"
    TYPE_MINIBAR = "minibar"
    TYPE_EXTRA_BED = "extra_bed"
    TYPE_SERVICE = "service"
    TYPE_TAX = "tax"
    TYPE_OTHER = "other"

    TYPE_CHOICES = [
        (TYPE_ROOM, "Room charge"),
        (TYPE_MINIBAR, "Minibar"),
        (TYPE_EXTRA_BED, "Extra bed"),
        (TYPE_SERVICE, "Service"),
        (TYPE_TAX, "Tax"),
        (TYPE_OTHER, "Other"),
    ]

    folio = models.ForeignKey(Folio, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OTHER)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        help_text="Percent, e.g. 13.00 for VAT 13%"
    )
    is_tax_inclusive = models.BooleanField(default=False)

    is_void = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=255, blank=True, default="")

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["folio", "item_type"]),
            models.Index(fields=["posted_at"]),
        ]

    @property
    def line_base(self) -> Decimal:
        return (self.quantity or Decimal("0.00")) * (self.unit_price or Decimal("0.00"))

    @property
    def line_subtotal(self) -> Decimal:
        base = self.line_base
        if self.is_tax_inclusive and self.tax_rate > 0:
            # subtotal = base / (1 + r)
            r = self.tax_rate / Decimal("100.00")
            return (base / (Decimal("1.00") + r)).quantize(Decimal("0.01"))
        return base.quantize(Decimal("0.01"))

    @property
    def line_tax(self) -> Decimal:
        base = self.line_base
        if self.tax_rate <= 0:
            return Decimal("0.00")
        r = self.tax_rate / Decimal("100.00")
        if self.is_tax_inclusive:
            return (base - self.line_subtotal).quantize(Decimal("0.01"))
        return (self.line_subtotal * r).quantize(Decimal("0.01"))

    def clean(self):
        if self.folio.status != Folio.STATUS_OPEN:
            raise ValidationError("Cannot add/modify items on non-open folio.")
        if self.is_void and not self.void_reason:
            raise ValidationError("Void reason is required.")


class Invoice(MoneyMixin):
    STATUS_DRAFT = "draft"
    STATUS_ISSUED = "issued"
    STATUS_VOID = "void"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ISSUED, "Issued"),
        (STATUS_VOID, "Void"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="invoices")
    folio = models.OneToOneField(Folio, on_delete=models.PROTECT, related_name="invoice")

    number = models.CharField(max_length=50)  # unique per hotel
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    issued_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    pdf_file = models.FileField(upload_to="invoices/", null=True, blank=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("hotel", "number")]
        indexes = [models.Index(fields=["hotel", "created_at"])]

    def __str__(self):
        return f"Invoice {self.number}"


class Payment(MoneyMixin):
    METHOD_CASH = "cash"
    METHOD_CARD = "card"
    METHOD_BANK = "bank"
    METHOD_WALLET = "wallet"
    METHOD_CHOICES = [
        (METHOD_CASH, "Cash"),
        (METHOD_CARD, "Card"),
        (METHOD_BANK, "Bank"),
        (METHOD_WALLET, "Wallet"),
    ]

    STATUS_CAPTURED = "captured"
    STATUS_VOID = "void"
    STATUS_CHOICES = [
        (STATUS_CAPTURED, "Captured"),
        (STATUS_VOID, "Void"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="payments")
    folio = models.ForeignKey(Folio, on_delete=models.PROTECT, related_name="payments")

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CAPTURED)

    captured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    captured_at = models.DateTimeField(auto_now_add=True)

    # cashier shift link (optional)
    shift = models.ForeignKey(
        "CashierShift", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )

    class Meta:
        indexes = [
            models.Index(fields=["hotel", "captured_at"]),
            models.Index(fields=["folio", "captured_at"]),
        ]

    def clean(self):
        if self.amount == Decimal("0.00"):
            raise ValidationError("Amount cannot be zero.")
        if self.folio.status != Folio.STATUS_OPEN:
            raise ValidationError("Cannot take payment for non-open folio.")


class RefundRequest(MoneyMixin):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="refund_requests")
    folio = models.ForeignKey(Folio, on_delete=models.PROTECT, related_name="refund_requests")
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refund_requests")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="refunds_requested"
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds_decided"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["hotel", "status"])]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Refund amount must be > 0.")
        if self.amount > self.payment.amount:
            raise ValidationError("Refund amount cannot exceed original payment amount.")


class CashierShift(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [(STATUS_OPEN, "Open"), (STATUS_CLOSED, "Closed")]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="cashier_shifts")
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    closing_note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["hotel", "status", "opened_at"])]

    def __str__(self):
        return f"Shift {self.id} {self.cashier} ({self.status})"


class NightAuditRun(models.Model):
    STATUS_RUNNING = "running"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "Running"),
        (STATUS_DONE, "Done"),
        (STATUS_FAILED, "Failed"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="night_audits")
    business_date = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_RUNNING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    totals = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=list, blank=True)

    ran_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = [("hotel", "business_date")]
        indexes = [models.Index(fields=["hotel", "business_date"])]

    def __str__(self):
        return f"NightAudit {self.hotel} {self.business_date}"
