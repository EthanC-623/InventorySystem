from django.shortcuts import render
from django.http import HttpResponse
from inventory.models import Product

# Create your views here.
def home(request):
    return render(request, "home.html")

def inventory(request):
    return render(request, "inventory.html")

def products(request):
    products_data = Product.objects.all()
    context = {
        "products_data": products_data
    }
    return render(request, "products.html", context)

def viewProduct(request, product_id):
    product = Product.objects.get(id=product_id)
    context = {
        "product": product
    }
    return render(request, "viewProduct.html", context)

def reports(request):
    return render(request, "reports.html")

def sales(request):
    return render(request, "sales.html")