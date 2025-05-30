# llm_engine.py

import re
import os
import json
from dotenv import load_dotenv
from textblob import TextBlob
from groq import Groq
from trigger import detect_fetch_trigger, generate_fetch_response

# Load API Key
load_dotenv()
groq_api_key = os.getenv("groq_api")
client = Groq(api_key=groq_api_key)

SYSTEM_PROMPT = (
    "You are AceBot, an intelligent e-commerce assistant. Your job is to assist users in finding products, "
    "comparing prices, and providing the best deals available online from Jumia and Amazon only. "
    "You should be friendly, smart, and responsive.\n\n"
    "✅ Rules:\n"
    "- Greet the user only on the first response.\n"
    "- Don’t repeat greetings like 'Hi' or 'Hello'.\n"
    "- If the user asks 'what are you' or 'who are you', say: 'I’m AceBot, your e-commerce assistant! 😊'\n"
    "- If the user says 'I want to buy a [product]', ask for their preferred brand if it's vague.\n"
    "- If the product is a phone, ask: 'Which brand? Samsung, iPhone, Tecno, or another brand?'\n"
    "- If a brand is mentioned, ask whether they'd like to buy from Jumia or Amazon.\n"
    "- If the user says something like 'fetch it for me from Jumia' or 'Amazon', trigger a fetch by auto-typing the product name in the search bar without scraping directly.\n"
    "- If the product mentioned is specific enough (e.g., 'HP Envy M11', 'iPhone 11', 'Samsung 55-inch 4K Smart TV'), do not ask further questions. Confirm and trigger the fetch immediately.\n"
    "- After products are fetched and displayed, generate a short, helpful summary comparing them based on features, price range, and best available deals."
)

user_history = []
user_context = {"product": None, "brand": None}
FIRST_RESPONSE = True

# === Helper Functions ===

def is_emotional(user_input):
    return any(x in user_input.lower() for x in ["i'm sick", "i feel sad", "i'm tired", "i'm depressed", "i'm stressed"])

def is_greeting(user_input):
    return user_input.lower().strip() in ["hi", "hello", "hey", "xup", "yo", "howdy"]

def is_gratitude(user_input):
    return any(x in user_input.lower() for x in ["thank", "thanks", "appreciate it", "grateful", "thank you", "love it", "great", "nice one"])

def extract_product(user_input):
    match = re.search(r"(?:i want to buy|buy|get|fetch|search(?: for)?|look(?:ing)?(?: for)?)\s+(.*)", user_input, re.IGNORECASE)
    if match:
        product = match.group(1).strip()
        product = re.sub(r"\b(from amazon|from jumia|on amazon|on jumia)\b", "", product, flags=re.IGNORECASE)
        product = re.sub(r"^(an|a|the)\s+", "", product, flags=re.IGNORECASE)
        return product.strip()
    blob = TextBlob(user_input)
    noun_phrases = blob.noun_phrases
    if noun_phrases:
        return noun_phrases[0].strip()
    return None

def extract_brand(user_input):
    user_input_lower = user_input.lower()

    # Known direct brand keywords
    brands = {
        "samsung": ["samsung", "galaxy"],
        "iphone": ["iphone", "ios", "apple"],
        "tecno": ["tecno", "camon", "phantom"],
        "infinix": ["infinix", "hot", "zero", "note"],
        "xiaomi": ["xiaomi", "redmi", "poco", "mi"],
        "sony": ["sony", "bravia", "xperia"],
        "lg": ["lg"],
        "hp": ["hp", "pavilion", "envy", "omen"],
        "dell": ["dell", "inspiron", "xps", "latitude"],
        "nokia": ["nokia"],
        "apple": ["macbook", "mac", "ipad", "apple"]
    }

    for brand, keywords in brands.items():
        for keyword in keywords:
            if keyword in user_input_lower:
                return brand.capitalize()

    return None


# === Main LLM Chat Handler ===

def query_llama3(user_input):
    global FIRST_RESPONSE

    user_input = user_input.strip()
    user_history.append(user_input.lower())
    lower_input = user_input.lower()

    # === Basic Conversations ===
    if is_greeting(lower_input):
        response = "Hi! 😊 I'm AceBot, your e-commerce assistant! What product are you looking for today?" if FIRST_RESPONSE else "Hey again! What would you like to find today?"
        FIRST_RESPONSE = False
        return response

    if "how are you" in lower_input:
        return "I'm doing great, thanks for asking! 😊 How can I help you shop today?"

    if is_emotional(lower_input):
        return "I'm really sorry to hear that 💙. If browsing helps, I'm here to assist you anytime."

    if is_gratitude(lower_input):
        return "You're welcome! Let me know if you're looking for something specific. 😊"

    if "who are you" in lower_input or "what are you" in lower_input:
        return "I’m AceBot, your e-commerce assistant! 😊 Ready to help you find the best deals."

    # === Product & Brand Extraction ===
    product = extract_product(user_input)
    brand = extract_brand(user_input)

    if product:
        user_context["product"] = product
        # Reset brand if product is not electronic
        non_electronics = ["shirt", "t-shirt", "shoe", "bag", "jacket", "watch", "cap", "jeans", "belt", "sneaker"]
        if user_context.get("brand") and user_context["brand"].lower() not in product.lower():
            if any(kw in product.lower() for kw in non_electronics):
                user_context["brand"] = None

    if brand:
        if brand.lower() == "iphone":
            brand = "Apple"
        user_context["brand"] = brand

    # === Fetch Site Detection ===
    triggered_site = detect_fetch_trigger(user_input)
    if triggered_site:
        vague_terms = ["it", "this", "that", f"it from {triggered_site}", f"from {triggered_site}"]
        product_name = user_context.get("product", "").strip().lower()

        # Try to recover from history if the product name is vague
        if not product_name or product_name in vague_terms:
            for past_input in reversed(user_history[:-1]):
                recovered = extract_product(past_input)
                if recovered and recovered.lower() not in vague_terms:
                    product_name = recovered.strip()
                    break

        if not product_name or product_name in vague_terms:
            return (
                f"You asked me to fetch something from {triggered_site.capitalize()}, "
                "but I couldn't tell which product you're referring to. Could you please clarify?"
            )

        # Format fetch command
        return generate_fetch_response(triggered_site, product_name, last_suggested=user_context.get("product", ""))

    # === LLaMA-3 Fallback (streaming) ===
    product_context = f"{user_context['brand'] or ''} {user_context['product'] or ''}".strip()
    user_prompt = f"User: {user_input}\nContext: The user is interested in buying a {product_context}.\nAssistant:"

    def stream_response():
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    FIRST_RESPONSE = False
    return stream_response()



# === Product Summary Generator ===

def summarize_products(query, results):
    flat_products = []
    for site in results:
        for item in site["data"]:
            flat_products.append({
                "title": item.get("title", ""),
                "price": item.get("price", ""),
                "site": item.get("source", site.get("site", "")),
                "link": item.get("link", "")
            })

    prompt = (
        f"Given the following search for '{query}', summarize the product listings shown below. "
        "Highlight differences in price ranges, notable features, and which site seems to offer the best deals.\n\n"
        f"Products:\n{json.dumps(flat_products[:10], indent=2)}"
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
