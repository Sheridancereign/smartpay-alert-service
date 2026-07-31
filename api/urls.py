from django.urls import path
from .views import TransactionListView, TransactionDetailView, HourlyMetricsView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<uuid:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('metrics/hourly/', HourlyMetricsView.as_view(), name='hourly-metrics'),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
