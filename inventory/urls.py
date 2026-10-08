from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("inventory/", views.inventory, name="inventory"),
    path("products/", views.products, name="products"),
    path("reports/", views.reports, name="reports"),
    path("sales/", views.sales, name="sales"),
]