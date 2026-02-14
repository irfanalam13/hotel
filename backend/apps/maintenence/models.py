from django.db import models
from django.utils import timezone


class TicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    ASSIGNED = "assigned", "Assigned"
    IN_PROGRESS = "in_progress", "In Progress"
    ON_HOLD = "on_hold", "On Hold"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class TicketPriority(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class MaintenanceTicket(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="maintenance_tickets")
    room = models.ForeignKey("rooms.Room", on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_tickets")

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    priority = models.CharField(max_length=16, choices=TicketPriority.choices, default=TicketPriority.NORMAL)

    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets_created")
    assigned_to = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets_assigned")

    # SLA
    sla_minutes = models.PositiveIntegerField(default=240)  # 4 hours default
    due_at = models.DateTimeField(null=True, blank=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "due_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.due_at:
            self.due_at = timezone.now() + timezone.timedelta(minutes=self.sla_minutes)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False
        return bool(self.due_at and timezone.now() > self.due_at)
