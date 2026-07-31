from rest_framework import serializers

from transactions.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id',
            'stripe_payment_intent_id',
            'amount',
            'currency',
            'status',
            'payment_method',
            'failure_reason',
            'ai_recommendation',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields