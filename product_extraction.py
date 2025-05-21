import os
import json
import re
from pathlib import Path

# ✅ Path to categories.json
CATEGORIES_PATH = Path("static/data/categories.json")

# Basic keyword matching for fallback category detection
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
    Remove unnecessary technical specs, model codes, and excessive descriptors.
    """
    name = raw_name.strip()

    # Remove text in parentheses or brackets
    name = re.sub(r"[\(\[].*?[\)\]]", "", name)

    # Remove long numeric strings, model numbers, special symbols
    name = re.sub(r"[-–—]{0,1}\s*\b(?:[A-Z]{1,4}[-]?\d{3,}.*|[A-Z]{2,}-\d{3,}.*?)\b", "", name)

    # Remove frequencies, resolutions, technical units, sizes, etc.
    name = re.sub(r"\b(\d{3,4}x\d{3,4}|\d{2,3}(Hz|GB|TB|inch|in)|Wi[-]?Fi|5G|4G|RAM|SSD|HDD|RTX|Intel|Core|Gen\d+|Windows\s?\d+|DDR\d?|PCIe.*?)\b", "", name, flags=re.I)

    # Collapse multiple spaces
    name = re.sub(r"\s{2,}", " ", name)

    # Remove trailing punctuation
    name = name.strip(" ,.-")

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

        existing_names = [n.lower() for n in categories[category]]
        if clean_name.lower() not in existing_names:
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
