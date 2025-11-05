# app.py
# Secure version of your Sentilizer Flask app.
# Contains: CSRF protection, rate limiting, secure cookie settings,
# security headers, basic input-length checks, model path validation,
# disabling debug for production, and a couple of helpful comments.

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from config import Config
from models import db, User, Contact
import html
import os
import joblib   # ✅ safer than pickle for your model objects
import numpy as np
import secrets
import re

# Security/utility extensions
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# ---------- Secure defaults (override or ensure in Config) ----------
# Ensure SECRET_KEY exists - prefer to set via environment (in .env)
if not app.config.get("SECRET_KEY"):
    # If no SECRET_KEY is provided, generate a secure one (use env in production).
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)

# Important session & cookie settings (set these in Config for production)
app.config.setdefault("SESSION_COOKIE_SECURE", True)       # only send cookies over HTTPS
app.config.setdefault("REMEMBER_COOKIE_SECURE", True)
app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)     # prevent JS access to cookie
app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)
app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")    # mitigate CSRF from other sites

# Disable debug in production - if you're testing locally, set to True; ensure False for deployment
app.config.setdefault("DEBUG", False)

# ---------- Initialize extensions ----------
csrf = CSRFProtect(app)  # adds CSRF protection for forms (requires {{ csrf_token() }} in your forms)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Note: We will add stricter limit for login route below.

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirect unauthenticated users to this view

# ---------- Context processor ----------
@app.context_processor
def inject_request():
    # Provide `request` to templates if needed
    return dict(request=request)

# ---------- Initialize DB ----------
db.init_app(app)
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)

with app.app_context():
    db.create_all()

# ---------- Validate model files before loading ----------
model_path = os.path.join(os.path.dirname(__file__), 'models', 'log_reg.pkl')
vectorizer_path = os.path.join(os.path.dirname(__file__), 'models', 'tfidf.pkl')

if not (os.path.exists(model_path) and os.path.exists(vectorizer_path)):
    # Fail fast if model files missing — prevents loading unexpected paths at runtime
    raise FileNotFoundError("Model or vectorizer file not found. Check models/log_reg.pkl and models/tfidf.pkl")

sentiment_model = joblib.load(model_path)
tfidf_vectorizer = joblib.load(vectorizer_path)

# ---------- User loader ----------
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# ---------- Security headers ----------
@app.after_request
def set_security_headers(response):
    # Basic security headers - tune CSP as per your frontend needs (scripts, fonts, CDNs).
    response.headers['X-Frame-Options'] = 'DENY'  # prevent clickjacking
    response.headers['X-Content-Type-Options'] = 'nosniff'  # prevent MIME sniffing
    # Minimal CSP - allow only same origin resources (adjust if you use external scripts/CDNs)
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

# Rate-limit contact form to avoid spam abuse
@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def contact():
    if request.method == 'POST':
        # Use html.escape to mitigate injected HTML (XSS) in stored messages
        name = html.escape(request.form.get('name', ''))
        email = html.escape(request.form.get('email', ''))
        message = html.escape(request.form.get('message', ''))

        # Basic validation + length checks to prevent excessively large inputs
        if not name or not email or not message:
            flash("All fields are required.", "error")
            return render_template('contact.html')

        if len(name) > 100 or len(email) > 200 or len(message) > 2000:
            flash("Input too long. Please shorten your message.", "error")
            return render_template('contact.html')

        try:
            new_message = Contact(name=name, email=email, message=message)
            db.session.add(new_message)
            db.session.commit()
            flash("Your message was sent successfully!", "success")
            return redirect(url_for('contact'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception("Error saving contact message")
            flash("Something went wrong. Please try again later.", "error")

    return render_template('contact.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', current_user=current_user)

# ---------- Signup with basic password strength checks ----------
@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # protect signups from abuse
def signup():
    if request.method == 'POST':
        username = html.escape(request.form.get('username', '').strip())
        email = html.escape(request.form.get('email', '').strip())
        password = request.form.get('password', '').strip()

        # Basic presence checks
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template('signup.html')

        # Input length checks
        if len(username) > 50 or len(email) > 150 or len(password) > 128:
            flash("Input too long.", "error")
            return render_template('signup.html')

        # Basic password strength enforcement (customize as needed)
        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash("Password must be at least 8 characters long and include letters and numbers.", "error")
            return render_template('signup.html')

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Username or email already exists.", "error")
            return render_template('signup.html')

        # Create user using your model's set_password method (keeps hashing centralized)
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            app.logger.exception("Error creating new user")
            flash("Something went wrong. Please try again later.", "error")

    return render_template('signup.html')

# ---------- Login (rate-limited to mitigate brute-force) ----------
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = html.escape(request.form.get('email', '').strip())
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("All fields are required.", "error")
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        # Use your model's check_password (which should use werkzeug.check_password_hash)
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            # Simple redirect after login (keeps UX straightforward)
            return redirect(url_for('dashboard'))
        else:
            # Do not reveal whether email exists or not — generic message
            flash("Invalid email or password.", "error")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# ---------- Sentiment analyze route (protected) ----------
@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    text = request.form.get('text', '').strip()

    # Small length check and empty-check
    if not text:
        flash("Please enter some text to analyze.", "error")
        return redirect(url_for('home'))
    if len(text) > 5000:
        flash("Text too long. Please reduce to 5000 characters or less.", "error")
        return redirect(url_for('home'))

    transform_text = tfidf_vectorizer.transform([text])
    prediction = sentiment_model.predict(transform_text)[0]
    probability = sentiment_model.predict_proba(transform_text)[0]

    if prediction == 1:
        result = f"Positive 😊 ({probability[1]*100:.2f}% confidence)"
        result_class = "positive"
    else:
        result = f"Negative 😞 ({probability[0]*100:.2f}% confidence)"
        result_class = "negative"

    return render_template('home.html', result=result, result_class=result_class)

# ---------- Run ----------
if __name__ == '__main__':
    # For local dev you can set app.run(debug=True), but ensure debug is False in production
    app.run(debug=app.config.get("DEBUG", False))
