from app.database.db import db
from app.models.models import Partido, Jugador, EstadoJugadorPartido
import json

def cargar_eventos_jugadores_desde_json(ruta_json="app/data/datos_partidos.json"):
    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    for registro in datos:
        partido = Partido.query.get(registro["id_partido"])
        if not partido:
            print(f"⚠️ Partido {registro['id_partido']} no encontrado. Se omite.")
            continue

        jugadores_validos = Jugador.query.filter(
            Jugador.categoria == partido.categoria,
            Jugador.equipo_id.in_([partido.equipo_local_id, partido.equipo_visitante_id])
        ).all()
        ids_validos = {j.id for j in jugadores_validos}

        for evento in registro["eventos"]:
            if evento["id_jugador"] not in ids_validos:
                print(f"🚫 Jugador {evento['id_jugador']} no pertenece al partido {partido.id}. Se omite.")
                continue

            estado = EstadoJugadorPartido.query.filter_by(
                id_jugador=evento["id_jugador"],
                id_partido=partido.id
            ).first()

            if estado:
                estado.cant_goles = evento["goles"]
                estado.tarjetas_amarillas = evento["amarillas"]
                estado.tarjetas_rojas = evento["rojas"]
            else:
                nuevo_estado = EstadoJugadorPartido(
                    id_jugador=evento["id_jugador"],
                    id_partido=partido.id,
                    cant_goles=evento["goles"],
                    tarjetas_amarillas=evento["amarillas"],
                    tarjetas_rojas=evento["rojas"]
                )
                db.session.add(nuevo_estado)

    db.session.commit()
    print("✅ Eventos de jugadores cargados correctamente desde JSON.")


def cargar_resultados_partidos_desde_json(ruta_json="app/data/resultados_partidos.json"):
    with open(ruta_json, "r", encoding="utf-8") as f:
        resultados = json.load(f)

    for item in resultados:
        partido = Partido.query.get(item["id_partido"])
        if not partido:
            print(f"⚠️ Partido {item['id_partido']} no encontrado. Se omite.")
            continue

        partido.goles_local = item["goles_local"]
        partido.goles_visitante = item["goles_visitante"]
        partido.jugado = True  # ✅ Marcamos el partido como jugado

        db.session.add(partido)

    db.session.commit()
    print("✅ Resultados de partidos cargados correctamente desde JSON.")

