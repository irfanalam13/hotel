from django.contrib import admin
from apps.auditlog.models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "hotel", "user", "method", "path", "status_code")
    list_filter = ("method", "status_code", "hotel")
    search_fields = ("path", "user__email", "hotel__hotel_code")
