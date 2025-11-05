import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory (project root)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Instance directory for local SQLite DB and other local files
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


class Config:
    # === SECRET KEY ===
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    # Auto-generate if not set (for easier deployment)

    # === DATABASE CONFIGURATION ===
    # Prefer PostgreSQL if DATABASE_URL is provided (Render), otherwise use local SQLite
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        # Render automatically provides DATABASE_URL in environment
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_DIR, 'sentiment.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === SECURITY SETTINGS ===
    SESSION_COOKIE_SECURE = True              # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True            # Prevent JS access to session cookie
    SESSION_COOKIE_SAMESITE = "Lax"           # Mitigate CSRF
    REMEMBER_COOKIE_SECURE = True             # Flask-Login remember cookie
    REMEMBER_COOKIE_HTTPONLY = True

    # === CSRF Protection ===
    WTF_CSRF_ENABLED = True                   # Required for Flask-WTF forms

    # === OTHER SETTINGS ===
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024      # Limit uploads to 2 MB
    PREFERRED_URL_SCHEME = "https"            # Prefer HTTPS redirects


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False             # Dev uses HTTP
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_DIR, 'sentiment.db')}"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True              # Enforce HTTPS in production


# === AUTO CONFIG DETECTION ===
def get_config():
    """Return the correct config class based on environment (Render or local)."""
    if os.getenv("RENDER"):  # Render automatically sets this env variable
        return ProductionConfig
    else:
        return DevelopmentConfig
