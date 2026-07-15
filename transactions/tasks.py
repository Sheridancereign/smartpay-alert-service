import redis
from celery import shared_task
from django.conf import settings
from django.db import models
from django.utils import timezone

from .models import Transaction

redis_client = redis.from_url(settings.REDIS_URL)


@shared_task
def analyze_failed_transaction(transaction_id):
    print(f"Analyzing failed transaction: {transaction_id}")

    return f"Analyzed transaction: {transaction_id}"


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
    print(f"Generating daily report for {today}")
    return f"Report generated for {today}"