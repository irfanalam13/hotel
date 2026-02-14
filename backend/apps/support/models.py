from django.db import models
from django.conf import settings


class SupportPlan(models.Model):
    code = models.CharField(max_length=50, unique=True)  # basic/pro/enterprise
    name = models.CharField(max_length=120)
    sla_first_response_minutes = models.IntegerField(default=240)  # 4 hours
    sla_resolution_minutes = models.IntegerField(default=2880)     # 48 hours
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SupportTicket(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="support_tickets")
    plan = models.ForeignKey(SupportPlan, on_delete=models.PROTECT, related_name="tickets")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tickets")

    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, default="normal")  # low/normal/high/urgent
    status = models.CharField(max_length=20, default="open")      # open/in_progress/waiting/closed

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="assigned_tickets")

    created_at = models.DateTimeField(auto_now_add=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.subject} ({self.status})"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
