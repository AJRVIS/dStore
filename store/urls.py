from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_customer, name="search_customer"),
    path("add/<str:cust_id>/", views.add_transaction, name="add_transaction"),
]
