from django.utils import timezone
from .models import ChannelSyncJob, ChannelSyncLog


def run_sync_job(job_id: int) -> None:
    """
    Framework: later you plug provider clients here.
    """
    job = ChannelSyncJob.objects.select_related("provider").get(id=job_id)
    job.status = "running"
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    try:
        # TODO: call provider adapter:
        # adapter = get_adapter(job.provider.code)
        # adapter.run(job)
        ChannelSyncLog.objects.create(job=job, level="info", event="sync_started", payload={"job_type": job.job_type})
        ChannelSyncLog.objects.create(job=job, level="info", event="sync_stub", payload={"note": "Connect provider SDK here"})
        job.status = "success"
        job.message = "Completed (stub)."
    except Exception as e:
        job.status = "failed"
        job.message = str(e)
        ChannelSyncLog.objects.create(job=job, level="error", event="sync_failed", payload={"error": str(e)})
    finally:
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "message", "finished_at"])
