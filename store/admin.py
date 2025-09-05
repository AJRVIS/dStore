from django.contrib import admin
from .models import Customer, Product, Transaction

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("cust_id", "name", "mobile", "email", "address")  # ✅ fixed

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "quantity", "total_price", "date")
