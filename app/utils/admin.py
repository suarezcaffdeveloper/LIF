from app.database.db import db
from app.models.models import Club, Temporada, Torneo, Equipo, Jugador
from datetime import datetime

def cargar_datos():
    # ----- Clubs -----
    clubs = [
        Club(nombre="Club A", localidad="Ciudad A", escudo_url=None),
        Club(nombre="Club B", localidad="Ciudad B", escudo_url=None),
    ]
    db.session.add_all(clubs)
    
    # ----- Temporadas -----
    temporada = Temporada(nombre="2025", activa=True)
    db.session.add(temporada)
    
    # ----- Torneos -----
    torneo = Torneo(nombre="Liga 2025", temporada_id=1)  # ajustá el id si lo necesitás
    db.session.add(torneo)
    
    # ----- Equipos -----
    equipo_a = Equipo(club_id=1, categoria="Primera")
    equipo_b = Equipo(club_id=2, categoria="Primera")
    db.session.add_all([equipo_a, equipo_b])
    
    # ----- Jugadores -----
    jugador = Jugador(numero_carnet=1, nombre="Juan", apellido="Pérez", club_id=1, creado_en=datetime.utcnow())
    db.session.add(jugador)
    
    # ----- Confirmar -----
    db.session.commit()
    print("Datos iniciales cargados correctamente.")