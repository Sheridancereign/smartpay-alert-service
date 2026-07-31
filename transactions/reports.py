import io
from datetime import date

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from .models import Transaction



def build_daily_report_pdf(report_date: date) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Daily Transactions Report — {report_date.isoformat()}", styles['Title']))
    elements.append(Spacer(1, 0.5 * cm))

    transactions = Transaction.objects.filter(created_at__date=report_date).order_by('created_at')

    success_count = transactions.filter(status=Transaction.Status.SUCCESS).count()
    failed_count = transactions.filter(status=Transaction.Status.FAILED).count()
    total_success_amount = sum(
        t.amount for t in transactions.filter(status=Transaction.Status.SUCCESS)
    )

    summary = (
        f"Total transactions: {transactions.count()} | "
        f"Successful: {success_count} | Failed: {failed_count} | "
        f"Total successful amount: {total_success_amount}"
    )
    elements.append(Paragraph(summary, styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))

    table_data = [["Payment Intent ID", "Status", "Amount", "Currency", "Created At"]]
    for t in transactions:
        table_data.append([
            t.stripe_payment_intent_id,
            t.status,
            str(t.amount),
            t.currency,
            t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    if len(table_data) == 1:
        table_data.append(["—", "No transactions", "—", "—", "—"])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()