# scrap_local.py
import os
import time
import hashlib
import requests
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
SCRAPER_API_KEY = os.getenv("scraper_api")

memory_cache = {}

RATING_SITES = {
    "jumia": "https://www.jumia.com.ng/catalog/?q=",
}

NON_RATING_SITES = {
    "konga": "https://www.konga.com/search?search=",
    "slot": "https://slot.ng/?s=",
    "kara": "https://www.kara.com.ng/catalogsearch/result/?q=",
    "ajebomarket": "https://ajebomarket.com/?s=",
    "topsuccess": "https://topsuccess.ng/?s="
}

PRODUCT_PRIORITY = {
    "wearables": ["ajebomarket", "konga", "jiji"],
    "electronics": ["slot", "topsuccess", "kara"]
}

WEARABLE_KEYWORDS = ["shirt", "jeans", "trouser", "dress", "shoe", "wear", "jacket", "cap", "bag", "t-shirt"]
ELECTRONIC_KEYWORDS = ["tv", "laptop", "phone", "camera", "monitor", "charger", "keyboard", "mouse", "speaker", "iphone", "ipad", "macbook"]

def generate_cache_key(query):
    return hashlib.md5(query.encode()).hexdigest()

def fetch_with_retry(payload, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get("https://api.scraperapi.com/", params=payload, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                return response
        except requests.exceptions.RequestException:
            pass
        time.sleep(random.randint(1, delay))
    return None

def match_query_exactly(name, query):
    query_keywords = query.lower().split()
    product_name = name.lower()
    return all(word in product_name for word in query_keywords)

def extract_jumia_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("article.prd")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("h3.name")
            price_elem = card.select_one("div.prc")
            image_elem = card.select_one("img")
            link_elem = card.select_one("a.core") or card.find("a")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = "https://www.jumia.com.ng" + link_elem["href"] if link_elem else None
            image = image_elem.get("data-src") or image_elem.get("src") if image_elem else None

            stars_container = card.select_one("div.stars")
            in_div = stars_container.select_one("div.in") if stars_container else None
            style = in_div.get("style") if in_div else ""
            star_value = None
            if style and "width" in style:
                width_percent = float(style.split("width:")[1].replace("%", "").strip())
                star_value = round((width_percent / 100) * 5, 1)

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "rating": star_value if star_value else 0.0,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    five_star = [p for p in products if p["rating"] == 5.0]
    four_star = [p for p in products if 4.0 <= p["rating"] < 5.0]
    sorted_results = five_star + sorted(four_star, key=lambda x: x["rating"], reverse=True)

    return sorted_results[:4] if sorted_results else []

def determine_product_type(query):
    q = query.lower()
    if any(keyword in q for keyword in WEARABLE_KEYWORDS):
        return "wearables"
    elif any(keyword in q for keyword in ELECTRONIC_KEYWORDS):
        return "electronics"
    return None

def scrape_products_by_category(product_query, category="ratings"):
    cache_key = generate_cache_key(f"{category}:{product_query}")
    if cache_key in memory_cache:
        return memory_cache[cache_key]

    results = []
    product_type = determine_product_type(product_query)

    if category == "ratings":
        sites = [("jumia", RATING_SITES["jumia"])]
        limit = 9
    elif product_type == "wearables":
        custom_sites = PRODUCT_PRIORITY["wearables"]
        sites = [(site, NON_RATING_SITES[site]) for site in custom_sites if site in NON_RATING_SITES]
        limit = 15
    elif product_type == "electronics":
        custom_sites = PRODUCT_PRIORITY["electronics"]
        sites = [(site, NON_RATING_SITES[site]) for site in custom_sites if site in NON_RATING_SITES]
        limit = 15
    else:
        sites = list(NON_RATING_SITES.items())
        limit = 15

    for name, base_url in sites:
        print(f"[INFO] Scraping from: {name}")
        search_url = base_url + product_query.replace(" ", "+")
        payload = {
            'api_key': SCRAPER_API_KEY,
            'url': search_url,
            'render': 'true',
            'autoparse': 'false',
            'country_code': 'ng',
            'device_type': 'desktop'
        }

        response = fetch_with_retry(payload)
        if not response:
            continue

        html = response.text
        if name == "jumia":
            products = extract_jumia_data(html, product_query)
        else:
            # Future support for other sites can be added here
            products = []

        if products:
            results.append({"site": name, "data": products})

    memory_cache[cache_key] = (results[:limit], False)
    return results[:limit], False
