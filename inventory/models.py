from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        STAFF = "STAFF", "Staff"
        READ_ONLY = "READ_ONLY", "Read Only"
        

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=20, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.READ_ONLY)
    created_at = models.DateTimeField(auto_now_add=True)

class Product(models.Model):
    class Category(models.TextChoices):
        MINIATURE = "MINIATURE", "Miniature"
        BOARD_GAME = "BOARD_GAME", "Board Game"
        PAINT = "PAINT", "Paint"
        TCG = "TCG", "Trading Card Game"
        BOOK = "BOOK", "Book"
        ACCESSORY = "ACCESSORY", "Accessory"
        MISCELLANEOUS = "MISCELLANEOUS", "Miscellaneous"
        
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50, unique=True)
    sku = models.CharField(max_length=50, unique=True)
    brandId = models.ForeignKey('Brand', on_delete=models.PROTECT)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.MISCELLANEOUS)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    imageURl = models.URLField(max_length=200, null=True, blank=True)
    attributes = models.JSONField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Brand(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(max_length=200, null=True, blank=True)
    logoUrl = models.URLField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Location(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    isDefault = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Stock_item(models.Model):
    id = models.BigAutoField(primary_key=True)
    productId = models.ForeignKey('Product', on_delete=models.PROTECT)
    locationId = models.ForeignKey('Location', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    reservedQuantity = models.IntegerField(default=0)
    reorderThreshold = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Stock_movement(models.Model):
    class MovementReason(models.TextChoices):
        SALE = "SALE", "Sale"
        PURCHASE = "PURCHASE", "Purchase"
        MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT", "Manual Adjustment"
        TRANSFER_IN = "TRANSFER_IN", "Transfer In"
        TRANSFER_OUT = "TRANSFER_OUT", "Transfer Out"
        STOCK_TAKE = "STOCK_TAKE", "Stock Take"
        DAMAGE = "DAMAGE", "Damage"
        RETURN = "RETURN", "Return"
        EVENT_USAGE = "EVENT_USAGE", "Event Usage"
        
    id = models.BigAutoField(primary_key=True)
    stockItemId = models.ForeignKey('Stock_item', on_delete=models.PROTECT)
    movementReason = models.CharField(max_length=20, choices=MovementReason.choices, default=MovementReason.MANUAL_ADJUSTMENT)
    quantityDelta = models.IntegerField()
    reference = models.CharField(max_length=100, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey('User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)