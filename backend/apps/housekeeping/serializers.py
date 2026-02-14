from django.db import models
from django.utils import timezone


class HKTaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    READY_FOR_INSPECTION = "ready_for_inspection", "Ready for Inspection"
    FAILED = "failed", "Failed Inspection"
    COMPLETED = "completed", "Completed"


class HKTaskPriority(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class CleaningTask(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="hk_tasks")
    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE, related_name="hk_tasks")

    # optional link to checkout/stay
    stay_id = models.CharField(max_length=64, blank=True, default="")  # store as string to avoid hard FK issues

    status = models.CharField(max_length=32, choices=HKTaskStatus.choices, default=HKTaskStatus.PENDING)
    priority = models.CharField(max_length=16, choices=HKTaskPriority.choices, default=HKTaskPriority.NORMAL)

    assigned_to = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_hk_tasks")
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_hk_tasks")

    due_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "room"]),
        ]

    def __str__(self):
        return f"HK {self.room} - {self.status}"


class InspectionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"


class Inspection(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="hk_inspections")
    task = models.OneToOneField(CleaningTask, on_delete=models.CASCADE, related_name="inspection")

    status = models.CharField(max_length=16, choices=InspectionStatus.choices, default=InspectionStatus.PENDING)
    inspected_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="hk_inspections_done")
    inspected_at = models.DateTimeField(null=True, blank=True)

    score = models.PositiveSmallIntegerField(default=0)  # 0-100
    remarks = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Inspection({self.task_id}) {self.status}"
