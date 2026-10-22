import os
import secrets
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "url_shortener")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]
urls = db["urls"]
users = db["users"]


def is_valid_url(value):
    """Accept absolute HTTP(S) URLs with a hostname and no whitespace."""
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if any(character.isspace() for character in value):
        return False
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        # Accessing parsed.port also catches malformed ports such as :abc or :99999.
        parsed.port
        return (
            parsed.scheme.lower() in ("http", "https")
            and bool(parsed.netloc)
            and bool(hostname)
            and "." in hostname
        )
    except (ValueError, UnicodeError):
        return False


def generate_short_code():
    """Generate a short code that is not already in the collection."""
    while True:
        code = secrets.token_urlsafe(5)
        if not urls.find_one({"short_code": code}):
            return code


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_or_username = request.form.get("email_or_username", "").strip()
        password = request.form.get("password", "")

        if not email_or_username or not password:
            flash("Enter both your email/username and password.", "error")
            return render_template("login.html")

        try:
            user = users.find_one({"$or": [{"email": email_or_username.lower()}, {"username": email_or_username.lower()}]})
        except PyMongoError:
            flash("Database error. Please try again later.", "error")
            return render_template("login.html")

        if user and check_password_hash(user.get("password", ""), password):
            session["user_id"] = str(user.get("_id"))
            session["username"] = user.get("username")
            flash("Welcome back!", "success")
            return redirect(url_for("index"))

        flash("Invalid email/username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"]) 
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        domain = request.form.get("domain", "").strip()

        if not email or not username or not password or not domain:
            flash("Please complete all fields: email, username, password, and domain.", "error")
            return render_template("signup.html")

        email_lower = email.lower()
        username_lower = username.lower()

        try:
            existing_user = users.find_one({"$or": [{"email": email_lower}, {"username": username_lower}]})
        except PyMongoError:
            flash("Database error. Please try again later.", "error")
            return render_template("signup.html")

        if existing_user:
            flash("An account with that email or username already exists.", "error")
            return render_template("signup.html")

        try:
            users.insert_one({
                "email": email_lower,
                "username": username_lower,
                "password": generate_password_hash(password),
                "domain": domain,
            })
        except PyMongoError:
            flash("Could not save your account. Please try again later.", "error")
            return render_template("signup.html")

        flash("Your account has been created successfully.", "success")
        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None

    if request.method == "POST":
        original_url = request.form.get("original_url", "").strip()

        if not is_valid_url(original_url):
            flash("Enter a valid URL beginning with http:// or https://, such as https://example.com.", "error")
        else:
            try:
                code = generate_short_code()
                urls.insert_one({
                    "short_code": code,
                    "original_url": original_url,
                    "clicks": 0,
                })
                short_url = url_for("redirect_url", code=code, _external=True)
                flash("Your short link is ready to share!", "success")
            except PyMongoError:
                flash("Database error. Check that MongoDB is running and your connection settings are correct.", "error")

    try:
        all_urls = list(urls.find().sort("_id", -1).limit(10))
    except PyMongoError:
        all_urls = []
        flash("Could not load recent links. Check your MongoDB connection.", "error")

    return render_template("index.html", short_url=short_url, all_urls=all_urls)


@app.route("/<code>")
def redirect_url(code):
    try:
        record = urls.find_one_and_update(
            {"short_code": code},
            {"$inc": {"clicks": 1}},
        )
    except PyMongoError:
        return "Database connection error.", 503

    if record is None:
        return "Short URL not found.", 404

    return redirect(record["original_url"], code=302)


if __name__ == "__main__":
    # Local development only. Disable debug mode for deployment.
    app.run(host="127.0.0.1", port=5000, debug=True)
