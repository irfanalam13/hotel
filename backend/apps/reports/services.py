import json
from datetime import date
from django.core.files.base import ContentFile

from .models import ExportKind, ExportFormat, ExportJob
from . import selectors
from .exporters import to_excel_bytes, to_pdf_bytes


def build_report_payload(kind: str, *, tenant_id, property_id, start: date, end: date) -> dict:
    if kind == ExportKind.KPI:
        return selectors.kpi_summary(tenant_id=tenant_id, property_id=property_id, start=start, end=end)
    if kind == ExportKind.OCCUPANCY:
        return selectors.kpi_summary(tenant_id=tenant_id, property_id=property_id, start=start, end=end)
    if kind == ExportKind.REVENUE_DEPT:
        return {"rows": selectors.revenue_by_department(tenant_id=tenant_id, property_id=property_id, start=start, end=end)}
    if kind == ExportKind.CXL_NOSHOW:
        return selectors.cancellations_and_noshows(tenant_id=tenant_id, property_id=property_id, start=start, end=end)
    if kind == ExportKind.DISC_REFUND_AUDIT:
        return selectors.discount_refund_audit(tenant_id=tenant_id, property_id=property_id, start=start, end=end)
    if kind == ExportKind.STOCK_VARIANCE:
        return selectors.stock_variance(tenant_id=tenant_id, property_id=property_id, start=start, end=end)
    if kind == ExportKind.STAFF_ACTIVITY:
        return selectors.staff_activity(tenant_id=tenant_id, property_id=property_id, start=start, end=end)
    raise ValueError("Unknown export kind")


def render_export(job: ExportJob, payload: dict):
    kind = job.kind
    fmt = job.fmt

    if fmt == ExportFormat.EXCEL:
        # Flatten common cases to rows
        if "rows" in payload and isinstance(payload["rows"], list):
            rows = payload["rows"]
            cols = sorted({k for r in rows for k in r.keys()}) if rows else ["empty"]
        else:
            rows = [payload]
            cols = list(payload.keys())

        b = to_excel_bytes(sheet_name=kind, columns=cols, rows=rows)
        job.file.save(f"{kind}.xlsx", ContentFile(b), save=False)
        return

    if fmt == ExportFormat.PDF:
        lines = json.dumps(payload, indent=2).splitlines()
        b = to_pdf_bytes(title=f"Report: {kind}", lines=lines)
        job.file.save(f"{kind}.pdf", ContentFile(b), save=False)
        return

    raise ValueError("Unknown format")
