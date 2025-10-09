from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search_customer, name="search_customer"),
    path("add-transaction/<int:dnumber>/", views.add_transaction, name="add_transaction"),
    path("upload/", views.upload_customers, name="upload_customers"),  
    path("ajax-search/", views.ajax_search_customer, name="ajax_search_customer"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customer/add/", views.add_customer, name="add_customer"),

    path("customer/<int:dnumber>/add-bill/", views.add_bill, name="add_bill"),
    path("customer/<int:dnumber>/", views.customer_dashboard, name="customer_dashboard"),

    path("transaction/<int:pk>/edit/", views.edit_transaction, name="edit_transaction"),
    path("transaction/<int:pk>/delete/", views.delete_transaction, name="delete_transaction"),
    path("customer/<int:dnumber>/settlement/", views.settlement, name="settlement"),

    path("customer/<int:dnumber>/edit/", views.edit_customer, name="edit_customer"),
    path("customer/<int:dnumber>/delete/", views.delete_customer, name="delete_customer"),
    
    path("ai-insights/", views.ai_insights, name="ai_insights"),
    

]
