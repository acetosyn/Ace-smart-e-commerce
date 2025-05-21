import os
import json
from pathlib import Path

# ✅ Local path to categories.json
CATEGORIES_PATH = Path("static/data/categories.json")

# Basic keyword matching for fallback category detection
CATEGORY_KEYWORDS = {
    "phones": ["phone", "samsung", "iphone", "infinix", "xiaomi", "pixel", "tecno"],
    "laptops": ["laptop", "macbook", "thinkpad", "notebook", "zenbook", "aspire"],
    "fashion": ["shoe", "shirt", "bag", "sneaker", "suit", "t-shirt", "dress", "blazer"],
    "electronics": ["tv", "television", "headphone", "speaker", "camera", "earbud", "powerbank", "drone"],
    "home_appliances": ["fan", "microwave", "fridge", "air conditioner", "kettle", "freezer", "washing machine"],
    "beauty": ["cream", "lotion", "serum", "lipstick", "mascara", "foundation", "balm"],
    "gaming": ["playstation", "ps5", "xbox", "controller", "headset", "gaming"],
    "groceries": ["milk", "milo", "tea", "indomie", "spaghetti", "cereal", "oil", "beverage"],
    "baby_products": ["baby", "diaper", "infant", "stroller", "bottle", "lotion", "wipes"],
    "sports": ["shoe", "sneaker", "jersey", "dumbbell", "tennis", "swim", "watch"],
    "automotive": ["tyre", "battery", "oil", "filter", "engine", "wiper", "car"]
}

def detect_category(product_name: str) -> str:
    name = product_name.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(word in name for word in keywords):
            return cat
    return "general"

def update_categories_with_products(products: list):
    if not CATEGORIES_PATH.exists():
        print(f"[ERROR] categories.json not found at {CATEGORIES_PATH}")
        return

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)

    updated = False

    for product in products:
        name = product.get("name", "").strip()
        if not name:
            continue

        category = detect_category(name)
        if category not in categories:
            categories[category] = []

        if name not in categories[category]:
            categories[category].append(name)
            updated = True
            print(f"[✅ ADDED] '{name}' → {category}")

    if updated:
        with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
        print("[💾] categories.json updated successfully.")
    else:
        print("[ℹ️] No new entries were added.")

def extract_and_store_products(results: list):
    """
    Given raw scraped `results` from any site,
    extract product names and add them to categories.json
    """
    if not results or not isinstance(results, list):
        print("[WARN] Invalid or empty results passed to extraction.")
        return

    all_products = []
    for site_block in results:
        for item in site_block.get("data", []):
            if "name" in item:
                all_products.append(item)

    update_categories_with_products(all_products)
