from django.contrib import admin
from .models import Customer, Product, Transaction

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("cust_id", "name", "phone")
    search_fields = ("cust_id", "name")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock")
    search_fields = ("name",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "quantity", "total_price", "date")
    list_filter = ("date",)
    search_fields = ("customer__name", "product__name")
