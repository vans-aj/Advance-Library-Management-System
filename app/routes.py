from flask import request, jsonify, Blueprint, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import Student

bp = Blueprint("main", __name__)

# ----- HTML Pages -----
@bp.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")

@bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

# ----- API Routes -----
@bp.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    roll_no = request.form.get("roll_no")
    password = request.form.get("password")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if Student.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    pw_hash = generate_password_hash(password)
    student = Student(name=name, email=email, roll_no=roll_no, password_hash=pw_hash)
    db.session.add(student)
    db.session.commit()

    return jsonify({"message": "signup successful", "student": {"id": student.id, "name": student.name, "email": student.email}}), 201

@bp.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    student = Student.query.filter_by(email=email).first()
    if not student or not check_password_hash(student.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({"message": "login successful", "student": {"id": student.id, "name": student.name, "email": student.email}}), 200