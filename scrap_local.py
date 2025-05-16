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
    "amazon": "https://www.amazon.com/s?k="
}

NON_RATING_SITES = {
    "konga": "https://www.konga.com/search?search=",
    "slot": "https://slot.ng/?s=",
    "kara": "https://www.kara.com.ng/catalogsearch/result/?q=",
    "ajebomarket": "https://ajebomarket.com/?s=",
    "topsuccess": "https://topsuccess.ng/?s=",
    "jiji": "https://jiji.ng/search?query="
}


PRODUCT_PRIORITY = {
    "fashion": ["ajebomarket", "konga", "jiji"],
    "electronics": ["slot", "kara", "topsuccess", "jiji"],
    "phones & tablets": ["slot", "kara", "jiji"],
    "appliances": ["kara", "topsuccess", "jiji"],
    "health & beauty": ["konga", "jiji"],
    "home & office": ["kara", "konga", "topsuccess", "jiji"],
    "supermarket": ["konga", "jiji"],
    "computing": ["slot", "kara", "jiji"],
    "baby products": ["konga", "jiji"],
    "gaming": ["kara", "jiji"],
    "musical instruments": ["kara", "jiji"],
    "general": ["konga", "slot", "kara", "topsuccess", "ajebomarket", "jiji"]
}

# Category → keywords to detect
PRODUCT_KEYWORDS = {
    "fashion": ["shirt", "jeans", "trouser", "dress", "shoe", "wear", "jacket", "cap", "bag", "t-shirt"],
    "electronics": ["tv", "laptop", "monitor", "camera", "speaker", "bluetooth", "dvd", "decoder"],
    "phones & tablets": ["phone", "iphone", "android", "tablet", "ipad", "smartphone"],
    "appliances": ["fridge", "refrigerator", "microwave", "freezer", "ac", "air conditioner", "fan", "cooker", "blender", "washing machine"],
    "health & beauty": ["cream", "lotion", "soap", "shampoo", "toothpaste", "perfume", "skincare"],
    "home & office": ["sofa", "desk", "chair", "bed", "lamp", "cabinet", "table", "mattress"],
    "supermarket": ["milk", "rice", "noodles", "biscuit", "sugar", "beverage", "tea", "juice"],
    "computing": ["keyboard", "mouse", "cpu", "ram", "ssd", "hard disk", "computer", "pc", "macbook"],
    "baby products": ["diaper", "baby", "stroller", "wipes", "milk", "feeder"],
    "gaming": ["console", "ps5", "xbox", "gamepad", "controller", "joystick"],
    "musical instruments": ["guitar", "keyboard", "drum", "piano", "microphone", "violin"]
}

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

#---------------------------------------------EXTRACTION----------------------------------------------------------------------------
#JUMIA EXTRACT
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

#KONGA EXTRACT
def extract_konga_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("div.af885_2o6yN")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("a.cebca_1iPzH span")
            price_elem = card.select_one("span.f89e4_2D88J")
            image_elem = card.select_one("img")
            link_elem = card.select_one("a.cebca_1iPzH")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = "https://www.konga.com" + link_elem["href"] if link_elem else None
            image = image_elem.get("data-src") or image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []


#AMAZON EXTRACT 

def extract_amazon_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("div.s-result-item")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("span.a-text-normal")
            price_elem = card.select_one("span.a-price > span.a-offscreen")
            image_elem = card.select_one("img.s-image")
            link_elem = card.select_one("a.a-link-normal.a-text-normal")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = "https://www.amazon.com" + link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "rating": 0.0,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []

#KARA EXTRACT

def extract_kara_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("li.item")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("h2.product-name a")
            price_elem = card.select_one("span.price")
            image_elem = card.select_one("img")
            link_elem = name_elem

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []

#SLOT EXTRACT

def extract_slot_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("ul.products li")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("h2.woocommerce-loop-product__title")
            price_elem = card.select_one("span.woocommerce-Price-amount")
            image_elem = card.select_one("img")
            link_elem = card.select_one("a.woocommerce-LoopProduct-link")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []

#AJEBO MARKET EXTRACT
def extract_ajebomarket_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("li.product")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("h2.woocommerce-loop-product__title")
            price_elem = card.select_one("span.woocommerce-Price-amount")
            image_elem = card.select_one("img")
            link_elem = card.select_one("a.woocommerce-LoopProduct-link")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []


#TOP SUCCES EXTRACT 

def extract_topsuccess_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("div.product-small")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("p.name.product-title")
            price_elem = card.select_one("span.woocommerce-Price-amount")
            image_elem = card.select_one("img")
            link_elem = card.select_one("a.woocommerce-LoopProduct-link")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []


#JIJI EXTRACTOR 

def extract_jiji_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("div.b-list-advert__item")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("div.b-list-advert__title a")
            price_elem = card.select_one("div.b-list-advert__price")
            image_elem = card.select_one("img")
            link_elem = name_elem

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = "https://jiji.ng" + link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and match_query_exactly(name, product_query):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []



def determine_product_type(query):
    q = query.lower()
    for category, keywords in PRODUCT_KEYWORDS.items():
        if any(keyword in q for keyword in keywords):
            return category
    return "general"

def scrape_products_by_category(product_query, category="ratings"):
    cache_key = generate_cache_key(f"{category}:{product_query}")
    if cache_key in memory_cache:
        return memory_cache[cache_key]

    product_type = determine_product_type(product_query)
    results = []

    # Extractor mapping
    EXTRACTOR_MAP = {
        "jumia": extract_jumia_data,
        "amazon": extract_amazon_data,
        "konga": extract_konga_data,
        "slot": extract_slot_data,
        "kara": extract_kara_data,
        "ajebomarket": extract_ajebomarket_data,
        "topsuccess": extract_topsuccess_data,
        "jiji": extract_jiji_data
    }

    def try_scraping_sites(sites_dict, site_keys, max_sites=3, min_products_per_site=2):
        site_results = []
        for site in site_keys:
            if site not in sites_dict:
                continue
            base_url = sites_dict[site]
            search_url = base_url + product_query.replace(" ", "+")
            print(f"[INFO] Scraping from: {site}")
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
            extractor = EXTRACTOR_MAP.get(site)
            products = extractor(html, product_query) if extractor else []

            if products and len(products) >= min_products_per_site:
                site_results.append({"site": site, "data": products[:min_products_per_site]})
                if len(site_results) >= max_sites:
                    break
        return site_results

    # Site priorities
    rating_sites = list(RATING_SITES.keys())  # ["jumia", "amazon"]
    non_rating_sites = PRODUCT_PRIORITY.get(product_type, PRODUCT_PRIORITY["general"])

    if category == "ratings":
        results = try_scraping_sites(RATING_SITES, rating_sites)
        if len(results) < 3:
            print("[INFO] Fallback to non-rating sites...")
            additional = try_scraping_sites(NON_RATING_SITES, non_rating_sites, max_sites=3 - len(results))
            results.extend(additional)

    elif category == "non-ratings":
        results = try_scraping_sites(NON_RATING_SITES, non_rating_sites)
        if len(results) < 3:
            print("[INFO] Fallback to rating sites...")
            additional = try_scraping_sites(RATING_SITES, rating_sites, max_sites=3 - len(results))
            results.extend(additional)

    else:
        # Default behaves like ratings category
        results = try_scraping_sites(RATING_SITES, rating_sites)
        if len(results) < 3:
            print("[INFO] Fallback to non-rating sites (auto)...")
            additional = try_scraping_sites(NON_RATING_SITES, non_rating_sites, max_sites=3 - len(results))
            results.extend(additional)

    memory_cache[cache_key] = (results, False)
    return results, False


