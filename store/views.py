import re
from django.shortcuts import render, get_object_or_404, redirect
from .models import Customer, Transaction, Product
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from django import forms

import pandas as pd
from django.http import JsonResponse
from .forms import UploadFileForm  # (new file we’ll create)
from django.db import transaction as db_transaction
from django.db.models import Sum

from store import models

def home(request):
    customer = None
    transactions = []
    total_due = 0
    message = None

    if request.method == "POST":
        cust_id = request.POST.get("cust_id", "").strip()
        if cust_id:
            try:
                customer = Customer.objects.get(cust_id__iexact=cust_id)
                

                if customer:
                    transactions = Transaction.objects.filter(customer=customer).order_by("-date")[:20]  # last 20
                    total_due = sum(t.total_price for t in customer.transactions.all())


            except Customer.DoesNotExist:
                message = f"Customer with ID {cust_id} not found"
        else:
            message = "Please enter a Customer ID"

    return render(request, "store/dashboard.html", {
        "customer": customer,
        "transactions": transactions,
        "total_due": total_due,  # pass grand total to template
        "message": message
    })
    
def search_customer(request):
    if request.method == "POST":
        cust_id = request.POST.get("cust_id", "").strip()

        # Validate format CUSTXXX
        if not re.match(r"^CUST[0-9]{3,}$", cust_id):
            return render(request, "store/search.html", {
                "message": "Invalid Customer ID format. Use CUSTXXX (e.g., CUST001)."
            })

        try:
            customer = Customer.objects.get(cust_id=cust_id)
        except Customer.DoesNotExist:
            return render(request, "store/search.html", {
                "message": f"Customer with ID {cust_id} not found."
            })

        transactions = Transaction.objects.filter(customer=customer).order_by("-date")

        total_bill = Transaction.objects.filter(customer=customer).aggregate(
            total=Sum('total_price')
        )['total'] or 0

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

def add_bill(request, cust_id):
    customer = get_object_or_404(Customer, cust_id=cust_id)

    if request.method == "POST":
        amount = request.POST.get("amount")

        if amount:  # ensure amount is provided
            # Pick a default product (or create a dummy one)
            default_product, _ = Product.objects.get_or_create(
                name="Miscellaneous", defaults={"price": 0}
            )

            Transaction.objects.create(
                customer=customer,
                product=default_product,
                quantity=1,
                total_price=Decimal(amount),
                date=timezone.now()
            )

    # Always redirect back to customer dashboard
    return redirect("customer_dashboard", cust_id=cust_id)


def customer_dashboard(request, cust_id):
    customer = get_object_or_404(Customer, cust_id=cust_id)
    transactions = customer.transactions.order_by("-date")[:10]  # last 10 transactions
    total_bill = customer.transactions.aggregate(total=Sum('total_price'))['total'] or 0

    return render(request, "store/dashboard.html", {
        "customer": customer,
        "transactions": transactions,
        "total_bill": total_bill
    })




def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "store/customers.html", {"customers": customers})


#Edit and Delete transaction, Add customer 

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["product", "quantity", "total_price"]

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['cust_id', 'name', 'mobile', 'email', 'address']
        widgets = {
            'cust_id': forms.TextInput(attrs={'placeholder': 'CUST001'}),
            'name': forms.TextInput(attrs={'placeholder': 'Customer Name'}),
            'mobile': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'address': forms.TextInput(attrs={'placeholder': 'Address'}),
        }


def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect("customer_dashboard", cust_id=transaction.customer.cust_id)
    else:
        form = TransactionForm(instance=transaction)
    return render(request, "store/edit_transaction.html", {"form": form, "transaction": transaction})


def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    cust_id = transaction.customer.cust_id
    if request.method == "POST":
        transaction.delete()
        return redirect("customer_dashboard", cust_id=cust_id)
    return render(request, "store/delete_transaction.html", {"transaction": transaction})


def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()  # Save and get the object
            return redirect("customer_dashboard", cust_id=customer.cust_id)
    else:
        form = CustomerForm()  # Create a blank form for GET requests

    return render(request, "store/add_customer.html", {"form": form})
