from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.apps import apps
from django.db.models import Sum

from .models import StockMovement, ItemBatch, MinibarCount


def get_on_hand(tenant_id, item_id, location_id, batch_id=None):
    qs = StockMovement.objects.filter(
        tenant_id=tenant_id,
        item_id=item_id,
        location_id=location_id,
        batch_id=batch_id,
    ).aggregate(s=Sum("qty"))["s"]
    return qs or Decimal("0")


@transaction.atomic
def receive_grn_to_stock(grn, lines, user):
    """
    lines: list of dicts:
      { item, qty_received, unit_cost, batch_code?, expiry_date? }
    Creates/gets batch per item+location+batch_code+expiry and makes StockMovement IN.
    """
    for ln in lines:
        item = ln["item"]
        qty = ln["qty_received"]
        unit_cost = ln.get("unit_cost") or item.default_cost

        batch_code = ln.get("batch_code", "")
        expiry_date = ln.get("expiry_date")

        batch = None
        if item.expiry_tracking or expiry_date or batch_code:
            batch = ItemBatch.objects.create(
                tenant=grn.tenant,
                item=item,
                location=grn.location,
                batch_code=batch_code or "",
                expiry_date=expiry_date,
                unit_cost=unit_cost,
            )

        StockMovement.objects.create(
            tenant=grn.tenant,
            item=item,
            location=grn.location,
            batch=batch,
            movement_type=StockMovement.TYPE_IN,
            qty=qty,
            unit_cost=unit_cost,
            reference=grn.grn_number,
            note="GRN receipt",
            created_by=user,
        )


@transaction.atomic
def post_minibar_consumption(minibar_count: MinibarCount, user):
    """
    For each consumed line:
      - stock OUT from minibar stock location
      - create FolioItem in billing (if available)
    """
    if minibar_count.posted_at:
        return  # idempotent

    room_minibar = minibar_count.room_minibar
    location = room_minibar.stock_location

    # Optional billing models
    FolioItem = apps.get_model("billing", "FolioItem")
    has_folioitem = FolioItem is not None

    for ln in minibar_count.lines.select_related("item").all():
        consumed = ln.consumed_qty
        if consumed <= 0:
            continue

        # stock OUT (no batch enforced here; you can extend FIFO batch picking later)
        StockMovement.objects.create(
            tenant=minibar_count.tenant,
            item=ln.item,
            location=location,
            movement_type=StockMovement.TYPE_OUT,
            qty=-abs(consumed),
            unit_cost=ln.item.default_cost,
            reference=f"MINIBAR-{minibar_count.id}",
            note=f"Minibar consumption room:{room_minibar.room_id}",
            created_by=user,
        )

        # post to folio (if linked)
        if minibar_count.folio_id and has_folioitem:
            FolioItem.objects.create(
                tenant_id=minibar_count.tenant_id,
                folio_id=minibar_count.folio_id,
                kind="minibar",
                description=f"Minibar: {ln.item.name} x {consumed}",
                quantity=consumed,
                unit_price=ln.sell_price or ln.item.minibar_sell_price,
                amount=(ln.sell_price or ln.item.minibar_sell_price) * consumed,
                metadata={"item_id": str(ln.item_id), "minibar_count_id": str(minibar_count.id)},
            )

    minibar_count.posted_at = timezone.now()
    minibar_count.save(update_fields=["posted_at"])
