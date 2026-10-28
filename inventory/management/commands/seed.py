import random
from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Max
from inventory.models import User, Brand, Location, Product, Stock_item, Stock_movement

# WARNING: This command is intended for development/testing purposes only. 
# It will create a large amount of sample data in the database, and can optionally delete all existing inventory data first. 
# Do not run this command in a production environment.

BRANDS = ["Games Workshop", "Citadel", "Wizards of the Coast", "Fantasy Flight",
          "Vallejo", "Army Painter", "Ravensburger", "Asmodee"]
LOCATIONS = ["Hobbiton Tabletop", "Rivendell Games", "Minas Tirith Miniatures"]
DEFAULT_LOCATION = "Hobbiton Tabletop"

# Which brands make which categories (brand names must match BRANDS above)
BRANDS_BY_CATEGORY = {
    "MINIATURE":     ["Games Workshop", "Fantasy Flight", "Asmodee"],
    "BOARD_GAME":    ["Ravensburger", "Fantasy Flight", "Asmodee", "Wizards of the Coast"],
    "PAINT":         ["Citadel", "Vallejo", "Army Painter"],
    "TCG":           ["Wizards of the Coast", "Asmodee"],
    "BOOK":          ["Games Workshop", "Wizards of the Coast", "Fantasy Flight"],
    "ACCESSORY":     ["Citadel", "Army Painter", "Games Workshop", "Ravensburger"],
    "MISCELLANEOUS": BRANDS,
}

# (name pool, price range) per category
CATALOG = {
    "MINIATURE": (
        ["Space Marine Intercessors", "Orc Boyz", "Skeleton Warriors", "Dwarf Longbeards",
         "Elf Archers", "Necron Warriors", "Chaos Cultists", "Knight Paladin", "Goblin Raiders",
         "Dragon Wyrmling", "Tyranid Hormagaunts", "Stormcast Liberators", "Cavalry Squadron",
         "Hero Command Squad", "Battle Tank"],
        (12, 120)),
    "BOARD_GAME": (
        ["Dungeon Crawlers", "Trade Routes", "Castle Siege", "Galaxy Conquest", "Forest Folk",
         "Harbour Merchants", "Mystery Manor", "Dragon's Hoard", "Rail Barons", "Island Settlers",
         "Shadow Heist", "Kingdom Builders", "Space Station Alpha", "Tavern Tales"],
        (20, 110)),
    "PAINT": (
        ["Blood Red", "Warp Purple", "Leaf Green", "Ocean Blue", "Bone White", "Charcoal Black",
         "Sunburst Yellow", "Rust Orange", "Skin Tone Base", "Metallic Silver", "Antique Gold",
         "Deep Brown Wash", "Ash Grey Layer", "Emerald Glaze", "Matt Varnish"],
        (2, 6)),
    "TCG": (
        ["Booster Pack", "Booster Box", "Starter Deck", "Commander Deck", "Draft Box",
         "Collector Bundle", "Prerelease Kit", "Theme Deck", "Elite Trainer Set", "Card Singles Lot"],
        (4, 160)),
    "BOOK": (
        ["Core Rulebook", "Campaign Guide", "Painting Handbook", "Army Codex", "Bestiary",
         "Adventure Module", "Lore Compendium", "Terrain Building Guide", "Player's Handbook",
         "Art Book"],
        (15, 65)),
    "ACCESSORY": (
        ["Brush Set", "Dice Set", "Card Sleeves", "Deck Box", "Storage Case", "Playmat",
         "Basing Kit", "Hobby Knife", "Clippers", "Miniature Tray", "Dice Tower", "Wet Palette",
         "Tape Measure", "Paint Rack"],
        (3, 45)),
    "MISCELLANEOUS": (
        ["Gift Card", "Tote Bag", "Enamel Pin", "Poster", "Sticker Pack", "Mug", "T-Shirt",
         "Lanyard", "Keyring", "Event Ticket"],
        (2, 30)),
}

# reason: ((min, max) quantity change, relative weight)
MOVEMENTS = {
    "SALE":              ((-5, -1),   50),   # by far the most common
    "PURCHASE":          ((10, 50),   12),   # regular restocking
    "RETURN":            ((1, 3),      6),   # some customers return items
    "TRANSFER_IN":       ((5, 25),     6),   # stock moved between stores
    "TRANSFER_OUT":      ((-25, -5),   6),
    "EVENT_USAGE":       ((-10, -2),   5),   # demos and in-store events
    "STOCK_TAKE":        ((-3, 3),     5),   # periodic count corrections
    "MANUAL_ADJUSTMENT": ((-5, 5),     3),   # occasional fixes
    "DAMAGE":            ((-3, -1),    2),   # rare
}


def make_delta(reason):
    low, high = MOVEMENTS[reason][0]
    delta = 0
    while delta == 0:                 # a movement of 0 is meaningless
        delta = random.randint(low, high)
    return delta

def make_name(category, brand, number):
    pool, _ = CATALOG[category]
    base = random.choice(pool)
    # Paints, books and TCG items read better with a brand/series prefix
    if category == "PAINT":
        return f"{brand} {base}"
    return f"{base} ({brand}) #{number}"

def random_time_in_past_year():
    day = timezone.now() - timedelta(days=random.randint(0, 364))
    return day.replace(hour=random.randint(9, 17), minute=random.randint(0, 59),
                        second=random.randint(0, 59), microsecond=0)

def random_time_between(start, end):
    """Random datetime between start and end."""
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(span, 0)))

class Command(BaseCommand):
    help = "Populate the database with sample inventory data"

    def add_arguments(self, parser):
        parser.add_argument("--products", type=int, default=200, help="Number of products to add")
        parser.add_argument("--movements", type=int, default=300, help="Number of stock movements to add")
        parser.add_argument("--clear", action="store_true", help="Delete all inventory data first")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["clear"]:
            Stock_movement.objects.all().delete()
            Stock_item.objects.all().delete()
            Product.objects.all().delete()
            Location.objects.all().delete()
            Brand.objects.all().delete()
            self.stdout.write("Cleared existing inventory data.")

        brands = {n: Brand.objects.get_or_create(name=n)[0] for n in BRANDS}
        locations = [
            Location.objects.get_or_create(name=n, defaults={"isDefault": n == DEFAULT_LOCATION})[0]
            for n in LOCATIONS
        ]

        start = (Product.objects.aggregate(m=Max("id"))["m"] or 0) + 1
        products = []
        for i in range(start, start + opts["products"]):
            category = random.choice(list(CATALOG))
            brand = brands[random.choice(BRANDS_BY_CATEGORY[category])]
            low, high = CATALOG[category][1]
            products.append(Product(
                name=make_name(category, brand.name, i),
                sku=f"{brand.name[:3].upper()}-{i:06d}",
                barcode=f"200{i:09d}",
                brandId=brand,
                category=category,
                price=round(random.uniform(low, high), 2),
                archived=random.random() < 0.1,
            ))
        Product.objects.bulk_create(products, batch_size=500)

        stock = []
        for p in Product.objects.filter(stock_item__isnull=True):
            for loc in random.sample(locations, k=random.randint(1, len(locations))):
                stock.append(Stock_item(
                    productId=p,
                    locationId=loc,
                    quantity=random.randint(0, 60),
                    reservedQuantity=random.randint(0, 10),
                    reorderThreshold=random.choice([0, 5, 10, 15]),
                ))
        Stock_item.objects.bulk_create(stock, batch_size=500)
        
        now = timezone.now()
        year_ago = now - timedelta(days=365)
        extra_ago = now - timedelta(days=395)   # products exist before the movement window starts

        # Products: created between 13 and 12 months ago
        for p in products:
            p.created_at = random_time_between(extra_ago, year_ago)
            p.updated_at = p.created_at
        Product.objects.bulk_update(products, ["created_at", "updated_at"], batch_size=500)

        # Stock items: created after their product, before the movement window starts
        new_stock = Stock_item.objects.filter(productId__in=products).select_related("productId")
        new_stock = list(new_stock)
        for si in new_stock:
            si.created_at = random_time_between(si.productId.created_at, year_ago)
            si.updated_at = si.created_at
        Stock_item.objects.bulk_update(new_stock, ["created_at", "updated_at"], batch_size=500)
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if user is None:
            user = User.objects.create_user(username="seed_user", password="seed_password", role=User.Role.ADMIN)
            self.stdout.write(self.style.WARNING("No users found, created 'seed_user' (password: seed_password)."))

        # Movements
        reasons = list(MOVEMENTS)
        weights = [MOVEMENTS[r][1] for r in reasons]
        items = list(
            Stock_item.objects.select_related("locationId").order_by("?")[:opts["movements"]]
        )
        movements = []
        for si in items:
            reason = random.choices(reasons, weights=weights)[0]
            movements.append(Stock_movement(
                stockItemId=si,
                locationId=si.locationId,
                movementReason=reason,
                quantityDelta=make_delta(reason),
                created_by=user,
            ))
        Stock_movement.objects.bulk_create(movements)

        # auto_now_add ignores values set before saving, so backdate afterwards
        for m in movements:
            m.created_at = random_time_between(max(m.stockItemId.created_at, year_ago), now)
        Stock_movement.objects.bulk_update(movements, ["created_at"], batch_size=500)
        
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(products)} products, {len(stock)} stock items, {len(items)} movements."
        ))