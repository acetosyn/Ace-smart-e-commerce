# scrap_global.py

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
    search_url = ALL_SITES[site] + product_query.replace(" ", "+")
    print(f"[DEBUG] 🌐 Search URL: {search_url}")

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
        print(f"[ERROR] ❌ No response received from {site}")
        return []

    html = response.text
    extractor = EXTRACTOR_MAP[site]
    print(f"[DEBUG] 🛠️ Using extractor for: {site}")
    products = extractor(html, product_query)

    if not products:
        print(f"[WARN] ⚠️ No products found on {site}")
    else:
        print(f"[INFO] ✅ Found {len(products)} products on {site}")

    return [{
        "site": site,
        "data": products[:4]  # Optional: limit for consistency
    }] if products else []
