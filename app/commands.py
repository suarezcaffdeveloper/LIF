from flask.cli import with_appcontext
import click
from datetime import datetime
from werkzeug.security import generate_password_hash

from app.database.db import db
from app.models.models import Usuario


@click.command("create-admin")
@with_appcontext
def create_admin():
    email = "admin@liga.com"
    password = "admin123"  # luego la cambiás
    nombre = "Administrador"

    if Usuario.query.filter_by(email=email).first():
        click.echo("❌ El usuario admin ya existe")
        return

    admin = Usuario(
        nombre_completo=nombre,
        email=email,
        contraseña=generate_password_hash(password),
        rol="admin",
        fecha_registro=datetime.utcnow()
    )

    db.session.add(admin)
    db.session.commit()

    click.echo("✅ Usuario admin creado")
