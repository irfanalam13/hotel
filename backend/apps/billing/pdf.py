import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def build_invoice_pdf(invoice):
    folder = os.path.join(settings.MEDIA_ROOT, "invoices")
    os.makedirs(folder, exist_ok=True)

    filename = f"{invoice.hotel.id}_{invoice.number}.pdf"
    abs_path = os.path.join(folder, filename)

    c = canvas.Canvas(abs_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"INVOICE: {invoice.number}")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Hotel: {invoice.hotel}")
    y -= 15
    c.drawString(40, y, f"Issued At: {invoice.issued_at or ''}")
    y -= 25

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Charges")
    y -= 15

    c.setFont("Helvetica", 9)
    for item in invoice.folio.items.filter(is_void=False).order_by("posted_at")[:50]:
        line = f"{item.item_type.upper()} - {item.description} | {item.quantity} x {item.unit_price} = {item.line_base}"
        c.drawString(40, y, line[:110])
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50

    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, f"Subtotal: {invoice.subtotal} {invoice.currency}")
    y -= 14
    c.drawString(40, y, f"Tax: {invoice.tax_total} {invoice.currency}")
    y -= 14
    c.drawString(40, y, f"Total: {invoice.total} {invoice.currency}")

    c.showPage()
    c.save()

    # return relative path for FileField
    return f"invoices/{filename}"
