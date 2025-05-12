from flask_caching import Cache

cache = Cache()

# ✅ Function to initialize cache with a Flask app
def init_cache(app):
    app.config["CACHE_TYPE"] = "simple"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 1800
    cache.init_app(app)  # ✅ Bind cache to Flask app
