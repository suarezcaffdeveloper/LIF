from flask import Flask
import re
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from app.commands import create_admin
import cloudinary
import cloudinary.uploader
import cloudinary.api

from .database.db import db
from .models.models import Usuario

mail = Mail()

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida")

def youtube_id(url):
    """
    Extrae el ID de un video de YouTube sin importar el formato.
    """
    patrones = [
        r"youtu\.be/([^?&]+)",
        r"youtube\.com/watch\?v=([^?&]+)",
        r"youtube\.com/embed/([^?&]+)",
        r"youtube\.com/shorts/([^?&]+)"
    ]

    for p in patrones:
        match = re.search(p, url)
        if match:
            return match.group(1)

    return url


def create_app():
    app = Flask(__name__)
    app.cli.add_command(create_admin)
    # -----------------------
    # CONFIG GENERAL
    # -----------------------
    app.jinja_env.filters["youtube_id"] = youtube_id

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    # -----------------------
    # DATABASE
    # -----------------------
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está definida")

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)

    # -----------------------
    # LOGIN
    # -----------------------
    login_manager = LoginManager()
    login_manager.login_view = "views.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # -----------------------
    # MAIL (usar variables de entorno)
    # -----------------------
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        "Liga Interprovincial <infoligainterprovincial@gmail.com>"
    )

    mail.init_app(app)
    
    # -----------------------
    # CLOUDINARY CONFIG
    # -----------------------
    app.config["CLOUDINARY_CLOUD_NAME"] = os.getenv("CLOUDINARY_CLOUD_NAME")
    app.config["CLOUDINARY_API_KEY"] = os.getenv("CLOUDINARY_API_KEY")
    app.config["CLOUDINARY_API_SECRET"] = os.getenv("CLOUDINARY_API_SECRET")
    
    cloudinary.config(
        cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
        api_key=app.config.get("CLOUDINARY_API_KEY"),
        api_secret=app.config.get("CLOUDINARY_API_SECRET"),
        secure=True
    )

    # -----------------------
    # BLUEPRINTS
    # -----------------------
    from .routes.views import views
    app.register_blueprint(views)

    return app


# 👇 ESTO ES CLAVE PARA GUNICORN
app = create_app()

