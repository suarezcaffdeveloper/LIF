# app/services/jugadores.py
from app.models.models import Jugador, Equipo
from app.database.db import db

def crear_jugador(nombre, apellido, equipo_nombre, categoria):
    """
    Crea y guarda un nuevo jugador en la base de datos.
    Valida duplicados por nombre, apellido, equipo y categoría.
    """

    if not (nombre and apellido and equipo_nombre and categoria):
        return False, "Todos los campos son obligatorios."

    # Buscar el equipo por nombre
    equipo = Equipo.query.filter(Equipo.nombre.ilike(equipo_nombre)).first()
    if not equipo:
        return False, f"El equipo '{equipo_nombre}' no existe en la base de datos."

    # Verificar si ya existe ese jugador en ese equipo y categoría
    jugador_existente = Jugador.query.filter_by(
        nombre=nombre.strip(),
        apellido=apellido.strip(),
        equipo_id=equipo.id,
        categoria=categoria
    ).first()

    if jugador_existente:
        return False, f"El jugador {nombre} {apellido} ya está registrado en {equipo_nombre} ({categoria})."

    jugador = Jugador(
        nombre=nombre.strip(),
        apellido=apellido.strip(),
        equipo_id=equipo.id,
        categoria=categoria.strip()
    )

    try:
        db.session.add(jugador)
        db.session.commit()
        return True, jugador
    except Exception as e:
        db.session.rollback()
        return False, f"Error al guardar el jugador: {str(e)}"
