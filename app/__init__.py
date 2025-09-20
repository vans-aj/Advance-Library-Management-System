# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # import models so they register with SQLAlchemy
    from . import models

    # import and register blueprints AFTER db is initialized
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    @app.route("/")
    def home():
        return "Factory pattern working!"

    return app