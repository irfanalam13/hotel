from celery import shared_task
from django.utils import timezone
from django.db.models import Sum

from .models import AISettings, AnomalyEvent

# IMPORTANT:
# Replace these imports with your actual billing models:
# - Payment, FolioCharge, POSOrder, Refund, VoidLog, etc.
# This task is written so you only need to map "events" from your real tables.
from .services.anomaly import detect_anomalies


@shared_task
def run_anomaly_detection_for_tenant(tenant_id: int, hours: int = 24):
    from django.apps import apps

    Tenant = apps.get_model("tenants", "Tenant")
    tenant = Tenant.objects.filter(id=tenant_id).first()
    if not tenant:
        return {"ok": False, "error": "tenant not found"}

    settings_obj = AISettings.objects.filter(tenant=tenant).order_by("-updated_at").first()
    if not settings_obj or not settings_obj.enabled:
        return {"ok": True, "skipped": "ai disabled"}

    since = timezone.now() - timezone.timedelta(hours=hours)

    # TODO: Replace with REAL billing/pos data.
    # Example “fake adapter”: you will map your models to this list shape.
    events = []
    # events.append({
    #   "event_type": "discount",
    #   "staff_id": 12,
    #   "amount": 500.0,
    #   "object_type": "folio",
    #   "object_id": "123",
    #   "created_at": timezone.now(),
    # })

    anomalies = detect_anomalies(
        events,
        min_events=settings_obj.anomaly_min_events,
        threshold=settings_obj.anomaly_zscore_threshold,
    )

    created = 0
    for e, score, m, s in anomalies:
        AnomalyEvent.objects.create(
            tenant=tenant,
            event_type=e["event_type"],
            object_type=e.get("object_type", ""),
            object_id=str(e.get("object_id", "")),
            staff_id=e.get("staff_id"),
            score=float(score),
            message=f"Unusual {e['event_type']} amount {e.get('amount')} (z={score:.2f}, mean={m:.2f})",
            meta={"mean": m, "std": s, "amount": e.get("amount")},
        )
        created += 1

    return {"ok": True, "created": created}


@shared_task
def run_anomaly_detection_all_tenants(hours: int = 24):
    from django.apps import apps
    Tenant = apps.get_model("tenants", "Tenant")
    results = []
    for tid in Tenant.objects.values_list("id", flat=True):
        results.append(run_anomaly_detection_for_tenant.delay(tid, hours=hours).id)
    return {"queued": len(results)}
