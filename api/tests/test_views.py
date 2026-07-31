import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from transactions.models import Transaction


@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestTransactionListView:

    def test_list_returns_all_transactions(self, api_client):
        Transaction.objects.create(
            stripe_event_id="evt_api_1",
            stripe_payment_intent_id="pi_api_1",
            amount=10.00,
            currency="usd",
            status=Transaction.Status.SUCCESS,
        )
        Transaction.objects.create(
            stripe_event_id="evt_api_2",
            stripe_payment_intent_id="pi_api_2",
            amount=20.00,
            currency="usd",
            status=Transaction.Status.FAILED,
        )

        response = api_client.get(reverse('transaction-list'))

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_filter_by_status(self, api_client):
        Transaction.objects.create(
            stripe_event_id="evt_api_3",
            stripe_payment_intent_id="pi_api_3",
            amount=15.00,
            currency="usd",
            status=Transaction.Status.SUCCESS,
        )
        Transaction.objects.create(
            stripe_event_id="evt_api_4",
            stripe_payment_intent_id="pi_api_4",
            amount=25.00,
            currency="usd",
            status=Transaction.Status.FAILED,
        )

        response = api_client.get(reverse('transaction-list'), {'status': 'failed'})

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'failed'

    def test_read_only_ignores_post(self, api_client):
        response = api_client.post(reverse('transaction-list'), {
            'stripe_event_id': 'evt_hack',
            'amount': 999,
        })
        assert response.status_code == 405


@pytest.mark.django_db
class TestTransactionDetailView:

    def test_retrieve_single_transaction(self, api_client):
        transaction = Transaction.objects.create(
            stripe_event_id="evt_api_5",
            stripe_payment_intent_id="pi_api_5",
            amount=99.99,
            currency="usd",
            status=Transaction.Status.SUCCESS,
        )

        response = api_client.get(reverse('transaction-detail', args=[transaction.id]))

        assert response.status_code == 200
        assert response.data['stripe_payment_intent_id'] == "pi_api_5"

    def test_retrieve_nonexistent_returns_404(self, api_client):
        response = api_client.get(
            reverse('transaction-detail', args=["00000000-0000-0000-0000-000000000000"])
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestHourlyMetricsView:

    def test_returns_empty_metrics_when_no_cache(self, api_client):
        response = api_client.get(reverse('hourly-metrics'))

        assert response.status_code == 200
        assert 'total_amount' in response.data
        assert 'count' in response.data