from django.db import models
from django.utils import timezone

# Customer model
class Customer(models.Model):
    cust_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # new field

    def __str__(self):
        return f"{self.cust_id} - {self.name}"



# Product model
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price in Rs
    stock = models.PositiveIntegerField(default=0)  # Available stock

    def __str__(self):
        return f"{self.name} (₹{self.price})"


# Transaction model (records purchases)
class Transaction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,related_name="transactions")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.customer.name} bought {self.quantity} x {self.product.name}"

class Settlement(models.Model):
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, related_name="settlements")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    mode = models.CharField(max_length=20, default="Cash")  # later extend to UPI, Card, etc.

    def __str__(self):
        return f"{self.customer.name} paid ₹{self.amount_paid} on {self.date.strftime('%Y-%m-%d')}"
