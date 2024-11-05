from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-here"  # Change this to a secure secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///print_requests.db"
app.config["UPLOAD_FOLDER"] = "uploads"
ALLOWED_EXTENSIONS = {"gcode"}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Ensure upload directory exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    id_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    print_requests = db.relationship("PrintRequest", backref="user", lazy=True)


class PrintRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    filepath = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="pending")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    notes = db.Column(db.Text)
    estimated_time = db.Column(db.Integer)
    material_type = db.Column(db.String(50))
    material_amount = db.Column(db.Float)
    layer_height = db.Column(db.Float)


def validate_password(password):
    """
    Password must:
    - Be at least 8 characters long
    - Contain at least one uppercase letter
    - Contain at least one lowercase letter
    - Contain at least one number
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        id_number = request.form["id_number"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validate password match
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("register"))

        # Validate password strength
        if not validate_password(password):
            flash(
                "Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
            )
            return redirect(url_for("register"))

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format")
            return redirect(url_for("register"))

        # Check if username, email, or ID already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register"))

        if User.query.filter_by(id_number=id_number).first():
            flash("ID number already exists")
            return redirect(url_for("register"))

        # Create new user
        user = User(
            username=username,
            email=email,
            id_number=id_number,
            password_hash=generate_password_hash(password),
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        print_requests = PrintRequest.query.order_by(
            PrintRequest.timestamp.desc()
        ).all()
    else:
        print_requests = (
            PrintRequest.query.filter_by(user_id=current_user.id)
            .order_by(PrintRequest.timestamp.desc())
            .all()
        )
    return render_template("dashboard.html", print_requests=print_requests)


@app.cli.command("create-admin")
def create_admin():
    """Create an admin user"""
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    id_number = input("Enter admin ID number: ")
    password = input("Enter admin password: ")

    if User.query.filter_by(username=username).first():
        print("Username already exists")
        return

    if User.query.filter_by(email=email).first():
        print("Email already exists")
        return

    if User.query.filter_by(id_number=id_number).first():
        print("ID number already exists")
        return

    admin = User(
        username=username,
        email=email,
        id_number=id_number,
        password_hash=generate_password_hash(password),
        is_admin=True,
    )

    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
