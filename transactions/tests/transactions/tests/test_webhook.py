from unittest.mock import patch, MagicMock

import pytest
from django.urls import reverse

from transactions.models import Transaction


def make_fake_event(event_type, payment_intent_id="pi_test_123", amount=2000,
                    currency="usd", failure_reason=None, event_id="evt_test_123"):
    payment_intent_data = {
        "id": payment_intent_id,
        "amount": amount,
        "currency": currency,
        "payment_method_types": ["card"],
        "last_payment_error": {"message": failure_reason} if failure_reason else None,
    }

    fake_object = MagicMock()
    fake_object.to_dict.return_value = payment_intent_data

    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": fake_object},
    }


@pytest.mark.django_db
class TestStripeWebhook:

    @patch("transactions.views.stripe.Webhook.construct_event")
    def test_successful_payment_creates_transaction(self, mock_construct_event, client):
        mock_construct_event.return_value = make_fake_event("payment_intent.succeeded", event_id="evt_success_1")

        response = client.post(
            reverse("stripe-webhook"),
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature"
        )

        assert response.status_code == 200
        assert Transaction.objects.filter(stripe_event_id="evt_success_1").exists()
        transaction = Transaction.objects.get(stripe_event_id="evt_success_1")
        assert transaction.status == Transaction.Status.SUCCESS
        assert transaction.amount == 20.00

    @patch("transactions.views.stripe.Webhook.construct_event")
    def test_duplicate_event_is_ignored(self, mock_construct_event, client):
        event = make_fake_event("payment_intent.succeeded", event_id="evt_success_1")
        mock_construct_event.return_value = event

        url = reverse("stripe-webhook")

        response1 = client.post(url, data="{}", content_type="application/json",
                                HTTP_STRIPE_SIGNATURE="fake_signature")
        response2 = client.post(url, data="{}", content_type="application/json",
                                HTTP_STRIPE_SIGNATURE="fake_signature")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert Transaction.objects.filter(stripe_event_id="evt_success_1").count() == 1

    def test_invalid_payload_returns_400(self, client):
        with patch("transactions.views.stripe.Webhook.construct_event") as mock_construct_event:
            mock_construct_event.side_effect = ValueError("Invalid payload")

        response = client.post(
            reverse("stripe-webhook"),
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature",
        )

        assert response.status_code == 400

    @patch("transactions.views.analyze_failed_transaction.delay")
    @patch("transactions.views.stripe.Webhook.construct_event")
    def test_failed_payment_triggers_ai_analysis(self, mock_construct_event, mock_delay, client):
        mock_construct_event.return_value = make_fake_event(
            "payment_intent.payment_failed",
            event_id="evt_failed_1",
            failure_reason="Your card was declined"
        )

        response = client.post(
            reverse("stripe-webhook"),
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature"
        )

        assert response.status_code == 200
        transaction = Transaction.objects.get(stripe_event_id="evt_failed_1")
        assert transaction.status == Transaction.Status.FAILED
        assert transaction.failure_reason == "Your card was declined"
        mock_delay.assert_called_once_with(str(transaction.id))
