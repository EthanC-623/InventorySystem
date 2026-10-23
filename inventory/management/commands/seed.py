import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from inventory.models import User, Brand, Location, Product, Stock_item, Stock_movement

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


def make_name(category, brand, number):
    pool, _ = CATALOG[category]
    base = random.choice(pool)
    # Paints, books and TCG items read better with a brand/series prefix
    if category == "PAINT":
        return f"{brand} {base}"
    return f"{base} ({brand}) #{number}"


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
                    reorderThreshold=random.choice([0, 5, 10, 15]),
                ))
        Stock_item.objects.bulk_create(stock, batch_size=500)

        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if user is None:
            user = User.objects.create_user(username="seed_user", password="seed_password", role=User.Role.ADMIN)
            self.stdout.write(self.style.WARNING("No users found, created 'seed_user' (password: seed_password)."))

        reasons = list(Stock_movement.MovementReason.values)
        items = list(Stock_item.objects.order_by("?")[:opts["movements"]])
        Stock_movement.objects.bulk_create([
            Stock_movement(
                stockItemId=si,
                movementReason=random.choice(reasons),
                quantityDelta=random.randint(-10, 20),
                created_by=user,
            )
            for si in items
        ])

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(products)} products, {len(stock)} stock items, {len(items)} movements."
        ))