from flask import Flask
from .database.db import db
from flask_migrate import Migrate
from flask_login import LoginManager
from .models.models import Usuario 

def create_app():
    app = Flask(__name__)

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

    return app

