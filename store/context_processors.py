from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, Settlement

def global_summary(request):
    today = timezone.now().date()
    last_10_days = today - timedelta(days=10)

    # --- Transactions ---
    total_transactions = Transaction.objects.aggregate(total=Sum("total_price"))["total"] or 0
    todays_transactions = Transaction.objects.filter(date__date=today).aggregate(total=Sum("total_price"))["total"] or 0
    last_10_days_transactions = Transaction.objects.filter(date__date__gte=last_10_days).aggregate(total=Sum("total_price"))["total"] or 0

    # --- Settlements ---
    total_settlements = Settlement.objects.aggregate(total=Sum("amount_paid"))["total"] or 0
    last_10_days_settlements = Settlement.objects.filter(date__date__gte=last_10_days).aggregate(total=Sum("amount_paid"))["total"] or 0

    # --- Net Dues ---
    global_total_due = total_transactions - total_settlements
    global_last_10_days_due = last_10_days_transactions - last_10_days_settlements
    global_todays_due = todays_transactions   # keep as-is (not reduced by settlements)
    global_total_due = max(0, global_total_due)

    return {
        "global_total_due": global_total_due,
        "global_todays_due": global_todays_due,
        "global_last_10_days_due": global_last_10_days_due,
    }
