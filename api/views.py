from django.conf import settings
from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
import redis
from drf_spectacular.utils import extend_schema, OpenApiParameter
from transactions.models import Transaction
from .serializers import TransactionSerializer



redis_client = redis.from_url(settings.REDIS_URL)


@extend_schema(
    summary="List transactions",
    description="Returns a paginated list of transactions, optionally filtered by status.",
    parameters=[
        OpenApiParameter(
            name='status',
            description='Filter by transaction status (success or failed)',
            required=False,
            type=str,
        ),
    ],
)
class TransactionListView(generics.ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

@extend_schema(
    summary="Retrieve a single transaction",
    description="Returns full details of a transaction by its internal UUID.",
)
class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()


@extend_schema(
    summary="Current hour metrics",
    description="Returns aggregated metrics (total amount, count) for the current hour, "
                "as cached by the Celery Beat periodic task.",
)
class HourlyMetricsView(APIView):
    def get(self, request):
        now = timezone.now()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        cache_key = f"metrics:hourly:{hour_start.strftime('%Y-%m-%d-%H')}"

        data = redis_client.hgetall(cache_key)

        if not data:
            return Response({
                'hour': hour_start.isoformat(),
                'total_amount': "0",
                'count': 0,
                'cached': False,
            })

        return Response({
            'hour': hour_start.isoformat(),
            'total_amount': data.get(b'total_amount', b'0').decode(),
            'count': int(data.get(b'count', b'0')),
            'cached': True,
        })








