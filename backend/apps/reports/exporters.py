import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def to_excel_bytes(sheet_name: str, columns: list[str], rows: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]

    ws.append(columns)
    for r in rows:
        ws.append([r.get(c, "") for c in columns])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def to_pdf_bytes(title: str, lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title)
    y -= 25

    c.setFont("Helvetica", 10)
    for line in lines:
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.drawString(40, y, line[:120])
        y -= 14

    c.showPage()
    c.save()
    return buf.getvalue()
