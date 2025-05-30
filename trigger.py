# trigger.py

RATING_SITES = ["jumia", "amazon"]

# Restrict fetch phrases to rating sites only, and explicitly structured fetch intents
FETCH_PHRASES = {
    "jumia": ["fetch from jumia", "get it from jumia", "search from jumia"],
    "amazon": ["fetch from amazon", "get it from amazon", "search from amazon"]
}

def detect_fetch_trigger(user_input):
    """
    Detects if user input contains a valid and explicit fetch trigger
    for a rating-supported site only.
    """
    user_input = user_input.lower().strip()
    
    for site in RATING_SITES:
        phrases = FETCH_PHRASES.get(site, [])
        if any(p in user_input for p in phrases):
            return site
    
    return None


def generate_fetch_response(site, product_name, last_suggested=None):
    """
    Returns a formatted fetch command and response string.
    """
    if product_name.strip().lower() == "it" and last_suggested:
        product_name = last_suggested

    product_name = product_name.title()
    site_label = site.capitalize() if site != "ajebomarket" else "AjeboMarket"
    return (
        f"Fetching {product_name} from {site_label}...\n"
        f"__FETCH_FROM_{site.upper()}__{product_name}"
    )
