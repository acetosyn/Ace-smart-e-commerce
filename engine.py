from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
import os
from flask import Flask, request, jsonify
from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
import soundfile as sf
# from kokoro import KPipeline
from io import BytesIO




db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirect to login page if not authenticated
login_manager.login_message_category = "info"  # Flash message category for login-required messages




def init_app(app):
    """Initialize app with database and login manager."""
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()  # Ensure tables are created

# --------------------------
# 👤 USER MODEL (DATABASE)
# --------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")  # Default role as "customer"
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        """Hash and set the password using bcrypt."""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verify the password."""
        return bcrypt.check_password_hash(self.password, password)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login session management."""
    return User.query.get(int(user_id))

# --------------------------
# 🔐 USER AUTHENTICATION HELPERS
# --------------------------
def register_user(first_name, middle_name, last_name, username, email, password, role="customer"):
    """Register a new user with bcrypt password hashing."""
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return False, "Username or Email already exists.", None  # ✅ Now returns 3 values

    try:
        new_user = User(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            username=username,
            email=email,
            role=role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return True, "Registration successful. Please log in.", new_user  # ✅ Returns 3 values
    except Exception as e:
        db.session.rollback()
        return False, f"An error occurred: {str(e)}", None  # ✅ Now returns 3 values

def login_user_helper(username, password):
    """Authenticate user by checking hashed password."""
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return True, "Login successful.", user
    return False, "Invalid credentials.", None

def logout_user_helper():
    """Log out the current user."""
    logout_user()
    return True, "Logged out successfully."




# # ✅ Set Kokoro Path
# KOKORO_PATH = os.path.abspath("kokoro")
# os.environ["KOKORO_MODEL_DIR"] = KOKORO_PATH

# # ✅ Load Kokoro Model
# print("🔄 Loading Kokoro TTS model...")
# pipeline = KPipeline(lang_code='a')
# print("✅ Kokoro TTS model loaded successfully!")

def fix_tts_pronunciation(text):
    return text.replace("Acebot", "Ace Bot").replace("acebot", "Ace Bot").replace("ACEBOT", "Ace Bot")

def clean_tts_text(text):
    text = text.strip()
    if not text:
        return "Sorry, I didn't catch that."
    if text[-1] not in ".!?":
        text += "."
    return text

# def generate_tts(text, voice="af_bella", speed=1.2):
#     try:
#         text = fix_tts_pronunciation(text)
#         text = clean_tts_text(text)
#         generator = pipeline(text, voice=voice, speed=speed)
#         for _, _, audio in generator:
#             wav_buffer = BytesIO()
#             sf.write(wav_buffer, audio, samplerate=24000, format="WAV")
#             wav_buffer.seek(0)
#             return wav_buffer.read()
#     except Exception as e:
#         print(f"❌ Kokoro TTS Error: {e}")
#         return None


