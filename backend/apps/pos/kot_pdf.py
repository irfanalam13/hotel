from io import BytesIO
from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from django.http import HttpResponse

def kot_to_pdf_response(kot) -> HttpResponse:
    """
    Small ticket PDF (A6) printable.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A6)
    width, height = A6

    y = height - 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(10, y, f"KOT: {kot.kot_no}")
    y -= 14

    c.setFont("Helvetica", 9)
    c.drawString(10, y, f"Order: #{kot.order_id}  Table: {kot.order.table.name if kot.order.table else '-'}")
    y -= 12
    c.drawString(10, y, f"Station: {kot.station or '-'}")
    y -= 12
    c.drawString(10, y, f"Time: {kot.created_at.strftime('%Y-%m-%d %H:%M')}")
    y -= 14

    c.setFont("Helvetica-Bold", 9)
    c.drawString(10, y, "Items:")
    y -= 12
    c.setFont("Helvetica", 9)

    for line in kot.lines.select_related("order_item__menu_item").all():
        name = line.order_item.menu_item.name
        qty = str(line.qty)
        c.drawString(10, y, f"{qty} x {name}")
        y -= 11
        if line.note:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(14, y, f"• {line.note}")
            c.setFont("Helvetica", 9)
            y -= 11
        if y < 30:
            c.showPage()
            y = height - 20

    c.setFont("Helvetica", 8)
    c.drawString(10, 12, "— Kitchen Copy —")
    c.showPage()
    c.save()

    pdf = buf.getvalue()
    buf.close()

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="kot-{kot.kot_no}.pdf"'
    resp.write(pdf)
    return resp
