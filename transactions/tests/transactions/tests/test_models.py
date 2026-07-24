import pytest
from transactions.models import Transaction

@pytest.mark.django_db
def test_transaction_creation():
    transaction = Transaction.objects.create(
        stripe_event_id="evt_test_1",
        stripe_payment_intent_id="pi_test_1",
        amount=100.5,
        currency="usd",
        status=Transaction.Status.SUCCESS,
    )
    assert transaction.id is not None
    assert transaction.status == Transaction.Status.SUCCESS
    assert str(transaction) == "pi_test_1 - success - 100.5 usd"


@pytest.mark.django_db
def test_transaction_event_id_is_unique():
    Transaction.objects.create(
        stripe_event_id="evt_test_dup",
        stripe_payment_intent_id="pi_test_1",
        amount=50,
        currency="usd",
        status=Transaction.Status.SUCCESS,
    )
    with pytest.raises(Exception):
        Transaction.objects.create(
            stripe_event_id="evt_test_dup",
            stripe_payment_intent_id="pi_test_2",
            amount=75,
            currency="usd",
            status=Transaction.Status.SUCCESS,
        )