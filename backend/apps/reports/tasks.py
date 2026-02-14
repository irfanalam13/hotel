from datetime import date, timedelta
from django.utils.timezone import now
from celery import shared_task

from .models import ExportJob, ExportSchedule
from .services import build_report_payload, render_export


@shared_task
def run_export_job(job_id: str):
    job = ExportJob.objects.get(id=job_id)
    job.status = "running"
    job.started_at = now()
    job.save(update_fields=["status","started_at"])

    try:
        params = job.params or {}
        start = date.fromisoformat(params.get("start"))
        end = date.fromisoformat(params.get("end"))

        payload = build_report_payload(
            job.kind,
            tenant_id=job.tenant_id,
            property_id=job.property_id,
            start=start,
            end=end,
        )
        render_export(job, payload)

        job.status = "done"
        job.finished_at = now()
        job.save(update_fields=["status","finished_at","file"])
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.finished_at = now()
        job.save(update_fields=["status","error","finished_at"])


@shared_task
def run_schedules_tick():
    """
    Run every 10 minutes via Celery beat.
    Real-life: if server restarts, schedules still run safely.
    """
    t = now()
    schedules = ExportSchedule.objects.filter(is_active=True)

    for s in schedules:
        # simplistic cadence check
        if s.last_run_at and (t - s.last_run_at).total_seconds() < 60 * 30:
            continue

        if t.hour != s.hour_local or t.minute < s.minute_local or t.minute > s.minute_local + 9:
            continue

        # decide date range (yesterday for daily; last 7 days for weekly; last 30 for monthly)
        today = t.date()
        if s.cadence == "daily":
            start = today - timedelta(days=1)
            end = today
        elif s.cadence == "weekly":
            start = today - timedelta(days=7)
            end = today
        else:
            start = today - timedelta(days=30)
            end = today

        job = ExportJob.objects.create(
            tenant_id=s.tenant_id,
            property_id=s.property_id,
            kind=s.kind,
            fmt=s.fmt,
            params={**(s.params or {}), "start": str(start), "end": str(end)},
            created_by=s.created_by,
        )
        run_export_job.delay(str(job.id))
        s.last_run_at = t
        s.save(update_fields=["last_run_at"])
