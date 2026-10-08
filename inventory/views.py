from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, "home.html")

def inventory(request):
    return render(request, "inventory.html")

def products(request):
    return render(request, "products.html")

def reports(request):
    return render(request, "reports.html")

def sales(request):
    return render(request, "sales.html")