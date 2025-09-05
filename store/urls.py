from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search_customer, name="search_customer"),
    path("add-transaction/<str:cust_id>/", views.add_transaction, name="add_transaction"),
    path("upload/", views.upload_customers, name="upload_customers"),  
    path("ajax-search/", views.ajax_search_customer, name="ajax_search_customer"),
    path("customers/", views.customer_list, name="customer_list"),

]
