import anthropic
import redis
from celery import shared_task
from django.conf import settings
from django.db import models
from django.utils import timezone

from .models import Transaction

from django.core.mail import EmailMessage
from .reports import build_daily_report_pdf

redis_client = redis.from_url(settings.REDIS_URL)

FALLBACK_RECOMMENDATION = [
    ("Payment has been declined by bank. Recommended to check payment details and try again. "
     "If the issue persists, please contact our support team.")
]


def _generate_recommendation(transaction: Transaction) -> str:
    prompt = (
        f"The payment failed. The reason is the payment system: "
        f"\"{transaction.failure_reason or 'not specified'}\". "
        f"Amount: {transaction.amount} {transaction.currency}."
        f"Form a short (1-2 sentences) understandable recommendation for the client"
        f"about what to do next. Write simply, without technical jargon."
    )
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


@shared_task
def analyze_failed_transaction(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return f"Transaction {transaction_id} not found"

    try:
        recommendation = _generate_recommendation(transaction)
    except anthropic.AnthropicError as e:
        print(f"Anthropic API unavailable ({e}), using fallback recommendation")
        recommendation = FALLBACK_RECOMMENDATION[0]

    transaction.ai_recommendation = recommendation
    transaction.save(update_fields=['ai_recommendation'])

    print(f"AI recommendation for {transaction_id}: {recommendation}")
    return recommendation


@shared_task
def aggregate_hourly_metrics():
    now = timezone.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    total = Transaction.objects.filter(
        status=Transaction.Status.SUCCESS,
        created_at__gte=hour_start,

    ).aggregate(
        total_amount=models.Sum('amount'),
        count=models.Count('id')
    )

    cache_key = f"metrics:hourly:{hour_start.strftime('%Y-%m-%d-%H')}"
    redis_client.hset(cache_key, mapping={
        'total_amount': str(total['total_amount'] or 0),
        'count': total['count'] or 0,
    })
    redis_client.expire(cache_key, 3600 * 2)

    print(f"Aggregated metrics for {hour_start}: {total}")
    return total


@shared_task
def generate_daily_report():
    today = timezone.now().date()
    pdf_bytes = build_daily_report_pdf(today)

    email = EmailMessage(
        subject=f"SmartPay Daily Report — {today.isoformat()}",
        body=f"Please find attached the transactions report for {today.isoformat()}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.MANAGER_EMAIL],
    )
    email.attach(f"report_{today.isoformat()}.pdf", pdf_bytes, "application/pdf")
    email.send()

    print(f"Daily report generated and emailed for {today}")
    return f"Daily report generated and emailed for {today}"