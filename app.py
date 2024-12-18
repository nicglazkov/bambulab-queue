from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    make_response,
)
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
ALLOWED_EXTENSIONS = {"stl", "gcode"}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Ensure upload directory exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)  # Made nullable
    id_number = db.Column(db.String(20), unique=True, nullable=True)  # Made nullable
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    print_requests = db.relationship("PrintRequest", backref="user", lazy=True)


class PrintFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    filepath = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'stl' or 'gcode'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    print_request_id = db.Column(
        db.Integer, db.ForeignKey("print_request.id"), nullable=False
    )


class PrintRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="pending")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    notes = db.Column(db.Text)
    files = db.relationship("PrintFile", backref="print_request", lazy=True)
    # Only populated for gcode files
    estimated_time = db.Column(db.Integer, nullable=True)
    material_type = db.Column(db.String(50), nullable=True)
    material_amount = db.Column(db.Float, nullable=True)
    layer_height = db.Column(db.Float, nullable=True)


def extract_gcode_info(filepath):
    """Extract print information from gcode file"""
    info = {
        "estimated_time": 0,
        "material_type": "Unknown",
        "material_amount": 0.0,
        "layer_height": 0.0,
    }

    try:
        with open(filepath, "r") as file:
            content = file.read()

            # Extract print time (looking for specific Bambu Lab format)
            time_match = re.search(
                r"estimated printing time \(normal mode\) = (\d+)m", content
            )
            if time_match:
                info["estimated_time"] = int(time_match.group(1))

            # Extract filament type
            material_match = re.search(r"filament_type = (.+)", content)
            if material_match:
                info["material_type"] = material_match.group(1)

            # Extract filament weight
            weight_match = re.search(r"total filament used \[g\] = ([\d.]+)", content)
            if weight_match:
                info["material_amount"] = float(weight_match.group(1))

            # Extract layer height
            layer_match = re.search(r"layer_height = ([\d.]+)", content)
            if layer_match:
                info["layer_height"] = float(layer_match.group(1))

    except Exception as e:
        print(f"Error parsing gcode: {e}")

    return info


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


def is_first_user():
    return User.query.first() is None


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    first_user = is_first_user()

    if request.method == "POST":
        username = request.form["username"]
        email = request.form.get("email")  # Using .get() to handle optional field
        id_number = request.form.get(
            "id_number"
        )  # Using .get() to handle optional field
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

        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))

        # Only check email uniqueness if an email was provided
        if email:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash("Invalid email format")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email already exists")
                return redirect(url_for("register"))

        # Only check ID number uniqueness if an ID was provided
        if id_number and User.query.filter_by(id_number=id_number).first():
            flash("ID number already exists")
            return redirect(url_for("register"))

        # Create new user
        user = User(
            username=username,
            email=email if email else None,  # Set to None if empty
            id_number=id_number if id_number else None,  # Set to None if empty
            password_hash=generate_password_hash(password),
            is_admin=first_user,
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html", first_user=first_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

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


@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit_print():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            file_type = filename.rsplit(".", 1)[1].lower()

            print_request = PrintRequest(
                user_id=current_user.id, notes=request.form.get("notes", "")
            )

            # Create the print file record
            print_file = PrintFile(
                filename=filename, filepath=filepath, file_type=file_type
            )

            # If it's a gcode file, extract additional information
            if file_type == "gcode":
                gcode_info = extract_gcode_info(filepath)
                print_request.estimated_time = gcode_info["estimated_time"]
                print_request.material_type = gcode_info["material_type"]
                print_request.material_amount = gcode_info["material_amount"]
                print_request.layer_height = gcode_info["layer_height"]

            db.session.add(print_request)
            print_request.files.append(print_file)
            db.session.commit()

            flash("Print request submitted successfully")
            return redirect(url_for("dashboard"))
        else:
            flash("Only .gcode and .stl files are allowed")
            return redirect(request.url)

    return render_template("submit.html")


@app.route("/approve/<int:request_id>")
@login_required
def approve_print(request_id):
    if not current_user.is_admin:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    print_request = PrintRequest.query.get_or_404(request_id)
    print_request.status = "approved"
    db.session.commit()
    flash("Print request approved")
    return redirect(url_for("dashboard"))


@app.route("/deny/<int:request_id>")
@login_required
def deny_print(request_id):
    if not current_user.is_admin:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    print_request = PrintRequest.query.get_or_404(request_id)
    print_request.status = "denied"
    db.session.commit()
    flash("Print request denied")
    return redirect(url_for("dashboard"))


@app.route("/file/download/<int:file_id>")
@login_required
def download_file(file_id):
    print_file = PrintFile.query.get_or_404(file_id)
    print_request = print_file.print_request

    if not current_user.is_admin and print_request.user_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    try:
        return send_file(
            print_file.filepath, as_attachment=True, download_name=print_file.filename
        )
    except Exception as e:
        flash(f"Error downloading file: {str(e)}")
        return redirect(url_for("view_request", request_id=print_request.id))


@app.route("/file/content/<int:file_id>")
@login_required
def get_file_content(file_id):
    print_file = PrintFile.query.get_or_404(file_id)
    print_request = print_file.print_request

    if not current_user.is_admin and print_request.user_id != current_user.id:
        return "Unauthorized", 403

    try:
        with open(
            print_file.filepath, "rb" if print_file.file_type == "stl" else "r"
        ) as f:
            content = f.read()
            if print_file.file_type == "stl":
                response = make_response(content)
                response.headers["Content-Type"] = "application/octet-stream"
            else:
                response = make_response(content)
                response.headers["Content-Type"] = "text/plain"
            return response
    except Exception as e:
        return f"Error reading file: {str(e)}", 500


@app.route("/gcode/download/<int:request_id>")
@login_required
def download_gcode(request_id):
    print_request = PrintRequest.query.get_or_404(request_id)
    if not current_user.is_admin and print_request.user_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    try:
        return send_file(
            print_request.filepath,
            as_attachment=True,
            download_name=print_request.filename,
        )
    except Exception as e:
        flash(f"Error downloading file: {str(e)}")
        return redirect(url_for("view_request", request_id=request_id))


@app.route("/gcode/view/<int:request_id>")
@login_required
def get_gcode(request_id):
    print_request = PrintRequest.query.get_or_404(request_id)
    if not current_user.is_admin and print_request.user_id != current_user.id:
        return "Unauthorized", 403

    try:
        with open(print_request.filepath, "r") as file:
            response = make_response(file.read())
            response.headers["Content-Type"] = "text/plain"
            return response
    except Exception as e:
        return f"Error reading file: {str(e)}", 500


@app.route("/request/<int:request_id>")
@login_required
def view_request(request_id):
    print_request = PrintRequest.query.get_or_404(request_id)
    if not current_user.is_admin and print_request.user_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    # Read first few lines of gcode for preview
    try:
        with open(print_request.filepath, "r") as file:
            gcode_preview = "".join(file.readlines()[:100])  # First 100 lines
    except Exception as e:
        gcode_preview = f"Unable to load gcode preview: {str(e)}"

    return render_template(
        "view_request.html", print_request=print_request, gcode_preview=gcode_preview
    )


@app.route("/manage/users")
@login_required
def manage_users():
    if not current_user.is_admin:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    users = User.query.all()
    return render_template("manage_users.html", users=users)


@app.route("/manage/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # Prevent admin from removing their own admin status
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"Admin status updated for {user.username}")

    return redirect(url_for("manage_users"))


@app.route("/manage/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("Unauthorized")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # Prevent admin from deleting themselves
        # Delete associated print requests and files
        for print_request in user.print_requests:
            try:
                os.remove(print_request.filepath)
            except:
                pass

        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted")

    return redirect(url_for("manage_users"))


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
    app.run(debug=True, host="0.0.0.0", port=5000)
