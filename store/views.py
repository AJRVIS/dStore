from django.shortcuts import render, get_object_or_404, redirect
from .models import Customer, Transaction, Product
from django.urls import reverse
from decimal import Decimal

import pandas as pd
from django.http import JsonResponse
from .forms import UploadFileForm  # (new file we’ll create)
from django.db import transaction as db_transaction

def home(request):
    customer = None
    transactions = []
    message = None

    if request.method == "POST":
        cust_id = request.POST.get("cust_id", "").strip()
        if cust_id:
            try:
                customer = Customer.objects.get(cust_id__iexact=cust_id)
                transactions = Transaction.objects.filter(
                    customer=customer
                ).order_by("-date")[:20]
            except Customer.DoesNotExist:
                message = f"Customer with ID {cust_id} not found"
        else:
            message = "Please enter a Customer ID"

    return render(request, "store/dashboard.html", {
        "customer": customer,
        "transactions": transactions,
        "message": message
    })


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

def upload_customers(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            df = pd.read_excel(file)

            with db_transaction.atomic():
                for _, row in df.iterrows():
                    Customer.objects.update_or_create(
                        cust_id=row["CustId"],
                        defaults={
                            "name": row["Name"],
                            "mobile": row.get("Mobile", ""),
                            "email": row.get("Email", ""),
                            "address": row.get("Address", ""),
                        }
                    )
            return redirect("customer_list")
    else:
        form = UploadFileForm()
    return render(request, "store/upload.html", {"form": form})

def ajax_search_customer(request):
    cust_id = request.GET.get("cust_id", "").strip()
    if cust_id:
        try:
            customer = Customer.objects.get(cust_id__iexact=cust_id)
            data = {
                "cust_id": customer.cust_id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
            }
            return JsonResponse({"found": True, "customer": data})
        except Customer.DoesNotExist:
            return JsonResponse({"found": False, "message": "Customer not found"})
    return JsonResponse({"found": False, "message": "No ID provided"})


def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "store/customers.html", {"customers": customers})
