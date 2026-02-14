from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class IntegrationProvider(models.TextChoices):
    # messaging
    TWILIO = "twilio", "Twilio"
    META_WA = "meta_whatsapp", "Meta WhatsApp"
    MOCK = "mock", "Mock (Dev)"

    # payment
    STRIPE = "stripe", "Stripe"
    PAYPAL = "paypal", "PayPal"
    NEPAL_LATER = "nepal_later", "Nepal Gateway (Later)"


class IntegrationKind(models.TextChoices):
    SMS = "sms", "SMS"
    WHATSAPP = "whatsapp", "WhatsApp"
    EMAIL = "email", "Email"
    PAYMENT = "payment", "Payment"


class IntegrationConfig(models.Model):
    """
    Tenant-scoped config. You should ensure tenant isolation via your middleware/base models.
    If you already use TenantForeignKey or tenant-aware base model, replace tenant_id accordingly.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    kind = models.CharField(max_length=20, choices=IntegrationKind.choices)
    provider = models.CharField(max_length=40, choices=IntegrationProvider.choices, default=IntegrationProvider.MOCK)

    is_enabled = models.BooleanField(default=False)

    # Store secrets in ENV if possible; here we store identifiers (not raw secrets) + optional JSON
    name = models.CharField(max_length=120, blank=True, default="")
    config = models.JSONField(default=dict, blank=True)  # e.g., sender_id, wa_phone_id, webhook secret, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant_id", "kind")]
        indexes = [
            models.Index(fields=["tenant_id", "kind"]),
        ]

    def __str__(self):
        return f"{self.tenant_id}::{self.kind}::{self.provider}"


class MessageTemplate(models.Model):
    """
    Template for WhatsApp/SMS/Email. Used for: booking confirmation, pre-arrival, payment link, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    kind = models.CharField(max_length=20, choices=IntegrationKind.choices)
    code = models.CharField(max_length=60)  # e.g. BOOKING_CONFIRM, CHECKIN_REMINDER
    title = models.CharField(max_length=120, blank=True, default="")

    # For Email
    subject = models.CharField(max_length=200, blank=True, default="")
    body = models.TextField()  # supports variables like {{guest_name}}, {{checkin}}, etc.

    # For WhatsApp template name (Meta approved template)
    wa_template_name = models.CharField(max_length=120, blank=True, default="")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant_id", "kind", "code")]
        indexes = [models.Index(fields=["tenant_id", "kind", "code"])]

    def __str__(self):
        return f"{self.kind}:{self.code}"


class OutboundMessage(models.Model):
    """
    Stores delivery logs and helps audits + retries.
    """
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        DELIVERED = "delivered", "Delivered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    kind = models.CharField(max_length=20, choices=IntegrationKind.choices)
    provider = models.CharField(max_length=40, choices=IntegrationProvider.choices, default=IntegrationProvider.MOCK)

    to = models.CharField(max_length=120)  # phone or email
    subject = models.CharField(max_length=200, blank=True, default="")
    body = models.TextField(blank=True, default="")

    metadata = models.JSONField(default=dict, blank=True)  # reservation_id, guest_id, etc.
    external_id = models.CharField(max_length=120, blank=True, default="")  # provider message id

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    error = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "kind", "status"]),
            models.Index(fields=["tenant_id", "created_at"]),
        ]


class PaymentIntent(models.Model):
    """
    Payment abstraction: create intent -> provide redirect/payment link -> confirm webhook later.
    Nepal gateways can be plugged later.
    """
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        REDIRECTED = "redirected", "Redirected"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    provider = models.CharField(max_length=40, choices=IntegrationProvider.choices, default=IntegrationProvider.MOCK)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="NPR")  # keep tenant setting later

    reference_type = models.CharField(max_length=40, default="reservation")  # reservation/folio/invoice
    reference_id = models.UUIDField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    payment_url = models.URLField(blank=True, default="")
    external_id = models.CharField(max_length=120, blank=True, default="")
    provider_payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "provider", "status"]),
            models.Index(fields=["tenant_id", "reference_type", "reference_id"]),
        ]
