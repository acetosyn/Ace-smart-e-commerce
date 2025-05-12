from cache_config import cache  # ✅ Import cache
import hashlib
import json
from flask import Flask, session  # ✅ Add Flask to initialize cache properly
from engine import query_acebot  

# ✅ Create a temporary Flask app for cache initialization (since app.py is separate)
flask_app = Flask(__name__)  
flask_app.config["CACHE_TYPE"] = "simple"
cache.init_app(flask_app)  # ✅ Initialize cache properly

# ✅ E-Commerce System Prompt
ECOMMERCE_PROMPT = (
    "You are AceBot, an advanced e-commerce assistant that scrapes multiple websites to find highly rated products. "
    "You must extract and return only the **top-rated products** based on customer reviews."
)

def generate_cache_key(query):
    """Generate a unique cache key based on the product query."""
    return hashlib.md5(query.encode()).hexdigest()

def query_acebot_for_products(product_query):
    """Query AceBot to scrape websites and return the best-rated products."""
    
    cache_key = generate_cache_key(product_query)
    
    # ✅ Check cache before scraping
    with flask_app.app_context():  
        cached_result = cache.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result), True  # ✅ Cached result
    
    # ✅ Format query for AceBot
    full_prompt = f"[INST] <<SYS>>\n{ECOMMERCE_PROMPT}\n<</SYS>>\n\nUser: Find me the best-rated {product_query}.\nAssistant:"
    
    bot_response = query_acebot(full_prompt)  # ✅ Query AceBot LLM
    
    # ✅ Store result in cache
    with flask_app.app_context():
        cache.set(cache_key, json.dumps(bot_response), timeout=1800)

    return bot_response, False  # ✅ Fresh result

