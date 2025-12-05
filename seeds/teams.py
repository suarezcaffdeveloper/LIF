# app/services/teams.py
from app.models.models import Equipo
from app.database.db import db

def crear_equipo(nombre, localidad, escudo_url=None):
    """
    Crea y guarda un nuevo equipo en la base de datos.
    Verifica que no exista un equipo con el mismo nombre.
    Devuelve (True, equipo) si se creó o (False, mensaje) si hay error.
    """
    if not nombre:
        return False, "Debe ingresar un nombre de equipo."

    # Validar duplicados por nombre (ignora mayúsculas)
    existe = Equipo.query.filter(Equipo.nombre.ilike(nombre)).first()
    if existe:
        return False, f"Ya existe un equipo con el nombre '{nombre}'."

    equipo = Equipo(
        nombre=nombre.strip(),
        localidad=localidad.strip() if localidad else None,
    )

    # Asignar escudo si existe esa columna
    if escudo_url:
        if hasattr(equipo, 'escudo'):
            equipo.escudo = escudo_url.strip()
        elif hasattr(equipo, 'url_escudo'):
            equipo.url_escudo = escudo_url.strip()
        elif hasattr(equipo, 'logo_url'):
            equipo.logo_url = escudo_url.strip()

    try:
        db.session.add(equipo)
        db.session.commit()
        return True, equipo
    except Exception as e:
        db.session.rollback()
        return False, f"Error al guardar en la base de datos: {str(e)}"
