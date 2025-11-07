import json
from app.database.db import db
from app.models.models import TablaPosiciones

def cargar_datos_tabla_posiciones(ruta_json="app/data/datos_tabla_posiciones.json"):
    TablaPosiciones.query.delete()
    db.session.commit()

    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    for item in datos:
        fila = TablaPosiciones(
            id_equipo=item["id_equipo"],
            nombre_equipo=item["nombre_equipo"],
            categoria=item["categoria"],
            partidos_jugados=item["partidos_jugados"],
            partidos_ganados=item["partidos_ganados"],
            partidos_empatados=item["partidos_empatados"],
            partidos_perdidos=item["partidos_perdidos"],
            goles_a_favor=item["goles_a_favor"],
            goles_en_contra=item["goles_en_contra"],
            cantidad_puntos=item["cantidad_puntos"],
            diferencia_gol=item["diferencia_gol"]
        )
        db.session.add(fila)

    db.session.commit()
    print("✅ Datos de prueba cargados correctamente en tabla_posiciones (reemplazando anteriores)")

