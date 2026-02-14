from django.conf import settings
from django.db import models
from django.utils import timezone


# If you already have Tenant model in tenants app, reuse it.
# Here we assume you have: tenants.Tenant and your system already isolates by tenant in middleware.
class TenantAwareModel(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="%(class)s_items")

    class Meta:
        abstract = True


class AISettings(TenantAwareModel):
    """
    Per-tenant AI controls. Keep it strict by default.
    """
    provider = models.CharField(max_length=32, default="dummy")  # dummy|openai|custom_http
    model = models.CharField(max_length=64, blank=True, default="")

    enabled = models.BooleanField(default=False)

    # Safety controls
    redact_pii = models.BooleanField(default=True)
    allow_phrases = models.JSONField(default=list, blank=True)  # optional allowlist keywords
    block_phrases = models.JSONField(default=list, blank=True)  # optional blocklist keywords

    require_human_approval = models.BooleanField(default=True)
    max_tokens = models.PositiveIntegerField(default=600)

    # Anomaly thresholds (simple practical version)
    anomaly_zscore_threshold = models.FloatField(default=2.5)
    anomaly_min_events = models.PositiveIntegerField(default=8)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "provider")

    def __str__(self):
        return f"AISettings({self.tenant_id}, enabled={self.enabled}, provider={self.provider})"


class KnowledgeBaseFAQ(TenantAwareModel):
    """
    Reception policies / FAQs (the safest “AI” is retrieval + templates).
    """
    title = models.CharField(max_length=200)
    question = models.TextField()
    answer = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ReplyTemplate(TenantAwareModel):
    """
    Pre-approved message templates for reception.
    """
    code = models.CharField(max_length=50)  # e.g. LATE_CHECKOUT, EARLY_CHECKIN, REFUND_POLICY
    title = models.CharField(max_length=200)
    body = models.TextField()  # can contain {guest_name}, {date}, {policy_excerpt}
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.code} - {self.title}"


class AIRequest(TenantAwareModel):
    """
    Every AI call must be logged (audit + debugging + safety).
    """
    TYPE_REPLY = "reply_assistant"
    TYPE_COMPLAINT = "complaint_summarize"
    TYPE_REVIEW = "review_summarize"
    TYPE_ANOMALY = "anomaly_explain"

    REQUEST_TYPES = [
        (TYPE_REPLY, "Reply Assistant"),
        (TYPE_COMPLAINT, "Complaint Summarize"),
        (TYPE_REVIEW, "Review Summarize"),
        (TYPE_ANOMALY, "Anomaly Explain"),
    ]

    request_type = models.CharField(max_length=32, choices=REQUEST_TYPES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_requests"
    )

    input_text = models.TextField()
    redacted_input = models.TextField(blank=True, default="")

    # outputs
    output_text = models.TextField(blank=True, default="")
    confidence = models.FloatField(default=0.0)  # heuristic
    sources = models.JSONField(default=list, blank=True)  # FAQ/template codes used, etc.

    # approvals
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_approvals"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="completed",
        choices=[("completed", "Completed"), ("blocked", "Blocked"), ("pending", "Pending"), ("failed", "Failed")],
    )
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def approve(self, user):
        self.approved_by = user
        self.approved_at = timezone.now()
        self.status = "completed"
        self.save(update_fields=["approved_by", "approved_at", "status"])

    def __str__(self):
        return f"AIRequest({self.request_type}, {self.status}, {self.created_at:%Y-%m-%d})"


class Complaint(TenantAwareModel):
    """
    If you already have a complaints model elsewhere, you can replace this with FK to that table.
    """
    guest_name = models.CharField(max_length=120, blank=True, default="")
    guest_contact = models.CharField(max_length=120, blank=True, default="")
    channel = models.CharField(max_length=30, default="frontdesk")  # email/whatsapp/frontdesk/ota
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        default="open",
        choices=[("open", "Open"), ("in_progress", "In Progress"), ("resolved", "Resolved"), ("closed", "Closed")],
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Review(TenantAwareModel):
    """
    If you already store reviews, link to that. This is a minimal store.
    """
    source = models.CharField(max_length=50, default="google")  # google/booking/tripadvisor
    rating = models.FloatField(null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AIInsight(TenantAwareModel):
    """
    Stores summarizations / extracted themes for complaints/reviews.
    """
    TYPE_COMPLAINT = "complaint"
    TYPE_REVIEW = "review"

    insight_type = models.CharField(max_length=20, choices=[(TYPE_COMPLAINT, "Complaint"), (TYPE_REVIEW, "Review")])
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True, related_name="insights")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name="insights")

    summary = models.TextField()
    suggested_response = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)  # e.g. ["noise", "cleanliness"]
    risk_flags = models.JSONField(default=list, blank=True)  # e.g. ["legal_threat", "medical"]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AnomalyEvent(TenantAwareModel):
    """
    Stores unusual patterns found in billing controls (discount/refund/void).
    """
    event_type = models.CharField(max_length=30)  # discount|refund|void
    object_type = models.CharField(max_length=40, blank=True, default="")  # payment|folio|pos_order
    object_id = models.CharField(max_length=64, blank=True, default="")

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    score = models.FloatField(default=0.0)  # z-score or anomaly score
    message = models.TextField()

    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        default="open",
        choices=[("open", "Open"), ("ack", "Acknowledged"), ("closed", "Closed")],
    )
