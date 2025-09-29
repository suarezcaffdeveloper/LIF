from app.database.db import db
from app.models.models import Equipo, Partido, Jugador
from datetime import date, timedelta
import random

def generar_fixtures():
    #Partido.query.delete()
    #db.session.commit()
    #print("⚠️ Partidos anteriores eliminados.")

    categorias = db.session.query(Jugador.categoria).distinct().all()
    categorias = [c[0] for c in categorias]

    fecha_inicio = date(2025, 5, 4)
    dias_entre_fechas = 7

    for categoria in categorias:
        equipos_categoria = (
            db.session.query(Equipo)
            .join(Jugador)
            .filter(Jugador.categoria == categoria)
            .distinct()
            .all()
        )

        if len(equipos_categoria) < 2:
            print(f"⚠️ No hay suficientes equipos para la categoría {categoria}")
            continue

        equipos_ids = [e.id for e in equipos_categoria]

        if len(equipos_ids) % 2 != 0:
            equipos_ids.append(None)

        n = len(equipos_ids)
        rondas_totales = n - 1
        mitad = n // 2

        equipos_fijos = equipos_ids[0]
        rotables = equipos_ids[1:]

        for jornada in range(1, rondas_totales + 1):
            ronda = []

            izquierda = [equipos_fijos] + rotables[:mitad - 1]
            derecha = rotables[mitad - 1:][::-1]

            for local, visitante in zip(izquierda, derecha):
                if local is not None and visitante is not None:
                    partido = Partido(
                        fecha_partido=fecha_inicio + timedelta(days=(jornada - 1) * dias_entre_fechas),
                        jornada=jornada,
                        categoria=categoria,
                        equipo_local_id=local,
                        equipo_visitante_id=visitante,
                        goles_local=0,
                        goles_visitante=0,
                        jugado=False
                    )
                    db.session.add(partido)

            rotables = rotables[-1:] + rotables[:-1]

    db.session.commit()
    print("✅ Fixture generado y guardado en la base de datos.")


