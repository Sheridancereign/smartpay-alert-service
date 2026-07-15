import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Transaction
from .tasks import analyze_failed_transaction
from django.db import IntegrityError

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] not in ['payment_intent.succeeded','payment_intent.payment_failed']:
        return HttpResponse(status=200)

    if Transaction.objects.filter(stripe_event_id=event['id']).exists():
        return HttpResponse(status=200)

    payment_intent = event['data']['object'].to_dict()

    status_map = {
        "payment_intent.succeeded": Transaction.Status.SUCCESS,
        "payment_intent.payment_failed": Transaction.Status.FAILED
    }

    try:
        transaction = Transaction.objects.create(
            stripe_event_id=event['id'],
            stripe_payment_intent_id=payment_intent['id'],
            amount=payment_intent['amount'] / 100,
            currency=payment_intent['currency'],
            status=status_map[event['type']],
            payment_method=payment_intent.get('payment_method_types', [None])[0],
            failure_reason=payment_intent.get('last_payment_error', {}).get('message') if payment_intent.get(
                'last_payment_error') else None,
            raw_payload=payment_intent,
        )
    except IntegrityError:
        return HttpResponse(status=200)


    if transaction.status == Transaction.Status.FAILED:
        analyze_failed_transaction.delay(str(transaction.id))

    return HttpResponse(status=200)
