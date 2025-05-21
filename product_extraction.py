import os
import json
import re
from pathlib import Path

# ✅ Path to categories.json
CATEGORIES_PATH = Path("static/data/categories.json")

# Category keywords for classification
CATEGORY_KEYWORDS = {
    "phones": ["phone", "samsung", "iphone", "infinix", "xiaomi", "pixel", "tecno"],
    "laptops": ["laptop", "macbook", "thinkpad", "notebook", "zenbook", "aspire", "rog"],
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


def clean_product_name(raw_name: str) -> str:
    """
    Clean product name by removing specs, models, sizes, and excessive descriptors.
    """
    name = raw_name.strip()

    # Remove text in parentheses or brackets
    name = re.sub(r"[\(\[].*?[\)\]]", "", name)

    # Remove model codes like 'G614JV-AS74' or 'ABC1234'
    name = re.sub(r"\b([A-Z]{2,}-?\d{2,}[\w\-]*)\b", "", name)

    # Remove specs like 16GB, 1TB, 165Hz, etc.
    name = re.sub(r"\b\d{2,4}(GB|TB|Hz|inch|in|MP|W|mAh|px|%)\b", "", name, flags=re.I)

    # Remove other tech specs and symbols
    name = re.sub(r"\b(Wi[-]?Fi|Bluetooth|RTX|DDR\d?|HDD|SSD|RAM|PCIe|Intel|Core|Gen\d+|Windows\s?\d+)\b", "", name, flags=re.I)

    # Remove extra hyphens, slashes, etc.
    name = re.sub(r"[-_/|•]", " ", name)

    # Remove extra punctuation and collapse spaces
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s{2,}", " ", name)

    return name.strip()


def update_categories_with_products(products: list):
    if not CATEGORIES_PATH.exists():
        print(f"[ERROR] categories.json not found at {CATEGORIES_PATH}")
        return

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)

    updated = False

    for product in products:
        raw_name = product.get("name", "").strip()
        if not raw_name:
            continue

        clean_name = clean_product_name(raw_name)
        if not clean_name:
            continue

        category = detect_category(clean_name)
        if category not in categories:
            categories[category] = []

        # Prevent duplicates (case-insensitive)
        existing = [item.lower() for item in categories[category]]
        if clean_name.lower() not in existing:
            categories[category].append(clean_name)
            updated = True
            print(f"[✅ ADDED] '{clean_name}' → {category}")
        else:
            print(f"[ℹ️] Skipped duplicate: {clean_name}")

    if updated:
        with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
        print("[💾] categories.json updated successfully.")
    else:
        print("[ℹ️] No new entries were added.")


def extract_and_store_products(results: list):
    """
    Extract product names from results and push to categories.json
    """
    if not results or not isinstance(results, list):
        print("[WARN] Invalid or empty results passed to extraction.")
        return

    all_products = []
    for site_block in results:
        if not isinstance(site_block, dict):
            continue
        for item in site_block.get("data", []):
            if "name" in item:
                all_products.append(item)

    update_categories_with_products(all_products)
