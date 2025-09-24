# app/book_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from . import db
from .models import Book

bp = Blueprint("books", __name__)

def login_required_html(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'student_id' not in session:
            # redirect to login page; include next param so we return after login
            return redirect(url_for("main.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper



def _get_request_data():
    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()
    return data

# -------- Server-rendered pages (protected) --------
@bp.route("/page", methods=["GET"])
@login_required_html
def books_page():
    """HTML list of books (login required)"""
    books = Book.query.order_by(Book.added_at.desc()).all()
    return render_template("list_books.html", books=books)

@bp.route("/add", methods=["GET"])
@login_required_html
def add_book_page():
    """HTML form to add a book (login required)"""
    return render_template("add_book.html")

@bp.route("/add", methods=["POST"])
@login_required_html
def add_book_from_form():
    """
    Form POST endpoint for browser Add Book page.
    On success redirect to /books/page
    """
    data = _get_request_data()
    title = data.get("title")
    if not title:
        # you can show errors in template later; for now redirect back
        return redirect(url_for("books.add_book_page"))

    author = data.get("author")
    isbn = data.get("isbn")
    try:
        total_copies = int(data.get("total_copies", 1))
    except (TypeError, ValueError):
        total_copies = 1
    if total_copies < 1:
        total_copies = 1

    cover_url = data.get("cover_url")

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        total_copies=total_copies,
        available_copies=total_copies,
        cover_url=cover_url
    )

    try:
        db.session.add(book)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # ignoring duplicate ISBN for form flow — in future show message
    return redirect(url_for("books.books_page"))

@bp.route("/page/<int:book_id>", methods=["GET"])
@login_required_html
def book_detail_page(book_id):
    """HTML detail page for a single book (login required)"""
    b = Book.query.get(book_id)
    if not b:
        return render_template("book_not_found.html", book_id=book_id), 404
    return render_template("book_detail.html", book=b)

# -------- JSON API routes (unchanged) --------
@bp.route("/", methods=["POST"])
def add_book():
    data = _get_request_data()
    title = data.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400

    author = data.get("author")
    isbn = data.get("isbn")
    try:
        total_copies = int(data.get("total_copies", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "total_copies must be an integer"}), 400
    if total_copies < 1:
        return jsonify({"error": "total_copies must be >= 1"}), 400

    cover_url = data.get("cover_url")

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        total_copies=total_copies,
        available_copies=total_copies,
        cover_url=cover_url
    )

    try:
        db.session.add(book)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Integrity error (maybe duplicate isbn)"}), 409

    return jsonify({
        "message": "book created",
        "book": {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn,
            "total_copies": book.total_copies,
            "available_copies": book.available_copies,
            "cover_url": book.cover_url
        }
    }), 201

@bp.route("/", methods=["GET"])
def list_books():
    q = request.args.get("q")
    available = request.args.get("available")
    query = Book.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Book.title.ilike(like),
                Book.author.ilike(like),
                Book.isbn.ilike(like)
            )
        )
    if available and available.lower() in ("1", "true", "yes"):
        query = query.filter(Book.available_copies > 0)

    books = query.order_by(Book.added_at.desc()).all()
    out = []
    for b in books:
        out.append({
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "isbn": b.isbn,
            "total_copies": b.total_copies,
            "available_copies": b.available_copies,
            "cover_url": b.cover_url,
            "added_at": b.added_at.isoformat() if b.added_at else None
        })
    return jsonify(out), 200

@bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    b = Book.query.get(book_id)
    if not b:
        return jsonify({"error": "book not found"}), 404
    return jsonify({
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "isbn": b.isbn,
        "total_copies": b.total_copies,
        "available_copies": b.available_copies,
        "cover_url": b.cover_url,
        "added_at": b.added_at.isoformat() if b.added_at else None
    }), 200

@bp.route("/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    b = Book.query.get(book_id)
    if not b:
        return jsonify({"error": "book not found"}), 404

    data = _get_request_data()
    if "title" in data: b.title = data["title"]
    if "author" in data: b.author = data["author"]
    if "isbn" in data: b.isbn = data["isbn"]

    if "total_copies" in data:
        try:
            new_total = int(data["total_copies"])
        except (TypeError, ValueError):
            return jsonify({"error": "total_copies must be an integer"}), 400
        if new_total < 0:
            return jsonify({"error": "total_copies cannot be negative"}), 400
        delta = new_total - b.total_copies
        b.total_copies = new_total
        b.available_copies = max(0, b.available_copies + delta)

    if "cover_url" in data:
        b.cover_url = data["cover_url"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Integrity error (maybe duplicate isbn)"}), 409

    return jsonify({"message": "book updated", "book_id": b.id}), 200

@bp.route("/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    b = Book.query.get(book_id)
    if not b:
        return jsonify({"error": "book not found"}), 404

    db.session.delete(b)
    db.session.commit()
    return jsonify({"message": "book deleted", "book_id": book_id}), 200