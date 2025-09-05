from django.shortcuts import render, get_object_or_404, redirect
from .models import Customer, Transaction, Product
from django.urls import reverse
from decimal import Decimal

def home(request):
    products = Product.objects.all()
    return render(request, "store/home.html", {"products": products})


def search_customer(request):
    if request.method == "POST":
        cust_id = request.POST.get("cust_id")
        customer = get_object_or_404(Customer, cust_id=cust_id)
        transactions = Transaction.objects.filter(customer=customer).order_by("-date")

        # Calculate total bill from transactions
        total_bill = sum(t.total_price for t in transactions)

        return render(request, "store/customer_detail.html", {
            "customer": customer,
            "transactions": transactions,
            "total_bill": total_bill
        })
    return render(request, "store/search.html")


def add_transaction(request, cust_id):
    customer = get_object_or_404(Customer, cust_id=cust_id)
    products = Product.objects.all()

    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity = int(request.POST.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)

        # Check stock
        if quantity > product.stock:
            return render(request, "store/add_transaction.html", {
                "customer": customer,
                "products": products,
                "error": f"Not enough stock for {product.name}. Only {product.stock} left."
            })

        total_price = product.price * Decimal(quantity)

        # Save transaction
        Transaction.objects.create(
            customer=customer,
            product=product,
            quantity=quantity,
            total_price=total_price
        )

        # Update stock
        product.stock -= quantity
        product.save()

        return redirect(reverse("search_customer"))

    return render(request, "store/add_transaction.html", {
        "customer": customer,
        "products": products
    })
