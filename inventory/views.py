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

    # filter data based on the selected archived status
    if archived == "no":
        products_data = products_data.filter(archived=False)
        active_archived = "Active only"
    elif archived == "yes":
        products_data = products_data.filter(archived=True)
        active_archived = "Archived only"

    # filter data based on the selected brand
    if brand.isdigit():
        active_brand = Brand.objects.filter(id=brand).first()
        if active_brand:
            products_data = products_data.filter(brandId=brand)

    # filter data based on the selected category
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

    # filter data based on the selected reorder status
    if reorderStatus == "Not Reordering":
        inventory_data = inventory_data.filter(quantity__gt=F("reorderThreshold"))
        active_reorderStatus = "Not Reordering"
    elif reorderStatus == "Needs Reordering":
        inventory_data = inventory_data.filter(quantity__lte=F("reorderThreshold"))
        active_reorderStatus = "Needs Reordering"

    # filter data based on the selected location
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

    # filter data based on the selected location
    if location.isdigit():
        active_location = Location.objects.filter(id=location).first()
        if active_location:
            stockMovements_data = stockMovements_data.filter(locationId=location)

    # filter data based on the selected reason
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
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    active_location = None

    # filter data based on the selected location
    if location.isdigit():
        active_location = Location.objects.filter(id=location).first()
        if active_location:
            stockMovements_data = stockMovements_data.filter(locationId=location)
            inventory_data = inventory_data.filter(locationId=location)    

    # filter data based on the selected date range
    if start_date:
        stockMovements_data = stockMovements_data.filter(created_at__date__gte=start_date)
    if end_date:
        stockMovements_data = stockMovements_data.filter(created_at__date__lte=end_date)

    # get stock category stats for chart
    stockCategory_data = inventory_data.values_list("productId__category").annotate(total=Sum("quantity")).order_by("productId__category")
    stockCategory_stats = [item[1] for item in stockCategory_data]
    stockCategory_labels = [Product.Category(item[0]).label for item in stockCategory_data]

    # filter and get data 
    total_revenue = stockMovements_data.filter(movementReason="SALE").aggregate(total_revenue=Sum("totalValue"))["total_revenue"] or 0
    total_return_value = stockMovements_data.filter(movementReason="RETURN").aggregate(total_return_value=Sum("totalValue"))["total_return_value"] or 0
    total_purchase_value = stockMovements_data.filter(movementReason="PURCHASE").aggregate(total_purchase_value=Sum("totalValue"))["total_purchase_value"] or 0
    total_stock_value = inventory_data.aggregate(total=Sum(F("quantity") * F("productId__price")))["total"] or 0
    item_sales = stockMovements_data.filter(movementReason="SALE")

    # filter low stock items
    low_stock_items = inventory_data.filter(quantity__lte=F("reorderThreshold")).order_by("quantity")
    
    # merge sales data by productId and get top selling items
    combined_sales = {}

    for sale in item_sales:
        product_id = sale.stockItemId.productId
        if product_id not in combined_sales:
            combined_sales[product_id] = [0, 0, "", 0]
        combined_sales[product_id][0] += float(sale.totalValue)
        combined_sales[product_id][1] -= sale.quantityDelta
        combined_sales[product_id][2] = sale.stockItemId.productId.imageURl or ""
        combined_sales[product_id][3] = sale.stockItemId.productId.id

    ordered_sales = {k: v for k, v in sorted(combined_sales.items(), key=lambda item: item[1][0], reverse=True)}
    top_sales = dict(list(ordered_sales.items())[:25])

    # get true total revenue by subtracting total return value
    return_rate = 0
    if total_revenue:
        return_rate = ((total_return_value / total_revenue) * 100)
    
    total_revenue -= total_return_value

    # get stock movement stats for chart
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
        "stockCategory_stats": stockCategory_stats,
        "stockCategory_labels": stockCategory_labels,
        "inventory_data": inventory_data,
        "low_stock_items": low_stock_items,
        "reasons": Stock_movement.MovementReason.choices,
        "locations": Location.objects.order_by("name"),
        "active_location": active_location,
        "start_date": start_date,
        "end_date": end_date,
        "return_rate": return_rate,
        "total_revenue": total_revenue,
        "total_stock_value": total_stock_value,
        "total_purchase_value": total_purchase_value,
        "top_sales": top_sales,
    }
    return render(request, "reports.html", context)