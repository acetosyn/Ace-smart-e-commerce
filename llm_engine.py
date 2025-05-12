import re
import os
from dotenv import load_dotenv
from textblob import TextBlob
from groq import Groq

# Load API Key
load_dotenv()
groq_api_key = os.getenv("groq_api")
client = Groq(api_key=groq_api_key)

# System Prompt
SYSTEM_PROMPT = (
    "You are AceBot, an intelligent e-commerce assistant. Your job is to assist users in finding products, "
    "comparing prices, and providing the best deals available online. You should be friendly, smart, and responsive.\n\n"
    "✅ Rules:\n"
    "- Greet the user only on the first response.\n"
    "- Don’t repeat greetings like 'Hi' or 'Hello'.\n"
    "- If user asks 'what are you' or 'who are you', say: 'I’m AceBot, your e-commerce assistant! 😊'\n"
    "- If the user says 'I want to buy a [product]', ask for their preferred brand.\n"
    "- If they say 'I want to buy a phone', ask: 'Which brand? Samsung, iPhone, Tecno, or another brand?'\n"
    "- If a brand is mentioned, proceed to ask where they’d like to buy it: Jumia, Amazon, or compare all.\n"
    "- If the user says 'fetch it for me from Jumia' or 'yes, Jumia', populate the search bar with the product and trigger the search automatically."
)

user_history = []
user_context = {"product": None, "brand": None}
FIRST_RESPONSE = True

# Helpers
def is_emotional(user_input):
    return any(x in user_input.lower() for x in ["i'm sick", "i feel sad", "i'm tired", "i'm depressed", "i'm stressed"])

def is_greeting(user_input):
    return user_input.lower().strip() in ["hi", "hello", "hey", "xup", "yo", "howdy"]

def is_gratitude(user_input):
    return any(x in user_input.lower() for x in ["thank", "thanks", "appreciate it", "grateful", "thank you", "love it", "great", "nice one"])

def extract_product(user_input):
    match = re.search(r"(?:i want to buy|i want|buy|purchase|order|find|get)\s+(?:an|a|the)?\s*([a-zA-Z0-9\s\-]+)", user_input, re.IGNORECASE)
    if match:
        product = match.group(1).strip()
        product = re.sub(r"^(an|a|the)\s+", "", product, flags=re.IGNORECASE)
        product = re.sub(r"\s+", " ", product)
        return product

    blob = TextBlob(user_input)
    noun_phrases = blob.noun_phrases
    if noun_phrases:
        return noun_phrases[0]
    return None

def extract_brand(user_input):
    brands = ["samsung", "iphone", "tecno", "infinix", "xiaomi", "lg", "sony", "hp", "dell", "apple", "nokia"]
    return next((b.capitalize() for b in brands if b in user_input.lower()), None)

def should_trigger_jumia_fetch(user_input):
    phrases = [
        "get it from jumia",
        "fetch it from jumia",
        "search for it from jumia",
        "yes, jumia",
        "yes jumia",
        "yes"
    ]
    user_input_lower = user_input.lower()
    return any(phrase in user_input_lower for phrase in phrases)

# Main LLM Handler
def query_llama3(user_input):
    global FIRST_RESPONSE

    user_input = user_input.strip()
    user_history.append(user_input)

    if is_greeting(user_input):
        return "Hi once again, how can I help you?" if not FIRST_RESPONSE else "Hi! 😊 I'm AceBot, your e-commerce assistant! What product are you looking for today?"

    if "how are you" in user_input.lower():
        return "I'm doing great, thanks! 😊 How can I assist you?"

    if is_emotional(user_input):
        return "I'm really sorry to hear that 💙. I’m here if you need help finding something or just want to chat."

    if is_gratitude(user_input):
        return "You're welcome! Let me know if you'd like to order any other products from Jumia or other websites 😊."

    if "who are you" in user_input.lower() or "what are you" in user_input.lower():
        return "I’m AceBot, your e-commerce assistant! 😊"

    # Update context
    product = extract_product(user_input)
    brand = extract_brand(user_input)

    if product:
        user_context["product"] = product

        # Clear old brand if irrelevant to new product
        if user_context.get("brand"):
            brand_in_product = user_context["brand"].lower() in product.lower()
            non_electronics = ["shirt", "t-shirt", "shoe", "bag", "jacket", "watch", "cap", "jeans", "belt", "sneaker"]
            if not brand_in_product and any(kw in product.lower() for kw in non_electronics):
                user_context["brand"] = None

    if brand:
        user_context["brand"] = brand

    # Jumia fetch trigger
    if should_trigger_jumia_fetch(user_input):
        product_name = user_context.get("product", "").strip()

        if not product_name or product_name.lower() in ["it", "it from jumia", "from jumia"]:
            # Try previous meaningful product mention
            for past_input in reversed(user_history[:-1]):
                product_name = extract_product(past_input)
                if product_name and product_name.lower() not in ["it", "this", "that"]:
                    break

        if product_name:
            product_name = product_name.title()
            human_line = f"Fetching {product_name} from Jumia...\n"
            trigger_line = f"__FETCH_FROM_JUMIA__{product_name}"
            return human_line + trigger_line
        else:
            return "I need to know what product you're referring to before fetching from Jumia 😊."

    # Context-aware prompt
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
