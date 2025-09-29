from app.models.models import TablaPosiciones, Equipo, Partido
from app.database.db import db

def cargar_puntajes():
    TablaPosiciones.query.delete()
    db.session.commit()

    equipos = Equipo.query.all()

    for equipo in equipos:
        partidos_local = Partido.query.filter_by(equipo_local_id=equipo.id, jugado=True).all()
        partidos_visitante = Partido.query.filter_by(equipo_visitante_id=equipo.id, jugado=True).all()
        partidos = partidos_local + partidos_visitante

        pj = pg = pe = pp = gf = gc = puntos = 0

        for partido in partidos:
            if partido.equipo_local_id == equipo.id:
                gf += partido.goles_local
                gc += partido.goles_visitante
                if partido.goles_local > partido.goles_visitante:
                    pg += 1
                    puntos += 3
                elif partido.goles_local == partido.goles_visitante:
                    pe += 1
                    puntos += 1
                else:
                    pp += 1
            else: 
                gf += partido.goles_visitante
                gc += partido.goles_local
                if partido.goles_visitante > partido.goles_local:
                    pg += 1
                    puntos += 3
                elif partido.goles_visitante == partido.goles_local:
                    pe += 1
                    puntos += 1
                else:
                    pp += 1

        pj = pg + pe + pp
        dif = gf - gc

        fila = TablaPosiciones(
            id_equipo=equipo.id,
            nombre_equipo=equipo.nombre,
            partidos_jugados=pj,
            partidos_ganados=pg,
            partidos_empatados=pe,
            partidos_perdidos=pp,
            goles_a_favor=gf,
            goles_en_contra=gc,
            cantidad_puntos=puntos,
            diferencia_gol=dif
        )
        db.session.add(fila)

    db.session.commit()
    print("✅ Tabla de posiciones generada correctamente.")