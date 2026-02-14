import uuid
from django.conf import settings
from django.db import models

class ExportFormat(models.TextChoices):
    EXCEL = "excel", "Excel"
    PDF = "pdf", "PDF"

class ExportKind(models.TextChoices):
    KPI = "kpi", "KPI Summary"
    OCCUPANCY = "occupancy", "Occupancy / ADR / RevPAR"
    REVENUE_DEPT = "revenue_dept", "Revenue by Department"
    CXL_NOSHOW = "cxl_noshow", "Cancellation / No-show"
    DISC_REFUND_AUDIT = "disc_refund_audit", "Discount / Refund Audit"
    STOCK_VARIANCE = "stock_variance", "Stock Variance"
    STAFF_ACTIVITY = "staff_activity", "Staff Activity Logs"

class ExportJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant_id = models.UUIDField(db_index=True)
    property_id = models.UUIDField(null=True, blank=True, db_index=True)

    kind = models.CharField(max_length=50, choices=ExportKind.choices)
    fmt = models.CharField(max_length=20, choices=ExportFormat.choices)

    params = models.JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="report_exports")
    created_at = models.DateTimeField(auto_now_add=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="queued",
        choices=(("queued","queued"),("running","running"),("done","done"),("failed","failed")),
    )
    error = models.TextField(blank=True, default="")

    # store in media/reports/...
    file = models.FileField(upload_to="reports/exports/%Y/%m/", null=True, blank=True)

    def __str__(self):
        return f"{self.kind} {self.fmt} {self.status}"

class ExportSchedule(models.Model):
    """
    Scheduled exports for owners (daily/weekly/monthly). Celery beat triggers tasks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant_id = models.UUIDField(db_index=True)
    property_id = models.UUIDField(null=True, blank=True, db_index=True)

    name = models.CharField(max_length=120)

    kind = models.CharField(max_length=50, choices=ExportKind.choices)
    fmt = models.CharField(max_length=20, choices=ExportFormat.choices)

    # Simple schedule config (no heavy dependencies)
    cadence = models.CharField(
        max_length=20,
        choices=(("daily","daily"),("weekly","weekly"),("monthly","monthly")),
        default="daily",
    )
    hour_local = models.PositiveSmallIntegerField(default=6)  # owner wants morning
    minute_local = models.PositiveSmallIntegerField(default=0)

    params = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="report_schedules")
    created_at = models.DateTimeField(auto_now_add=True)

    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.cadence})"
