from flask import Flask, render_template , redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("SECRET_KEY") or "dev-secret"

    # initialize extensions with the app
    db.init_app(app)

    # import models so SQLAlchemy knows about them
    from . import models

    # import and register blueprints AFTER db/init and models import
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .book_routes import bp as books_bp
    app.register_blueprint(books_bp, url_prefix="/books")

    # @app.route("/")
    # def home():
    #     return render_template("index.html")
    return app  