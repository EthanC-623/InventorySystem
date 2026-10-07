from django.contrib import admin

# Register your models here.

from .models import Product, Stock_item, Brand, Stock_movement, User, Location

admin.site.register(User)
admin.site.register(Product)
admin.site.register(Stock_item)
admin.site.register(Brand)
admin.site.register(Stock_movement)
admin.site.register(Location)