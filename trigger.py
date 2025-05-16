# trigger.py

FETCH_PHRASES = {
    "jumia": ["from jumia", "yes jumia", "get it from jumia", "fetch it from jumia", "search for it from jumia"],
    "amazon": ["from amazon", "yes amazon", "get it from amazon", "fetch it from amazon", "search for it from amazon"],
    "konga": ["from konga", "yes konga", "get it from konga", "fetch it from konga", "search for it from konga"],
    "slot": ["from slot", "yes slot", "get it from slot"],
    "kara": ["from kara", "yes kara", "get it from kara"],
    "ajebomarket": ["from ajebo", "from ajebomarket", "yes ajebo", "get it from ajebo"],
    "jiji": ["from jiji", "yes jiji", "get it from jiji"]
}

def detect_fetch_trigger(user_input):
    """Detects if user input contains a fetch trigger for a specific site."""
    user_input = user_input.lower()
    for site, phrases in FETCH_PHRASES.items():
        if any(p in user_input for p in phrases):
            return site
    return None

def generate_fetch_response(site, product_name):
    """Returns a fetch command for the detected site and product."""
    product_name = product_name.title()
    site_label = site.capitalize() if site != "ajebomarket" else "AjeboMarket"
    return (
        f"Fetching {product_name} from {site_label}...\n"
        f"__FETCH_FROM_{site.upper()}__{product_name}"
    )
