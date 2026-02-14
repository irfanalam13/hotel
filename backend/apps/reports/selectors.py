from datetime import date
from django.db.models import Sum, Count, Q, F
from django.utils.timezone import now

# --- Adjust these imports to your actual apps/models ---
from apps.reservations.models import Reservation
from apps.billing.models import FolioItem, Payment
from apps.auditlog.models import AuditEvent
from apps.inventory.models import StockMove  # should include type + qty + cost + variance fields if available


def _daterange_filter(qs, field, start: date, end: date):
    # inclusive start, exclusive end
    return qs.filter(**{f"{field}__gte": start, f"{field}__lt": end})


def kpi_summary(*, tenant_id, property_id=None, start: date, end: date):
    """
    Owner KPI pack:
    - Occupancy %
    - ADR
    - RevPAR
    - Room revenue, total revenue
    """
    res_qs = Reservation.objects.filter(tenant_id=tenant_id)
    if property_id:
        res_qs = res_qs.filter(property_id=property_id)

    # Rooms sold = checked-in or checked-out nights in range (simplified)
    # If you have night audit room charges, use FolioItem(room_charge) as source of truth.
    checked_qs = res_qs.filter(status__in=["checked_in", "checked_out"])
    checked_qs = checked_qs.filter(checkin__lt=end, checkout__gt=start)

    rooms_sold = checked_qs.count()

    room_rev_qs = FolioItem.objects.filter(tenant_id=tenant_id, department="rooms")
    if property_id:
        room_rev_qs = room_rev_qs.filter(property_id=property_id)
    room_rev_qs = _daterange_filter(room_rev_qs, "posted_at", start, end)

    room_revenue = room_rev_qs.aggregate(v=Sum("amount"))["v"] or 0

    total_rev_qs = FolioItem.objects.filter(tenant_id=tenant_id)
    if property_id:
        total_rev_qs = total_rev_qs.filter(property_id=property_id)
    total_rev_qs = _daterange_filter(total_rev_qs, "posted_at", start, end)
    total_revenue = total_rev_qs.aggregate(v=Sum("amount"))["v"] or 0

    # available rooms in range: if you have a Room model, multiply by nights
    # fallback: assume "rooms_sold" denominator from configured property setting
    nights = max((end - start).days, 1)
    # If you store property.room_count setting, use it. Here we approximate from reservations’ room assignments.
    distinct_rooms = checked_qs.values("room_id").distinct().count() or 1
    available_room_nights = distinct_rooms * nights

    occupancy = float(rooms_sold) / float(available_room_nights) * 100.0

    adr = float(room_revenue) / float(max(rooms_sold, 1))
    revpar = float(room_revenue) / float(available_room_nights)

    return {
        "start": str(start),
        "end": str(end),
        "nights": nights,
        "rooms_sold": rooms_sold,
        "available_room_nights": available_room_nights,
        "occupancy_pct": round(occupancy, 2),
        "adr": round(adr, 2),
        "revpar": round(revpar, 2),
        "room_revenue": float(room_revenue),
        "total_revenue": float(total_revenue),
    }


def revenue_by_department(*, tenant_id, property_id=None, start: date, end: date):
    qs = FolioItem.objects.filter(tenant_id=tenant_id)
    if property_id:
        qs = qs.filter(property_id=property_id)
    qs = _daterange_filter(qs, "posted_at", start, end)

    rows = (
        qs.values("department")
        .annotate(revenue=Sum("amount"), items=Count("id"))
        .order_by("-revenue")
    )
    return list(rows)


def cancellations_and_noshows(*, tenant_id, property_id=None, start: date, end: date):
    qs = Reservation.objects.filter(tenant_id=tenant_id)
    if property_id:
        qs = qs.filter(property_id=property_id)
    qs = _daterange_filter(qs, "created_at", start, end)

    cxl = qs.filter(status="cancelled").count()
    no_show = qs.filter(status="no_show").count()
    total = qs.count()
    return {
        "total_created": total,
        "cancelled": cxl,
        "no_show": no_show,
        "cxl_rate_pct": round((cxl / max(total, 1)) * 100.0, 2),
        "no_show_rate_pct": round((no_show / max(total, 1)) * 100.0, 2),
    }


def discount_refund_audit(*, tenant_id, property_id=None, start: date, end: date):
    """
    Real-life leakage control:
    - Discounts: folio items with negative amounts or explicit discount type
    - Refunds: payments with type=refund or negative amount
    """
    discounts_qs = FolioItem.objects.filter(tenant_id=tenant_id)
    if property_id:
        discounts_qs = discounts_qs.filter(property_id=property_id)
    discounts_qs = _daterange_filter(discounts_qs, "posted_at", start, end)
    discounts_qs = discounts_qs.filter(Q(kind="discount") | Q(amount__lt=0))

    refunds_qs = Payment.objects.filter(tenant_id=tenant_id)
    if property_id:
        refunds_qs = refunds_qs.filter(property_id=property_id)
    refunds_qs = _daterange_filter(refunds_qs, "paid_at", start, end)
    refunds_qs = refunds_qs.filter(Q(kind="refund") | Q(amount__lt=0))

    return {
        "discounts_total": float(discounts_qs.aggregate(v=Sum("amount"))["v"] or 0),
        "discounts_count": discounts_qs.count(),
        "refunds_total": float(refunds_qs.aggregate(v=Sum("amount"))["v"] or 0),
        "refunds_count": refunds_qs.count(),
        "discounts": list(discounts_qs.values("id","folio_id","amount","kind","created_by_id","posted_at").order_by("-posted_at")[:200]),
        "refunds": list(refunds_qs.values("id","folio_id","amount","kind","created_by_id","paid_at").order_by("-paid_at")[:200]),
    }


def stock_variance(*, tenant_id, property_id=None, start: date, end: date):
    """
    Stock variance = expected vs actual adjustments (anti-theft/anti-leakage).
    Requires StockMove rows with move_type and qty, and optionally variance_value.
    """
    qs = StockMove.objects.filter(tenant_id=tenant_id)
    if property_id:
        qs = qs.filter(property_id=property_id)
    qs = _daterange_filter(qs, "created_at", start, end)

    adjustments = qs.filter(move_type__in=["adjustment_plus", "adjustment_minus"])
    variance_value = adjustments.aggregate(v=Sum("variance_value"))["v"] or 0

    return {
        "adjustments_count": adjustments.count(),
        "variance_value": float(variance_value),
        "top_variances": list(
            adjustments.values("id","sku_id","move_type","qty","variance_value","created_by_id","created_at")
            .order_by("-variance_value")[:200]
        ),
    }


def staff_activity(*, tenant_id, property_id=None, start: date, end: date):
    qs = AuditEvent.objects.filter(tenant_id=tenant_id)
    if property_id:
        qs = qs.filter(property_id=property_id)
    qs = _daterange_filter(qs, "created_at", start, end)

    by_user = (
        qs.values("actor_id")
        .annotate(events=Count("id"))
        .order_by("-events")
    )
    recent = list(qs.values("id","actor_id","action","object_type","object_id","created_at").order_by("-created_at")[:300])

    return {
        "by_user": list(by_user[:100]),
        "recent": recent,
    }
