# store/ai_module/analytics.py
from store.models import Transaction, Product
from django.db.models import Sum
from django.utils import timezone

def get_sales_summary():
    today = timezone.now().date()
    total_sales_today = Transaction.objects.filter(date__date=today).aggregate(Sum("total_price"))["total_price__sum"] or 0
    top_product = (
        Product.objects.annotate(sold_qty=Sum("transaction__quantity"))
        .order_by("-sold_qty")
        .first()
    )
    return {
        "total_sales_today": total_sales_today,
        "top_product": top_product.name if top_product else "N/A",
    }
