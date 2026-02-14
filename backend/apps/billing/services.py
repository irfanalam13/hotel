from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import (
    Folio, FolioItem, Invoice, Payment,
    RefundRequest, CashierShift, NightAuditRun, DayLock
)
from .pdf import build_invoice_pdf


def assert_day_not_locked(hotel, business_date):
    if DayLock.objects.filter(hotel=hotel, business_date=business_date).exists():
        raise ValueError(f"Day is locked by night audit: {business_date}")


@transaction.atomic
def add_charge(*, folio: Folio, item_type: str, description: str, quantity, unit_price,
               tax_rate=Decimal("0.00"), is_tax_inclusive=False, posted_by=None):
    if folio.status != Folio.STATUS_OPEN:
        raise ValueError("Folio is not open.")
    # If you use business dates, check lock here (optional)
    # assert_day_not_locked(folio.hotel, timezone.localdate())

    item = FolioItem.objects.create(
        folio=folio,
        item_type=item_type,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        tax_rate=tax_rate,
        is_tax_inclusive=is_tax_inclusive,
        posted_by=posted_by,
        currency=folio.currency,
    )
    folio.recalc()
    return item


@transaction.atomic
def take_payment(*, folio: Folio, method: str, amount: Decimal, captured_by=None,
                 reference="", shift: CashierShift | None = None):
    if folio.status != Folio.STATUS_OPEN:
        raise ValueError("Folio not open.")
    folio.recalc()

    if amount <= 0:
        raise ValueError("Amount must be > 0.")
    if amount > folio.balance_due:
        # Real-life anti-mistake guard (unless you want to allow deposit/credit)
        raise ValueError("Payment exceeds balance due.")

    pay = Payment.objects.create(
        hotel=folio.hotel,
        folio=folio,
        method=method,
        amount=amount,
        reference=reference,
        captured_by=captured_by,
        shift=shift,
        currency=folio.currency,
        status=Payment.STATUS_CAPTURED,
    )
    folio.recalc()
    return pay


@transaction.atomic
def create_invoice(*, folio: Folio, number: str, issued_by=None):
    folio.recalc()
    inv = Invoice.objects.create(
        hotel=folio.hotel,
        folio=folio,
        number=number,
        status=Invoice.STATUS_DRAFT,
        subtotal=folio.subtotal,
        tax_total=folio.tax_total,
        total=folio.total,
        currency=folio.currency,
    )
    return inv


@transaction.atomic
def issue_invoice(*, invoice: Invoice, issued_by=None):
    if invoice.status != Invoice.STATUS_DRAFT:
        raise ValueError("Invoice is not draft.")
    invoice.folio.recalc()

    invoice.subtotal = invoice.folio.subtotal
    invoice.tax_total = invoice.folio.tax_total
    invoice.total = invoice.folio.total
    invoice.status = Invoice.STATUS_ISSUED
    invoice.issued_at = timezone.now()
    invoice.issued_by = issued_by
    invoice.save()

    # Build & attach PDF
    pdf_path = build_invoice_pdf(invoice)
    invoice.pdf_file.name = pdf_path
    invoice.save(update_fields=["pdf_file"])
    return invoice


@transaction.atomic
def request_refund(*, payment: Payment, amount: Decimal, reason: str, requested_by):
    if amount <= 0:
        raise ValueError("Refund must be > 0.")
    rr = RefundRequest.objects.create(
        hotel=payment.hotel,
        folio=payment.folio,
        payment=payment,
        amount=amount,
        reason=reason,
        requested_by=requested_by,
        currency=payment.currency,
    )
    return rr


@transaction.atomic
def approve_refund(*, refund: RefundRequest, decided_by, note=""):
    if refund.status != RefundRequest.STATUS_PENDING:
        raise ValueError("Refund is not pending.")
    refund.status = RefundRequest.STATUS_APPROVED
    refund.decided_by = decided_by
    refund.decided_at = timezone.now()
    refund.decision_note = note
    refund.save()

    # Create negative payment entry for accounting trail
    Payment.objects.create(
        hotel=refund.hotel,
        folio=refund.folio,
        method=refund.payment.method,
        amount=-refund.amount,
        reference=f"REFUND:{refund.payment.id}",
        captured_by=decided_by,
        currency=refund.currency,
        status=Payment.STATUS_CAPTURED,
        shift=refund.payment.shift,
    )
    refund.folio.recalc()
    return refund


@transaction.atomic
def reject_refund(*, refund: RefundRequest, decided_by, note=""):
    if refund.status != RefundRequest.STATUS_PENDING:
        raise ValueError("Refund is not pending.")
    refund.status = RefundRequest.STATUS_REJECTED
    refund.decided_by = decided_by
    refund.decided_at = timezone.now()
    refund.decision_note = note
    refund.save()
    return refund


@transaction.atomic
def open_shift(*, hotel, cashier, opening_float=Decimal("0.00")):
    if CashierShift.objects.filter(hotel=hotel, cashier=cashier, status=CashierShift.STATUS_OPEN).exists():
        raise ValueError("You already have an open shift.")
    return CashierShift.objects.create(
        hotel=hotel, cashier=cashier, opening_float=opening_float
    )


@transaction.atomic
def close_shift(*, shift: CashierShift, closing_note=""):
    if shift.status != CashierShift.STATUS_OPEN:
        raise ValueError("Shift is not open.")
    shift.status = CashierShift.STATUS_CLOSED
    shift.closed_at = timezone.now()
    shift.closing_note = closing_note
    shift.save()
    return shift


@transaction.atomic
def run_night_audit(*, hotel, business_date, ran_by=None):
    # prevent double-run
    audit, created = NightAuditRun.objects.select_for_update().get_or_create(
        hotel=hotel, business_date=business_date,
        defaults={"status": NightAuditRun.STATUS_RUNNING, "ran_by": ran_by}
    )
    if not created and audit.status == NightAuditRun.STATUS_DONE:
        raise ValueError("Night audit already completed for this date.")

    audit.status = NightAuditRun.STATUS_RUNNING
    audit.errors = []
    audit.save()

    try:
        # ✅ Example: compute money totals for that date
        # (If you track business_date on charges/payments, filter by it.)
        folios = Folio.objects.filter(hotel=hotel).exclude(status=Folio.STATUS_VOID)
        total_sales = sum((f.total for f in folios), start=Decimal("0.00"))
        total_due = sum((f.balance_due for f in folios), start=Decimal("0.00"))

        payments = Payment.objects.filter(hotel=hotel, status=Payment.STATUS_CAPTURED)
        total_paid = payments.aggregate(s=models.Sum("amount"))["s"] or Decimal("0.00")

        audit.totals = {
            "total_sales": str(total_sales),
            "total_paid": str(total_paid),
            "total_balance_due": str(total_due),
        }

        # ✅ LOCK the date (real-life safety)
        DayLock.objects.get_or_create(hotel=hotel, business_date=business_date, defaults={"locked_by": ran_by})

        audit.status = NightAuditRun.STATUS_DONE
        audit.finished_at = timezone.now()
        audit.save()
        return audit

    except Exception as e:
        audit.status = NightAuditRun.STATUS_FAILED
        audit.errors = audit.errors + [{"error": str(e)}]
        audit.finished_at = timezone.now()
        audit.save()
        raise
