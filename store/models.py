from django.db import models
from django.utils import timezone

# Customer model
class Customer(models.Model):
    cust_id = models.CharField(max_length=20, unique=True)   # Unique customer ID
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)

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
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.customer.name} bought {self.quantity} x {self.product.name}"
