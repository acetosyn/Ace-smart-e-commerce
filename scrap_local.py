# scrap_local.py
import os
import time
import hashlib
import requests
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import traceback
from product_extraction import extract_and_store_products

load_dotenv()
SCRAPER_API_KEY = os.getenv("scraper_api")
SCRAPINGBEE_API_KEY = os.getenv("scraping_bee_api")

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

def fetch_with_retry(payload, use_scrapingbee=False, retries=3, delay=5):
    base_url = "https://app.scrapingbee.com/api/v1" if use_scrapingbee else "https://api.scraperapi.com/"

    for attempt in range(retries):
        try:
            response = requests.get(base_url, params=payload, headers={"User-Agent": "Mozilla/5.0"})
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


def fuzzy_match(query, name):
    return all(word in name.lower() for word in query.lower().split())


#Function to give a definate product return and filter out unecessary product not searched
UNWANTED_KEYWORDS = {"case", "cover", "protector", "screen", "glass"}

def is_relevant_product(query, name):
    if not fuzzy_match(query, name):
        return False
    name_lower = name.lower()
    return not any(bad in name_lower for bad in UNWANTED_KEYWORDS)


#---------------------------------------------EXTRACTION----------------------------------------------------------------------------
#JUMIA EXTRACT

# JUMIA
def extract_jumia_data(html, product_query):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("article.prd")[:30]
    products = []

    # Keywords to exclude accessories, cases, chargers, etc.
    exclusion_keywords = ["case", "cover", "screen", "protector", "charger", "cable", "adapter", "glass", "earpiece", "battery", "strap"]

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

            # Filter: skip accessories or unrelated items
            if name and any(ex_kw.lower() in name.lower() for ex_kw in exclusion_keywords):
                continue

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

    # Sort best rated first
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
    print(f"[🔍 AMAZON] Structured search for: {product_query}")

    # Step 1: Keyword Search to get ASINs
    search_endpoint = "https://api.scraperapi.com/structured/amazon/search"
    search_params = {
        "api_key": SCRAPER_API_KEY,
        "query": product_query
    }

    search_res = requests.get(search_endpoint, params=search_params)
    if search_res.status_code != 200:
        print("[❌ AMAZON] Search failed")
        return []

    search_data = search_res.json()
    asins = [item["asin"] for item in search_data.get("results", []) if "asin" in item][:4]
    print(f"[✅ AMAZON] Found ASINs: {asins}")

    # Step 2: Fetch product data for each ASIN
    product_endpoint = "https://api.scraperapi.com/structured/amazon/product"
    products = []

    for asin in asins:
        try:
            res = requests.get(product_endpoint, params={"api_key": SCRAPER_API_KEY, "asin": asin})
            if res.status_code != 200:
                continue

            data = res.json()

            name = data.get("name")
            price = data.get("pricing") or data.get("list_price", "Not listed")
            rating = float(data.get("average_rating", 0.0))
            url = f"https://www.amazon.com/dp/{asin}"
            image = data.get("images", [None])[0]

            if name and image:
                products.append({
                    "name": name,
                    "price": price,
                    "rating": rating,
                    "url": url,
                    "image": image
                })

        except Exception as e:
            print(f"[⚠️ AMAZON] Failed to process ASIN {asin}: {e}")
            continue

    # Sort like Jumia
    five_star = [p for p in products if p["rating"] == 5.0]
    four_star = [p for p in products if 4.0 <= p["rating"] < 5.0]
    sorted_results = five_star + sorted(four_star, key=lambda x: x["rating"], reverse=True)

    return sorted_results[:4]





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

                # 🔁 Choose ScrapingBee for Jumia, ScraperAPI otherwise
                if site == "jumia":
                    payload = {
                        'api_key': os.getenv("scraping_bee_api"),
                        'url': search_url,
                        'render_js': "true"
                    }
                    proxy_url = "https://app.scrapingbee.com/api/v1"
                else:
                    payload = {
                        'api_key': SCRAPER_API_KEY,
                        'url': search_url,
                        'render': 'true',
                        'autoparse': 'false',
                        'country_code': 'ng',
                        'device_type': 'desktop'
                    }
                    proxy_url = "https://api.scraperapi.com/"

                response = requests.get(proxy_url, params=payload, headers={"User-Agent": "Mozilla/5.0"})
                print(f"[DEBUG] Attempt → Status: {response.status_code}")
                print(f"[DEBUG] Final URL: {response.url}")

                if response.status_code != 200:
                    print(f"[ERROR] Non-200 response from {site}. Content:\n{response.text[:400]}")
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
    extract_and_store_products(results)
    return results, False
