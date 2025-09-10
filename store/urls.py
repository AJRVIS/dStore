from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search_customer, name="search_customer"),
    path("add-transaction/<str:cust_id>/", views.add_transaction, name="add_transaction"),
    path("upload/", views.upload_customers, name="upload_customers"),  
    path("ajax-search/", views.ajax_search_customer, name="ajax_search_customer"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customer/add/", views.add_customer, name="add_customer"),

    path('customer/<str:cust_id>/add-bill/', views.add_bill, name='add_bill'),
    path("customer/<str:cust_id>/", views.customer_dashboard, name="customer_dashboard"),

    path("transaction/<int:pk>/edit/", views.edit_transaction, name="edit_transaction"),
    path("transaction/<int:pk>/delete/", views.delete_transaction, name="delete_transaction"),
    path("customer/<str:cust_id>/settlement/", views.settlement, name="settlement"),

    path("customer/<str:cust_id>/edit/", views.edit_customer, name="edit_customer"),
    path("customer/<str:cust_id>/delete/", views.delete_customer, name="delete_customer"),

]
