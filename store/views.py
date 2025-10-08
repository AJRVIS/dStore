from datetime import timedelta
from pyexpat.errors import messages
import re
from django.shortcuts import render, get_object_or_404, redirect
from .models import Customer, Settlement, Transaction, Product
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from django import forms

import pandas as pd
from django.http import JsonResponse
from .forms import SettlementForm, UploadFileForm
from django.db import transaction as db_transaction
from django.db.models import Sum

from store import models

def home(request):
    customer = None
    transactions = []
    total_due = 0
    message = None

    today = timezone.now().date()
    last_10_days = today - timedelta(days=10)

    # Global totals
    global_total_due = Transaction.objects.aggregate(Sum("total_price"))["total_price__sum"] or 0
    global_todays_due = Transaction.objects.filter(date__date=today).aggregate(Sum("total_price"))["total_price__sum"] or 0
    global_last_10_days_due = Transaction.objects.filter(date__date__gte=last_10_days).aggregate(Sum("total_price"))["total_price__sum"] or 0

    if request.method == "POST":
        dnumber = request.POST.get("dnumber", "").strip()
        if not dnumber:
            message = "Please enter a DNumber"
        else:
            try:
                customer = Customer.objects.get(dnumber=dnumber)

                # --- combine transactions and settlements into a single list ---
                tx_qs = Transaction.objects.filter(customer=customer)
                st_qs = Settlement.objects.filter(customer=customer)

                entries = []
                for t in tx_qs:
                    entries.append({
                        "type": "transaction",
                        "date": t.date,
                        "product_name": t.product.name,
                        "quantity": t.quantity,
                        "total_price": t.total_price,
                        "is_settled": t.is_settled,
                        "obj": t,
                    })
                for s in st_qs:
                    entries.append({
                        "type": "settlement",
                        "date": s.date,
                        "amount_paid": s.amount_paid,
                        "mode": s.mode,
                        "obj": s,
                    })

                # sort by date desc and limit to last 20
                entries.sort(key=lambda e: e["date"], reverse=True)
                transactions = entries[:20]

                total_settlements = sum(s.amount_paid for s in st_qs)
                total_due = sum(t.total_price for t in tx_qs) - total_settlements
                total_due = max(0, total_due)  # prevent negative dues

            except Customer.DoesNotExist:
                message = f"Customer with DNumber '{dnumber}' not found."

    return render(request, "store/dashboard.html", {
        "customer": customer,
        "transactions": transactions,
        "total_bill": total_due,
        "has_due": bool(total_due),
        "message": message,
        "global_total_due": global_total_due,
        "global_todays_due": global_todays_due,
        "global_last_10_days_due": global_last_10_days_due,
    })


def search_customer(request):
    if request.method == "POST":
        dnumber = request.POST.get("dnumber", "").strip()

        try:
            customer = Customer.objects.get(dnumber=dnumber)
        except Customer.DoesNotExist:
            return render(request, "store/search.html", {
                "message": f"Customer with DNumber {dnumber} not found."
            })

        transactions = Transaction.objects.filter(customer=customer).order_by("-date")
        total_settlements = sum(s.amount_paid for s in customer.settlements.all())
        total_due = sum(t.total_price for t in customer.transactions.all()) - total_settlements

        total_bill = Transaction.objects.filter(customer=customer).aggregate(
            total=Sum('total_price')
        )['total'] or 0

        return render(request, "store/customer_detail.html", {
            "customer": customer,
            "transactions": transactions,
            "total_bill": total_due
        })

    return render(request, "store/search.html")


def add_transaction(request, dnumber):
    customer = get_object_or_404(Customer, dnumber=dnumber)
    products = Product.objects.all()

    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        if quantity > product.stock:
            return render(request, "store/add_transaction.html", {
                "customer": customer,
                "products": products,
                "error": f"Not enough stock for {product.name}. Only {product.stock} left."
            })

        total_price = product.price * Decimal(quantity)
        Transaction.objects.create(customer=customer, product=product, quantity=quantity, total_price=total_price)

        product.stock -= quantity
        product.save()

        return redirect(reverse("search_customer"))

    return render(request, "store/add_transaction.html", {"customer": customer, "products": products})

# store/views.py

def upload_customers(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        try:
            xls = pd.ExcelFile(file)
            added, skipped = 0, 0

            for sheet in xls.sheet_names:
                df = pd.read_excel(file, sheet_name=sheet)

                # Normalize column names (strip spaces, uppercase)
                df.columns = [col.strip().upper() for col in df.columns]

                if "NAME" not in df.columns or "D/NUMBER" not in df.columns:
                    messages.error(request, f"❌ Missing NAME or D/NUMBER column in {sheet}")
                    continue

                for _, row in df.iterrows():
                    name = str(row["NAME"]).strip() if pd.notna(row["NAME"]) else None
                    dnumber = str(row["D/NUMBER"]).strip() if pd.notna(row["D/NUMBER"]) else None

                    if name and dnumber:
                        # Ensure consistent string (avoid int/float issues)
                        dnumber = dnumber.replace(".0", "")  # remove .0 from Excel numbers
                        _, created = Customer.objects.get_or_create(
                            dnumber=dnumber,
                            defaults={"name": name}
                        )
                        if created:
                            added += 1
                        else:
                            skipped += 1

            messages.success(request, f"✅ Upload complete. Added {added}, skipped {skipped} (already exist).")
            return redirect("customer_list")

        except Exception as e:
            messages.error(request, f"⚠️ Error while processing file: {e}")

    return render(request, "store/upload.html")



def ajax_search_customer(request):
    dnumber = request.GET.get("dnumber", "").strip()
    if dnumber:
        try:
            customer = Customer.objects.get(dnumber=dnumber)
            data = {
                "dnumber": customer.dnumber,
                "name": customer.name,
            }
            return JsonResponse({"found": True, "customer": data})
        except Customer.DoesNotExist:
            return JsonResponse({"found": False, "message": "Customer not found"})
    return JsonResponse({"found": False, "message": "No DNumber provided"})


def add_bill(request, dnumber):
    customer = get_object_or_404(Customer, dnumber=dnumber)

    if request.method == "POST":
        amount = request.POST.get("amount")
        if amount:
            default_product, _ = Product.objects.get_or_create(name="Miscellaneous", defaults={"price": 0})
            Transaction.objects.create(customer=customer, product=default_product, quantity=1, total_price=Decimal(amount), date=timezone.now())

    return redirect("customer_dashboard", dnumber=dnumber)

def customer_dashboard(request, dnumber):
    customer = get_object_or_404(Customer, dnumber=dnumber)

    tx_qs = Transaction.objects.filter(customer=customer)
    st_qs = Settlement.objects.filter(customer=customer)

    entries = []
    for t in tx_qs:
        entries.append({
            "type": "transaction",
            "date": t.date,
            "product_name": t.product.name,
            "quantity": t.quantity,
            "total_price": t.total_price,
            "is_settled": t.is_settled,
            "obj": t,
        })
    for s in st_qs:
        entries.append({
            "type": "settlement",
            "date": s.date,
            "amount_paid": s.amount_paid,
            "mode": s.mode,
            "obj": s,
        })

    entries.sort(key=lambda e: e["date"], reverse=True)
    transactions = entries[:20]

    total_bill = tx_qs.aggregate(total=Sum('total_price'))['total'] or 0
    total_settlements = sum(s.amount_paid for s in st_qs)
    total_due = total_bill - total_settlements
    total_due = max(0, total_due)

    return render(request, "store/dashboard.html", {
        "customer": customer,
        "transactions": transactions,
        "total_bill": total_due,
        "has_due": bool(total_due),
    })



def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "store/customers.html", {"customers": customers})


# Forms
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["product", "quantity", "total_price"]


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['dnumber', 'name']
        widgets = {
            'dnumber': forms.NumberInput(attrs={'placeholder': 'Enter DNumber'}),
            'name': forms.TextInput(attrs={'placeholder': 'Customer Name'}),
        }


def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect("customer_dashboard", dnumber=transaction.customer.dnumber)
    else:
        form = TransactionForm(instance=transaction)
    return render(request, "store/edit_transaction.html", {"form": form, "transaction": transaction})


def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    dnumber = transaction.customer.dnumber
    if request.method == "POST":
        transaction.delete()
        return redirect("customer_dashboard", dnumber=dnumber)
    return render(request, "store/delete_transaction.html", {"transaction": transaction})


def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            return redirect("customer_dashboard", dnumber=customer.dnumber)
    else:
        form = CustomerForm()

    return render(request, "store/add_customer.html", {"form": form})


def settlement(request, dnumber):
    customer = get_object_or_404(Customer, dnumber=dnumber)

    # Calculate total due before payment
    total_due = sum(t.total_price for t in customer.transactions.all())
    total_paid = sum(s.amount_paid for s in customer.settlements.all())
    outstanding_due = total_due - total_paid

    if request.method == "POST":
        amount = float(request.POST.get("amount", 0))
        if amount > 0 and outstanding_due > 0 and amount<=outstanding_due:
            # Create a settlement record
            Settlement.objects.create(
                customer=customer,
                amount_paid=amount,
                date=timezone.now()
            )

            # Apply the payment to unsettled transactions
            remaining = amount
            for t in customer.transactions.filter(is_settled=False).order_by("date"):
                if remaining <= 0:
                    break
                if remaining >= t.total_price:
                    t.is_settled = True
                    remaining -= t.total_price
                else:
                    # partial coverage — leave as not settled
                    remaining = 0
                t.save()

            return redirect("customer_dashboard", dnumber=customer.dnumber)
        else:
            message = f"Amount cannot be greater than or equal to outstanding due (₹{outstanding_due:.2f})."
            return redirect("settlement", dnumber=customer.dnumber)

    # Recalculate after settlement for display
    total_due = sum(t.total_price for t in customer.transactions.all())
    total_paid = sum(s.amount_paid for s in customer.settlements.all())
    outstanding_due = total_due - total_paid

    return render(request, "store/settlement.html", {
        "customer": customer,
        "outstanding_due": max(0, outstanding_due),  # never negative
        "total_bill": max(0, outstanding_due),
    })


def edit_customer(request, dnumber):
    customer = get_object_or_404(Customer, dnumber=dnumber)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("customer_list")
    else:
        form = CustomerForm(instance=customer)
    return render(request, "store/edit_customer.html", {"form": form, "customer": customer})


def delete_customer(request, dnumber):
    customer = get_object_or_404(Customer, dnumber=dnumber)
    if request.method == "POST":
        customer.delete()
        return redirect("customer_list")
    return render(request, "store/confirm_delete.html", {"customer": customer})
