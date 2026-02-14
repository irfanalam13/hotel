from django.db import models


class AccountingExportJob(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="export_jobs")
    export_type = models.CharField(max_length=60)  # "daily_revenue", "folio_ledger", "tax_report"
    date_from = models.DateField()
    date_to = models.DateField()
    format = models.CharField(max_length=10, default="xlsx")  # xlsx/csv
    status = models.CharField(max_length=20, default="queued")
    file_path = models.CharField(max_length=500, blank=True)
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
