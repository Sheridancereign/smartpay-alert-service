import pytest
from django.core import mail
from django.utils import timezone

from transactions.models import Transaction
from transactions.tasks import generate_daily_report
from transactions.reports import build_daily_report_pdf


@pytest.mark.django_db
class TestDailyReport:

    def test_pdf_generation_with_transactions(self):
        Transaction.objects.create(
            stripe_event_id="evt_report_1",
            stripe_payment_intent_id="pi_report_1",
            amount=100.00,
            currency="usd",
            status=Transaction.Status.SUCCESS,
        )
        Transaction.objects.create(
            stripe_event_id="evt_report_2",
            stripe_payment_intent_id="pi_report_2",
            amount=50.00,
            currency="usd",
            status=Transaction.Status.FAILED,
        )

        pdf_bytes = build_daily_report_pdf(timezone.now().date())

        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 0

    def test_pdf_generation_with_no_transactions(self):
        pdf_bytes = build_daily_report_pdf(timezone.now().date())
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_daily_report_sends_email_with_attachment(self):
        Transaction.objects.create(
            stripe_event_id="evt_report_email_1",
            stripe_payment_intent_id="pi_report_email_1",
            amount=75.00,
            currency="usd",
            status=Transaction.Status.SUCCESS,
        )

        generate_daily_report()

        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert "SmartPay Daily Report" in sent_email.subject
        assert len(sent_email.attachments) == 1

        filename, content, mimetype = sent_email.attachments[0]
        assert filename.endswith(".pdf")
        assert mimetype == "application/pdf"