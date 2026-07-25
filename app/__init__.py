from flask import Flask, request, session
import re
import os
import sqlalchemy as sa
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_login import LoginManager, user_logged_in, user_logged_out
from flask_mail import Mail
from app.commands import create_admin, reset_demo_db
import cloudinary
import cloudinary.uploader
import cloudinary.api

from .database.db import db, DEMO_BIND_KEY, DEMO_ROLE, is_demo_mode, set_demo_mode
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


def _normalizar_db_url(nombre_var, valor):
    """Limpia errores comunes de copy/paste (comillas, espacios) al setear una
    URL de base de datos como variable de entorno, normaliza el esquema
    'postgres://' -> 'postgresql://', y valida que sea parseable ANTES de
    llegar a db.init_app(), para que un error de configuración se vea claro
    (qué variable y qué valor) en vez de un stack trace de SQLAlchemy.
    """
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ("'", '"'):
        valor = valor[1:-1].strip()

    if valor.startswith("postgres://"):
        valor = valor.replace("postgres://", "postgresql://", 1)

    try:
        sa.engine.make_url(valor)
    except sa.exc.ArgumentError as e:
        pistas = ""
        if " " in valor or "\n" in valor:
            pistas = " (parece tener espacios o saltos de línea de más)"
        elif valor.count("://") == 0:
            pistas = " (falta el esquema, ej. 'postgresql://...')"
        raise RuntimeError(
            f"{nombre_var} no es una URL de base de datos válida{pistas}: {valor!r}"
        ) from e

    return valor


def create_app():
    app = Flask(__name__)
    app.cli.add_command(create_admin)
    app.cli.add_command(reset_demo_db)
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

    DATABASE_URL = _normalizar_db_url("DATABASE_URL", DATABASE_URL)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # -----------------------
    # DATABASE DEMO (para reclutadores)
    # -----------------------
    # Base de datos secundaria, aislada de la real, a la que se desvían todas
    # las consultas cuando inicia sesión un usuario con rol 'demo'. Si no se
    # define DEMO_DATABASE_URL (por ejemplo, un Postgres dedicado en producción),
    # se usa un sqlite local dentro de la carpeta instance/ para que funcione
    # sin configuración adicional en desarrollo.
    DEMO_DATABASE_URL = os.environ.get("DEMO_DATABASE_URL")
    if not DEMO_DATABASE_URL:
        os.makedirs(app.instance_path, exist_ok=True)
        DEMO_DATABASE_URL = "sqlite:///" + os.path.join(app.instance_path, "demo.db")
    else:
        DEMO_DATABASE_URL = _normalizar_db_url("DEMO_DATABASE_URL", DEMO_DATABASE_URL)

    app.config["SQLALCHEMY_BINDS"] = {DEMO_BIND_KEY: DEMO_DATABASE_URL}

    db.init_app(app)
    Migrate(app, db)

    # -----------------------
    # RUTEO A BASE DE DATOS DEMO
    # -----------------------
    # Un usuario con rol 'demo' debe quedar aislado en la base demo durante
    # toda su sesión, usando el mismo `db.session`/`Modelo.query` de siempre
    # en las rutas existentes (ver DemoRoutingSession en database/db.py).
    #
    # El desafío es el intento de login en sí: en ese momento todavía no hay
    # un current_user autenticado que nos diga "soy demo", así que la ruta
    # /login no sabría en qué base buscar el email. Para resolverlo sin tocar
    # el código de la ruta de login:
    #   1) Antes de cada request restauramos el modo demo desde un marcador
    #      firmado en la sesión de Flask (session['_demo_mode']), ANTES de que
    #      Flask-Login intente cargar al current_user (por eso este
    #      before_request se registra antes de login_manager.init_app).
    #   2) Si el request es justo un POST a /login, primero "espiamos" (sin
    #      loguear a nadie) si el email enviado corresponde a una cuenta con
    #      rol 'demo' en la base demo, y si es así activamos el modo demo
    #      para ese request: la consulta que ya hace login() por su cuenta
    #      queda automáticamente apuntando a la base demo.
    #   3) Cuando login_user()/logout_user() se ejecutan dentro de login()/
    #      logout() (código ya existente, sin tocar), las señales de
    #      Flask-Login nos avisan para grabar o borrar ese marcador.
    def _es_cuenta_demo(usuario):
        # rol == 'demo' cubre la cuenta pública de solo-lectura del sitio;
        # es_demo permite además sandboxes con otros roles (p. ej. un
        # 'administrador' de demo) sin perder los permisos de ese rol.
        return getattr(usuario, "rol", None) == DEMO_ROLE or bool(getattr(usuario, "es_demo", False))

    def _email_es_de_demo(email):
        if not email:
            return False
        estaba_en_demo = is_demo_mode()
        set_demo_mode(True)
        try:
            # Traemos sólo columnas (no la entidad completa) para no dejar un
            # Usuario de la base demo cacheado en el identity map de la sesión:
            # como real y demo comparten la misma clase/PKs, un objeto completo
            # ahí podría "filtrarse" y devolverse por error en una consulta
            # posterior contra la base real con el mismo id.
            fila = (
                db.session.query(Usuario.rol, Usuario.es_demo)
                .filter_by(email=email)
                .first()
            )
            return fila is not None and (fila.rol == DEMO_ROLE or bool(fila.es_demo))
        finally:
            set_demo_mode(estaba_en_demo)

    @app.before_request
    def _sincronizar_modo_demo():
        if request.method == "POST" and request.endpoint == "views.login":
            set_demo_mode(_email_es_de_demo(request.form.get("email")))
        else:
            set_demo_mode(session.get("_demo_mode", False))

    @app.context_processor
    def _inject_demo_mode():
        return {"demo_mode": is_demo_mode()}

    @user_logged_in.connect_via(app)
    def _marcar_sesion_demo(sender, user):
        session["_demo_mode"] = _es_cuenta_demo(user)

    @user_logged_out.connect_via(app)
    def _limpiar_sesion_demo(sender, user):
        session.pop("_demo_mode", None)

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

