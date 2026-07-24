import pytest
import anthropic
from unittest.mock import patch

from transactions.models import Transaction
from transactions.tasks import analyze_failed_transaction


@pytest.mark.django_db
class TestAnalyzeFailedTransaction:

    def test_uses_fallback_when_anthropic_unavailable(self):
        transaction = Transaction.objects.create(
            stripe_event_id="evt_task_test_1",
            stripe_payment_intent_id="pi_task_test_1",
            amount=30.00,
            currency="usd",
            status=Transaction.Status.FAILED,
            failure_reason="Card declined",
        )

        with patch("transactions.tasks._generate_recommendation") as mock_generate:
            mock_generate.side_effect = anthropic.APIError(
                "no credit", request=None, body=None
            )

            result = analyze_failed_transaction(str(transaction.id))

        transaction.refresh_from_db()

        assert transaction.ai_recommendation is not None
        assert "declined" in transaction.ai_recommendation.lower() or "bank" in transaction.ai_recommendation.lower()
        assert result == transaction.ai_recommendation

    def test_returns_early_if_transaction_not_found(self):
        result = analyze_failed_transaction("00000000-0000-0000-0000-000000000000")
        assert "not found" in result


