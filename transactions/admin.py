from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('stripe_payment_intent_id', 'status', 'amount', 'currency', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('stripe_payment_intent_id', 'stripe_event_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'raw_payload')