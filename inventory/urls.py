from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("inventory/", views.inventory, name="inventory"),
    path("products/", views.products, name="products"),
    path("products/<int:product_id>/", views.viewProduct, name="viewProduct"),
    path("reports/", views.reports, name="reports"),
    path("stock-movement/", views.stockMovement, name="stockMovement"),
]