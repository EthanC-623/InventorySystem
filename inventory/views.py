from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import F, Sum
from inventory.models import Brand, Location, Product, Stock_item, Stock_movement, User

# Create your views here.
def home(request):
    return render(request, "home.html")

def products(request):
    products_data = Product.objects.select_related("brandId")

    archived = request.GET.get("archived", "")
    brand = request.GET.get("brand", "")
    category = request.GET.get("category", "")

    active_category = None
    active_brand = None
    active_archived = None

    if archived == "no":
        products_data = products_data.filter(archived=False)
        active_archived = "Active only"
    elif archived == "yes":
        products_data = products_data.filter(archived=True)
        active_archived = "Archived only"

    if brand.isdigit():
        active_brand = Brand.objects.filter(id=brand).first()
        if active_brand:
            products_data = products_data.filter(brandId=brand)

    if category in Product.Category.values:
        active_category = Product.Category(category).label
        products_data = products_data.filter(category=category)

    context = {
        "products_data": products_data,
        "brands": Brand.objects.order_by("name"),
        "categories": Product.Category.choices,
        "active_category": active_category,
        "active_brand": active_brand,
        "active_archived": active_archived,
    }
    return render(request, "products.html", context)

def inventory(request):
    inventory_data = Stock_item.objects.select_related("locationId")

    location = request.GET.get("location", "")
    reorderStatus = request.GET.get("reorderStatus", "")

    active_location = None
    active_reorderStatus = None

    if reorderStatus == "Not Reordering":
        inventory_data = inventory_data.filter(quantity__gt=F("reorderThreshold"))
        active_reorderStatus = "Not Reordering"
    elif reorderStatus == "Needs Reordering":
        inventory_data = inventory_data.filter(quantity__lte=F("reorderThreshold"))
        active_reorderStatus = "Needs Reordering"

    if location.isdigit():
        active_location = Location.objects.filter(id=location).first()
        if active_location:
            inventory_data = inventory_data.filter(locationId=location)
    

    context = {
        "inventory_data": inventory_data,
        "locations": Location.objects.order_by("name"),
        "active_location": active_location,
        "active_reorderStatus": active_reorderStatus,
    }
    return render(request, "inventory.html", context)

def viewProduct(request, product_id):
    product = Product.objects.get(id=product_id)
    context = {
        "product": product
    }
    return render(request, "viewProduct.html", context)

def stockMovement(request):
    stockMovements_data = Stock_movement.objects.select_related("stockItemId")

    reason = request.GET.get("reason", "")
    location = request.GET.get("location", "")

    active_location = None
    active_reason = None

    if location.isdigit():
        active_location = Location.objects.filter(id=location).first()
        if active_location:
            stockMovements_data = stockMovements_data.filter(locationId=location)

    if reason in Stock_movement.MovementReason.values:
        active_reason = Stock_movement.MovementReason(reason).label
        stockMovements_data = stockMovements_data.filter(movementReason=reason)
    
    context = {
        "stockMovements_data": stockMovements_data,
        "reasons": Stock_movement.MovementReason.choices,
        "locations": Location.objects.order_by("name"),
        "active_reason": active_reason,
        "active_location": active_location,
    }

    return render(request, "stockMovement.html", context)

def reports(request):
    stockMovements_data = Stock_movement.objects.select_related("stockItemId")
    inventory_data = Stock_item.objects.select_related("locationId")

    location = request.GET.get("location", "")

    active_location = None

    if location.isdigit():
        active_location = Location.objects.filter(id=location).first()
        if active_location:
            stockMovements_data = stockMovements_data.filter(locationId=location)
            inventory_data = inventory_data.filter(locationId=location)

    if location.isdigit():
        total_revenue = Stock_movement.objects.filter(movementReason="SALE", locationId=location).aggregate(total_revenue=Sum("totalValue"))["total_revenue"]
        total_return_value = Stock_movement.objects.filter(movementReason="RETURN", locationId=location).aggregate(total_return_value=Sum("totalValue"))["total_return_value"]
        total_stock_value = Stock_item.objects.filter(locationId=location).aggregate(total_stock_value=Sum("productId__price"))["total_stock_value"]
        total_purchase_value = Stock_movement.objects.filter(movementReason="PURCHASE", locationId=location).aggregate(total_purchase_value=Sum("totalValue"))["total_purchase_value"]
    else:
        total_revenue = Stock_movement.objects.filter(movementReason="SALE").aggregate(total_revenue=Sum("totalValue"))["total_revenue"]
        total_return_value = Stock_movement.objects.filter(movementReason="RETURN").aggregate(total_return_value=Sum("totalValue"))["total_return_value"]
        total_stock_value = Stock_item.objects.aggregate(total_stock_value=Sum("productId__price"))["total_stock_value"]
        total_purchase_value = Stock_movement.objects.filter(movementReason="PURCHASE").aggregate(total_purchase_value=Sum("totalValue"))["total_purchase_value"]

    rate_of_return = 0
    if total_return_value and total_revenue:
        rate_of_return = 100 - ((total_return_value / total_revenue) * 100)
         # get true total revenue by subtracting total return value
        total_revenue -= total_return_value

   

    stockMovement_stats = {}
    new_value = 0
    for i in range(len(Stock_movement.MovementReason.choices)):
        stockMovement_stats[Stock_movement.MovementReason.choices[i][1]] = 0
        for entry in stockMovements_data:
            if entry.movementReason == Stock_movement.MovementReason.choices[i][0]:
                new_value = stockMovement_stats.get(Stock_movement.MovementReason.choices[i][1])
                new_value += 1
                stockMovement_stats.update({Stock_movement.MovementReason.choices[i][1]:new_value})

    sortedStockMovement_stats = sorted(stockMovement_stats.items(), key=lambda x:x[1])
    stockMovement_stats = dict(sortedStockMovement_stats)
  
    context = {
        "stockMovements_data": stockMovements_data,
        "stockMovement_stats": list(stockMovement_stats.values()),
        "stockMovement_labels": list(stockMovement_stats.keys()),
        "inventory_data": inventory_data,
        "reasons": Stock_movement.MovementReason.choices,
        "locations": Location.objects.order_by("name"),
        "active_location": active_location,
        "rate_of_return": rate_of_return,
        "total_revenue": total_revenue,
        "total_stock_value": total_stock_value,
        "total_purchase_value": total_purchase_value,
    }
    return render(request, "reports.html", context)