# app/models.py
from datetime import datetime
from . import db

class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=True)   # optional college roll
    password_hash = db.Column(db.String(200), nullable=False)        # store hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship: student's transactions (borrows/returns)
    transactions = db.relationship("Transaction", back_populates="student", lazy="dynamic")

    def __repr__(self):
        return f"<Student {self.id} {self.email}>"

class Book(db.Model):
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(200), nullable=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    total_copies = db.Column(db.Integer, default=1, nullable=False)
    available_copies = db.Column(db.Integer, default=1, nullable=False)
    cover_url = db.Column(db.String(500), nullable=True)  # store path/URL, not blob
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", back_populates="book", lazy="dynamic")

    def __repr__(self):
        return f"<Book {self.id} {self.title}>"

class Transaction(db.Model):
    """
    A borrow / return record.
    status: 'borrowed' or 'returned'
    fine_amount: numeric for fines (if any)
    """
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)

    borrowed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    returned_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum("borrowed", "returned", name="transaction_status"), default="borrowed", nullable=False)
    fine_amount = db.Column(db.Numeric(8,2), default=0.00, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    student = db.relationship("Student", back_populates="transactions")
    book = db.relationship("Book", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.id} student={self.student_id} book={self.book_id} status={self.status}>"

# Optional Seat model (uncomment if you want now or later)
# class Seat(db.Model):
#     __tablename__ = "seat"
#     id = db.Column(db.Integer, primary_key=True)
#     seat_no = db.Column(db.String(50), unique=True, nullable=False)
#     location = db.Column(db.String(200), nullable=True)   # e.g., "1st floor, A block"
#     is_booked = db.Column(db.Boolean, default=False, nullable=False)
#     booked_by = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=True)
#     booked_at = db.Column(db.DateTime, nullable=True)
#
#     # optional relationship to student if you need it:
#     # student = db.relationship("Student", backref="seat", uselist=False)
#
#     def __repr__(self):
#         return f"<Seat {self.seat_no} booked={self.is_booked}>"