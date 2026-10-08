from django.contrib import admin

# Register your models here.

from .models import Product, Stock_item, Brand, Stock_movement, User, Location

admin.site.register(User)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'barcode', 'sku', 'brandId', 'category', 'price',
                     'attributes', 'archived', 'created_at', 'updated_at')
    readonly_fields = ('sku', 'barcode', 'created_at', 'updated_at')
    list_filter = ('category', 'brandId')
    search_fields = ('name',)

admin.site.register(Stock_item)
admin.site.register(Brand)
admin.site.register(Stock_movement)
admin.site.register(Location)