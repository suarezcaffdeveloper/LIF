from app.database.db import db
from app.models.models import Equipo, Partido, Jugador
from datetime import date, timedelta

def generar_fixtures():
    fecha_inicio = date(2025, 5, 4)
    dias_entre_fechas = 7

    divisiones = {
        "Mayores": ["Primera", "Reserva"],
        "Inferiores": ["Quinta", "Sexta", "Septima"]
    }

    # -------------- OPCIONAL: eliminar todos los partidos previos --------------
    #print("🧹 Eliminando partidos existentes...")
    #db.session.query(Partido).delete()
    #db.session.commit()
    #print("✅ Partidos anteriores eliminados.\n")

    for nombre_division, categorias in divisiones.items():
        # Obtener equipos que tengan jugadores en alguna de las categorías del grupo
        equipos = (
            db.session.query(Equipo)
            .join(Jugador)
            .filter(Jugador.categoria.in_(categorias))
            .distinct()
            .order_by(Equipo.id)
            .all()
        )

        if len(equipos) < 2:
            print(f"⚠️ No hay suficientes equipos en {nombre_division}. Se saltea.")
            continue

        equipos_ids = [e.id for e in equipos]

        # Si la cantidad es impar, agregamos un "bye" (None)
        if len(equipos_ids) % 2 != 0:
            equipos_ids.append(None)

        # Generar emparejamientos round-robin UNA vez por división
        teams = equipos_ids.copy()
        n = len(teams)
        rondas = []
        for _ in range(n - 1):
            pares = []
            for i in range(n // 2):
                a = teams[i]
                b = teams[n - 1 - i]
                pares.append((a, b))
            rondas.append(pares)
            # rotación standard: mantener el primero fijo
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        print(f"📅 División {nombre_division}: {len(equipos)} equipos -> {len(rondas)} jornadas generadas (base).")

        # Para cada categoría del grupo crear los partidos (si no existen ya)
        for categoria in categorias:
            existe = db.session.query(Partido).filter(Partido.categoria == categoria).first()
            if existe:
                print(f"⚠️ Ya existen partidos para {categoria}, se omiten.")
                continue

            partidos_creados = 0
            for idx_jornada, pares in enumerate(rondas, start=1):
                fecha = fecha_inicio + timedelta(days=(idx_jornada - 1) * dias_entre_fechas)
                for local, visitante in pares:
                    # saltar enfrentamientos con 'bye'
                    if local is None or visitante is None:
                        continue
                    partido = Partido(
                        fecha_partido=fecha,
                        jornada=idx_jornada,
                        categoria=categoria,
                        equipo_local_id=local,
                        equipo_visitante_id=visitante,
                        goles_local=0,
                        goles_visitante=0,
                        jugado=False
                    )
                    db.session.add(partido)
                    partidos_creados += 1

            db.session.commit()
            print(f"  ✅ Fixture creado para {categoria}: {len(rondas)} jornadas, {partidos_creados} partidos.")

    print("🎯 Fixtures generados.")