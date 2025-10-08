from django.db import models
from django.utils import timezone

# Customer model
class Customer(models.Model):
    dnumber = models.CharField(max_length=50, unique=True, null=True, blank=True)  # temporary fix
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.dnumber} - {self.name}"

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
    is_settled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.customer.name} bought {self.quantity} x {self.product.name}"

class Settlement(models.Model):
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE, related_name="settlements")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    mode = models.CharField(max_length=20, default="Cash")  # later extend to UPI, Card, etc.

    def __str__(self):
        return f"{self.customer.name} paid ₹{self.amount_paid} on {self.date.strftime('%Y-%m-%d')}"
