# scrap_local.py
import os
import time
import hashlib
import requests
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import traceback

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
            print(f"[DEBUG] Attempt {attempt + 1} → Status: {response.status_code}")
            print(f"[DEBUG] Final URL: {response.url}")

            if response.status_code == 200:
                return response
            else:
                print(f"[ERROR] Non-200 status. Content:\n{response.text[:500]}")

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request exception: {e}")

        time.sleep(random.randint(1, delay))

    return None


# def match_query_exactly(name, query):
#     query_keywords = query.lower().split()
#     product_name = name.lower()
#     return all(word in product_name for word in query_keywords)

def fuzzy_match(query, name):
    return all(word in name.lower() for word in query.lower().split())


#---------------------------------------------EXTRACTION----------------------------------------------------------------------------
#JUMIA EXTRACT
from bs4 import BeautifulSoup

# JUMIA
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

            if name and price and link and image and fuzzy_match(product_query, name):
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

# KONGA
def extract_konga_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    # print(f"\n\nThe soup object returned here is:\n{soup.prettify()}")  # ← This shows the full HTML in your terminal
    product_cards = soup.select("article.a2cf5_2S5q5")[:30]
    products = []

    for card in product_cards:
        try:
            name_elem = card.select_one("h3.af885_1iPzH")
            price_elem = card.select_one("span.d7c0f_sJAqi")
            image_elem = card.select_one("img")
            link_elem = card.select_one("a[href*='/product/']")

            name = name_elem.text.strip() if name_elem else None
            price = price_elem.text.strip() if price_elem else None
            link = "https://www.konga.com" + link_elem["href"] if link_elem else None
            image = image_elem.get("src") if image_elem else None

            if name and price and link and image and fuzzy_match(product_query, name):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []

# SLOT
def extract_slot_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    # print(f"\n\nThe soup object returned here is:\n{soup.prettify()}") 
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

            if name and price and link and image and fuzzy_match(product_query, name):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []


#KARA EXTRACT

def extract_kara_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    # print(f"\n\nThe soup object returned here is:\n{soup.prettify()}") 
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

            if name and price and link and image and fuzzy_match(product_query, name):
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
    # print(f"\n\nThe soup object returned here is:\n{soup.prettify()}") 
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

            if name and price and link and image and fuzzy_match(product_query, name):
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
    # print(f"\n\nThe soup object returned here is:\n{soup.prettify()}") 
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

            if name and price and link and image and fuzzy_match(product_query, name):
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

    # print(f"\n\nThe soup object returned here is:\n{soup.prettify()}") 
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

            if name and price and link and image and fuzzy_match(product_query, name):
                products.append({
                    "name": name,
                    "price": price,
                    "url": link,
                    "image": image
                })
        except Exception:
            continue

    return products[:4] if products else []


def extract_amazon_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    # print (f"\n\n Full HTML sample the Soup returned is : \n{soup.prettify()}")
    product_cards = soup.select("div.s-result-item[data-component-type='s-search-result']")[:30]
    products = []

    for card in product_cards:
        try:
            # Product name: fallbacks included
            name_elem = card.select_one("span.a-text-normal")
            name = name_elem.text.strip() if name_elem else None

            # Price
            price_elem = card.select_one("span.a-price > span.a-offscreen")
            price = price_elem.text.strip() if price_elem else None

            # Image
            image_elem = card.select_one("img.s-image")
            image = image_elem["src"] if image_elem and image_elem.get("src") else None

            # Link fallback
            link_elem = card.select_one("a.a-link-normal.s-no-outline") or card.select_one("a.a-link-normal")
            link = "https://www.amazon.com" + link_elem["href"] if link_elem else None

            # Rating
            rating_elem = card.select_one("span.a-icon-alt")
            rating_text = rating_elem.text.strip() if rating_elem else ""
            rating = 0.0
            if "out of" in rating_text:
                try:
                    rating = float(rating_text.split(" out of")[0])
                except ValueError:
                    rating = 0.0

            if name and price and link and image and fuzzy_match(product_query, name):
                products.append({
                    "name": name,
                    "price": price,
                    "rating": rating,
                    "url": link,
                    "image": image
                })

        except Exception:
            continue

    # Sort 5-star first, then 4-star
    five_star = [p for p in products if p["rating"] == 5.0]
    four_star = [p for p in products if 4.0 <= p["rating"] < 5.0]
    sorted_results = five_star + sorted(four_star, key=lambda x: x["rating"], reverse=True)

    return sorted_results[:4] if sorted_results else []





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
            try:
                if site not in sites_dict:
                    print(f"[WARN] Site key '{site}' not found in dictionary.")
                    continue

                base_url = sites_dict[site]
                search_url = base_url + product_query.replace(" ", "+")
                print(f"[INFO] Scraping from: {site}")
                print(f"[DEBUG] Search URL: {search_url}")

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
                    print(f"[ERROR] No response received from {site}")
                    continue

                html = response.text
                extractor = EXTRACTOR_MAP.get(site)
                if not extractor:
                    print(f"[ERROR] No extractor defined for site: {site}")
                    continue

                print(f"[DEBUG] Running extractor for {site}")
                products = extractor(html, product_query)

                if not products:
                    print(f"[WARN] No products found on {site}")
                elif len(products) < min_products_per_site:
                    print(f"[WARN] Only {len(products)} products found on {site}, below threshold of {min_products_per_site}")
                else:
                    print(f"[INFO] {len(products)} products found on {site}")
                    site_results.append({
                        "site": site,
                        "data": products[:min_products_per_site]
                    })

                if len(site_results) >= max_sites:
                    break

            except Exception as e:
                print(f"[EXCEPTION] Failed scraping {site}: {e}")
                traceback.print_exc()

        return site_results

    # Site groups
    rating_sites = list(RATING_SITES.keys())  # e.g., ["jumia", "amazon"]
    non_rating_sites = PRODUCT_PRIORITY.get(product_type, PRODUCT_PRIORITY["general"])

    if category == "ratings":
        results = try_scraping_sites(RATING_SITES, rating_sites)

    elif category == "non-ratings":
        results = try_scraping_sites(NON_RATING_SITES, non_rating_sites)

    else:
        # Default fallback to ratings
        results = try_scraping_sites(RATING_SITES, rating_sites)

    memory_cache[cache_key] = (results, False)
    return results, False
