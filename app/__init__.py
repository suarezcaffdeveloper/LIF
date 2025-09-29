from flask import Flask
from .database.db import db
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pimpeano@localhost:5432/liga'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'PimpeanO02'
    
    db.init_app(app)
    Migrate(app, db)

    from .models import models

    from .routes.views import views
    app.register_blueprint(views)
    
    return app

