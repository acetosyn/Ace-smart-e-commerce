# scrap_global.py
import requests
import os
from product_extraction import extract_and_store_products
from scrap_local import (
    RATING_SITES,
    NON_RATING_SITES,
    extract_jumia_data,
    extract_amazon_data,
    extract_konga_data,
    extract_slot_data,
    extract_kara_data,
    extract_ajebomarket_data,
    extract_topsuccess_data,
    extract_jiji_data,
    fetch_with_retry,
    SCRAPER_API_KEY
)

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

ALL_SITES = {**RATING_SITES, **NON_RATING_SITES}

def try_single_site_scrape(product_query, site):
    if site not in ALL_SITES or site not in EXTRACTOR_MAP:
        print(f"[ERROR] ❌ Unsupported site: {site}")
        return []

    print(f"\n[INFO] 🔍 Scraping from the selected site: {site}")

    # ✅ Amazon uses ASIN-based structured endpoint
    if site == "amazon":
        print("[🔁 AMAZON] Using structured ASIN-based logic.")
        products = extract_amazon_data(None, product_query)
        result_data = [{
            "site": "amazon",
            "data": products
        }] if products else []
        extract_and_store_products(result_data)
        return result_data

    # ✅ For other sites
    search_url = ALL_SITES[site] + product_query.replace(" ", "+")
    print(f"[DEBUG] 🌐 Search URL: {search_url}")

    if site == "jumia":
        payload = {
            "api_key": os.getenv("scraping_bee_api"),
            "url": search_url,
            "render_js": "true"
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
        print(f"[ERROR] ❌ Non-200 response from {site}. Content:\n{response.text[:400]}")
        return []

    html = response.text
    extractor = EXTRACTOR_MAP[site]
    print(f"[DEBUG] 🛠️ Using extractor for: {site}")
    products = extractor(html, product_query)

    if not products:
        print(f"[WARN] ⚠️ No products found on {site}")
    else:
        print(f"[INFO] ✅ Found {len(products)} products on {site}")

    result_data = [{
        "site": site,
        "data": products[:4]
    }] if products else []

    extract_and_store_products(result_data)
    return result_data

