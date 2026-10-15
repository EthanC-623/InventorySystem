from django.shortcuts import render
from django.http import HttpResponse
from inventory.models import Brand, Product

# Create your views here.
def home(request):
    return render(request, "home.html")

def inventory(request):
    return render(request, "inventory.html")

def products(request):
    products_data = Product.objects.select_related("brandId")

    archived = request.GET.get("archived", "")
    brand = request.GET.get("brand", "")
    category = request.GET.get("category", "")

    if archived == "no":
        products_data = products_data.filter(archived=False)
    elif archived == "yes":
        products_data = products_data.filter(archived=True)

    if brand.isdigit():
        products_data = products_data.filter(brandId=brand)

    if category in Product.Category.values:
        products_data = products_data.filter(category=category)

    context = {
        "products_data": products_data,
        "brands": Brand.objects.order_by("name"),
        "categories": Product.Category.choices,
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