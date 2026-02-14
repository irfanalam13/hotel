from django.db import models
from apps.common.models import TimeStampedModel
from apps.tenants.models import Hotel
from apps.accounts.models import User

class AuditEvent(TimeStampedModel):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    method = models.CharField(max_length=10)
    path = models.CharField(max_length=300)
    status_code = models.PositiveIntegerField(default=200)

    ip = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=300, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.method} {self.path} {self.status_code}"
