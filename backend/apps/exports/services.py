import csv
import os
from django.utils import timezone
from django.conf import settings

from .models import AccountingExportJob


def build_export_file(job: AccountingExportJob) -> str:
    """
    Simple CSV export stub.
    Real-life: replace with openpyxl XLSX + charting + department mapping.
    """
    export_dir = getattr(settings, "EXPORT_DIR", os.path.join(settings.BASE_DIR, "var", "exports"))
    os.makedirs(export_dir, exist_ok=True)

    filename = f"{job.hotel_id}_{job.export_type}_{job.date_from}_{job.date_to}_{int(timezone.now().timestamp())}.csv"
    full_path = os.path.join(export_dir, filename)

    # Example: export folio charges (adjust to your billing models)
    # from apps.billing.models import FolioItem
    rows = [
        ["date", "type", "amount", "note"],
        [str(job.date_from), "stub", "0.00", "Replace with real accounting dataset"],
    ]

    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return full_path


def run_export_job(job_id: int) -> None:
    job = AccountingExportJob.objects.get(id=job_id)
    job.status = "running"
    job.save(update_fields=["status"])

    try:
        path = build_export_file(job)
        job.file_path = path
        job.status = "success"
        job.message = "Export generated."
    except Exception as e:
        job.status = "failed"
        job.message = str(e)
    job.save(update_fields=["status", "file_path", "message"])
