# app/routes.py
from flask import request, jsonify, Blueprint, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import Student
from functools import wraps

bp = Blueprint("main", __name__)

@bp.route("/", methods=["GET"])
def index_page():
    """
    Landing page. If user already logged in (student_id in session),
    redirect to books page. Otherwise render index.html.
    """
    if session.get("student_id"):
        # user already logged in -> go to books list
        return redirect(url_for("books.books_page"))
    # not logged in -> show landing page
    return render_template("index.html")

@bp.route("/login", methods=["GET"])
def login_page():
    # render the login form (POST handler can remain separate)
    return render_template("login.html")

@bp.route("/signup", methods=["GET"])
def signup_page():
    # render the signup form (POST handler can remain separate)
    return render_template("signup.html")

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

    # optionally log the user in right after signup:
    session.clear()
    session['student_id'] = student.id

    return jsonify({"message": "signup successful", "student": {"id": student.id, "name": student.name, "email": student.email}}), 201

@bp.route("/login", methods=["POST"])
def login():
    # Accept form POST from HTML page
    email = request.form.get("email")
    password = request.form.get("password")
    # support JSON login too
    if not email or not password:
        data = request.get_json(silent=True) or {}
        email = email or data.get("email")
        password = password or data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    student = Student.query.filter_by(email=email).first()
    if not student or not check_password_hash(student.password_hash, password):
        # if request from browser form, redirect back to login page (optional)
        if request.content_type and "application/json" not in request.content_type:
            return redirect(url_for("main.login_page"))
        return jsonify({"error": "invalid credentials"}), 401

    # login successful -> set session
    session.clear()
    session['student_id'] = student.id
    session.permanent = True  # optional; set SESSION_PERMANENT etc.

    # handle "next" param (redirect after login)
    next_url = request.args.get("next") or request.form.get("next")
    if next_url:
        return redirect(next_url)

    # if JSON login, return JSON
    if request.content_type and "application/json" in request.content_type:
        return jsonify({"message": "login successful", "student": {"id": student.id, "name": student.name, "email": student.email}}), 200

    # otherwise redirect to books page
    return redirect(url_for("books.books_page"))

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("main.index_page"))  # go back to landing page