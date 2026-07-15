from celery import shared_task


@shared_task
def analyze_failed_transaction(transaction_id):
    print(f"Analyzing failed transaction: {transaction_id}")

    return f"Analyzed transaction: {transaction_id}"