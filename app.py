from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
# ✅ Engine: database, auth, user model
from engine import db, init_app, register_user, login_user_helper, logout_user_helper
# ✅ TTS functions only (from engine.py)
# from engine import generate_tts
# ✅ LLM logic only (from llm_engine.py)
from llm_engine import query_llama3, SYSTEM_PROMPT #is_product_query
# ✅ Chat history
# from engine2 import get_chat_history, save_chat_history, clear_chat_history
# ✅ Caching (if you’re using it)
from cache_config import init_cache
# ✅ Async and threading
import os
import secrets
from datetime import timedelta
from io import BytesIO
import re
from dotenv import load_dotenv
from flask_cors import CORS
from scrap_local import scrape_products_by_category
from scrap_global import try_single_site_scrape
from product_extraction import extract_and_store_products
from llm_engine import summarize_products

load_dotenv()

app = Flask(__name__)
# 🔐 Secret Key for sessions
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(16)
# ✅ PostgreSQL (Neon) database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
# ✅ Init cache and database
init_cache(app)
init_app(app)
# ✅ Create tables if not exist
with app.app_context():
    from engine import db
    db.create_all()


@app.route('/')
@login_required
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        success, message, user = login_user_helper(username, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'danger')

    return render_template('login.html')

# Registration Page
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')  # Optional field
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('login'))

        success, message, _ = register_user(first_name, middle_name, last_name, username, email, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')

    return redirect(url_for('login'))

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user_helper()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

# Blog Page
@app.route('/blog')
@login_required
def blog():
    return render_template('blog.html')

# Contact Page
@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')


def remove_emojis(text):
    """Removes emojis from the given text."""
    return re.sub(r'[\U00010000-\U0010FFFF]', '', text)  # Matches all emojis



def remove_non_latin1(text):
    """Removes characters that are not in the Latin-1 range."""
    return "".join(c for c in text if ord(c) < 256)


# @app.route("/generate_tts", methods=["POST"])
# def generate_tts_audio():
#     """Handles TTS generation for the initial bot message."""
#     try:
#         data = request.get_json()
#         text = data.get("text", "").strip()

#         if not text:
#             return "❌ No text provided", 400

#         audio_bytes = generate_tts(text, "af_bella", 1.2)

#         if audio_bytes:
#             return send_file(BytesIO(audio_bytes), mimetype="audio/wav")

#         return "❌ TTS generation failed", 500

#     except Exception as e:
#         print(f"❌ TTS API Error: {e}")
#         return "Internal server error", 500


app.config['JSON_AS_ASCII'] = False  # ✅ Ensure UTF-8 encoding

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        print(f"📩 User Input: {user_input}")  # Debugging

        # ✅ Streaming Response Generator
        def generate():
            for chunk in query_llama3(user_input):
                yield chunk

        return Response(generate(), content_type="text/plain")

    except Exception as e:
        print(f"❌ Chat API Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/voice", methods=["POST"])
def voice():
    """Handles voice queries and fetches responses from AceBot with TTS."""
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()

        if not user_input:
            return "No message provided", 400

        # ✅ Streaming Response Generator for Voice
        def generate():
            for chunk in query_llama3(user_input):
                yield chunk

        return Response(generate(), content_type="text/plain")

    except Exception as e:
        print(f"❌ Voice API Error: {e}")
        return "Internal server error", 500
    

@app.route("/search-products", methods=["POST"])
def search_products():
    data = request.json
    query = (data.get("query") or "").strip().lower()
    category = data.get("category", "ratings")
    
    # Safely handle specificSite (could be None)
    raw_selected_site = data.get("specificSite", "")
    selected_site = raw_selected_site.strip() if isinstance(raw_selected_site, str) else ""

    bot_type = data.get("bot_type", "chat")

    print(f"[ROUTE] 🔔 Incoming search request: {data}")

    if not query:
        return jsonify({"error": "Missing product query"}), 400

    try:
        # ✅ 1. Handle single-site scraping
        if category == "specific-sites":
            if not selected_site:
                return jsonify({"error": "No specific site selected"}), 400
            results = try_single_site_scrape(query, selected_site)
        else:
            # ✅ 2. Multi-site or ratings-based scraping
            results, _ = scrape_products_by_category(query, category)

        # ✅ 3. Add source tag to each product
        for site_result in results:
            site_name = site_result["site"]
            for product in site_result["data"]:
                product["source"] = site_name

        # ✅ 4. Generate summary from LLM
        summary = summarize_products(query, results)

        # ✅ 5. Construct and return response
        response = {
            "products": results or [],
            "message": {
                "text": f"Here are the top products from {', '.join(r['site'].capitalize() for r in results)} displayed on your screen.",
                "speak": bot_type == "voice"
            },
            "summary": summary
        }

        return jsonify(response), 200

    except Exception as e:
        print("Scraping error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 5000, debug=True) 
