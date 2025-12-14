from flask import Flask
import re
from .database.db import db
from flask_migrate import Migrate
from flask_login import LoginManager
from .models.models import Usuario 
from flask_mail import Mail

mail = Mail()

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

    return url  # fallback

def create_app():
    app = Flask(__name__)
    
    app.jinja_env.filters["youtube_id"] = youtube_id

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pimpeano@localhost:5432/liga'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'PimpeanO02'

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'views.login'  
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from .routes.views import views
    app.register_blueprint(views)
    
    
    
    #--------------------------------------
    #AUTOMATIZACION MAILS
    #--------------------------------------
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    # Cuenta real desde la cual se envían los correos
    app.config['MAIL_USERNAME'] = 'infoligainterprovincial@gmail.com'
    # Tu contraseña de aplicación recién creada
    app.config['MAIL_PASSWORD'] = 'qwle jhej bmnh epjl'
    # Remitente que verán los usuarios
    app.config['MAIL_DEFAULT_SENDER'] = 'Liga Interprovincial <infoligainterprovincial@gmail.com>'
    
    mail.init_app(app)





    return app


