from app.models.models import EstadoJugadorPartido, Jugador, Partido
from app.database.db import db

def cargar_goleadores():
    partidos_jugados = Partido.query.filter_by(jugado=True).all()

    for partido in partidos_jugados:
        jugadores_local = Jugador.query.filter_by(equipo_id=partido.equipo_local_id, categoria=partido.categoria).all()
        jugadores_visitante = Jugador.query.filter_by(equipo_id=partido.equipo_visitante_id, categoria=partido.categoria).all()

        jugadores = jugadores_local + jugadores_visitante

        for jugador in jugadores:
            existente = EstadoJugadorPartido.query.filter_by(
                id_jugador=jugador.id,
                id_partido=partido.id
            ).first()

            if not existente:
                nuevo_estado = EstadoJugadorPartido(
                    id_jugador=jugador.id,
                    id_partido=partido.id,
                    cant_goles=0,
                    tarjetas_amarillas=0,
                    tarjetas_rojas=0
                )
                db.session.add(nuevo_estado)

    db.session.commit()
    print("Estad√≠sticas de jugadores inicializadas para los partidos jugados.")

    

