from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import POSOrder, POSOrderItem, KOTTicket, KOTLine, Settlement, ApprovalRequest, RoomPost
import uuid

def _kot_no(branch_id: int) -> str:
    # Simple unique KOT number (real-life: could be per-day/per-branch counter)
    return f"KOT-{branch_id}-{uuid.uuid4().hex[:8].upper()}"

@transaction.atomic
def create_kot_for_order(*, order: POSOrder, user, station: str = "") -> KOTTicket:
    if order.status in [POSOrder.Status.CLOSED, POSOrder.Status.VOIDED]:
        raise ValidationError("Cannot create KOT for closed/voided order.")

    kot = KOTTicket.objects.create(
        tenant=order.tenant,
        branch=order.branch,
        order=order,
        kot_no=_kot_no(order.branch_id),
        created_by=user,
        station=station or "",
    )

    for item in order.items.select_related("menu_item").all():
        KOTLine.objects.create(
            tenant=order.tenant,
            kot=kot,
            order_item=item,
            qty=item.qty,
            note=item.notes or "",
        )

    order.status = POSOrder.Status.SENT_TO_KITCHEN
    order.save(update_fields=["status"])
    return kot

@transaction.atomic
def add_item_to_order(*, order: POSOrder, menu_item, qty: Decimal, note: str = "") -> POSOrderItem:
    if order.status not in [POSOrder.Status.OPEN, POSOrder.Status.SENT_TO_KITCHEN]:
        raise ValidationError("Cannot modify items unless order is open/sent.")

    oi = POSOrderItem.objects.create(
        tenant=order.tenant,
        order=order,
        menu_item=menu_item,
        qty=qty,
        unit_price=menu_item.price,
        tax_rate=menu_item.tax_rate,
        notes=note or "",
    )
    order.recompute_totals()
    return oi

@transaction.atomic
def room_post_order(*, order: POSOrder, folio, user, idempotency_key: str) -> RoomPost:
    """
    Charges POS order total to a guest folio (room posting).
    Prevents duplicates using RoomPost.idempotency_key
    """
    if not idempotency_key:
        raise ValidationError("idempotency_key is required")

    # Already posted?
    existing = RoomPost.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing

    if order.status == POSOrder.Status.VOIDED:
        raise ValidationError("Cannot room-post a voided order.")

    if order.total <= Decimal("0.00"):
        raise ValidationError("Order total must be > 0 to room-post.")

    # Link order -> folio
    order.folio = folio
    order.save(update_fields=["folio"])

    # Create folio item
    from apps.billing.models import FolioItem  # local import to avoid circular
    folio_item = FolioItem.objects.create(
        tenant=order.tenant,
        folio=folio,
        item_type="pos",
        description=f"Restaurant charges (POS Order #{order.id})",
        amount=order.total,
        quantity=Decimal("1.00"),
        metadata={"pos_order_id": str(order.id)},
    )

    rp = RoomPost.objects.create(
        tenant=order.tenant,
        branch=order.branch,
        order=order,
        folio=folio,
        folio_item=folio_item,
        posted_by=user,
        posted_at=timezone.now(),
        amount=order.total,
        idempotency_key=idempotency_key,
    )

    # Settlement entry as "ROOM"
    Settlement.objects.create(
        tenant=order.tenant,
        branch=order.branch,
        order=order,
        method=Settlement.Method.ROOM,
        amount=Decimal("0.00"),
        reference=f"FOLIO:{folio.id}",
        received_by=user,
        cash_shift=order.cash_shift,
        idempotency_key=f"room-settlement:{idempotency_key}",
    )

    order.status = POSOrder.Status.CLOSED
    order.save(update_fields=["status"])
    return rp

@transaction.atomic
def request_void_order(*, order: POSOrder, user, reason: str, idempotency_key: str) -> ApprovalRequest:
    if not idempotency_key:
        raise ValidationError("idempotency_key is required")
    existing = ApprovalRequest.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing

    if order.status == POSOrder.Status.VOIDED:
        raise ValidationError("Order already voided.")
    if order.status == POSOrder.Status.CLOSED:
        # closed orders should be refunded not voided (real-life)
        raise ValidationError("Closed orders require refund workflow.")

    return ApprovalRequest.objects.create(
        tenant=order.tenant,
        branch=order.branch,
        request_type=ApprovalRequest.Type.VOID_ORDER,
        order=order,
        reason=reason,
        requested_by=user,
        idempotency_key=idempotency_key,
    )

@transaction.atomic
def decide_approval(*, approval: ApprovalRequest, manager, approve: bool, note: str = "") -> ApprovalRequest:
    if approval.status != ApprovalRequest.Status.PENDING:
        return approval

    approval.decided_by = manager
    approval.decided_at = timezone.now()
    approval.decision_note = note or ""

    if approve:
        approval.status = ApprovalRequest.Status.APPROVED
        # Execute action
        if approval.request_type == ApprovalRequest.Type.VOID_ORDER and approval.order:
            order = approval.order
            order.status = POSOrder.Status.VOIDED
            order.save(update_fields=["status"])
    else:
        approval.status = ApprovalRequest.Status.REJECTED

    approval.save(update_fields=["decided_by", "decided_at", "decision_note", "status"])
    return approval
