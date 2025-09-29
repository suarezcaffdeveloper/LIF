from app.models.models import Jugador, Equipo
from app.database.db import db

def cargar_jugadores():
    jugadores = [
        {"nombre": "Santiago", "apellido": "Suarez", "equipo": "Cafferatense", "categoria": "Primera"},
        {"nombre": "Juan", "apellido": "Martinez", "equipo": "Federacion", "categoria": "Primera"},
        {"nombre": "Marcos", "apellido": "Canigia", "equipo": "Arteaga", "categoria": "Primera"},
        {"nombre": "Jose", "apellido": "Lopez", "equipo": "Chañarense", "categoria": "Primera"},
        {"nombre": "Pedro", "apellido": "Rossi", "equipo": "Huracan", "categoria": "Primera"},
        {"nombre": "Julio", "apellido": "Brennan", "equipo": "Alianza", "categoria": "Primera"},
        {"nombre": "Mateo", "apellido": "Candiz", "equipo": "Independiente", "categoria": "Primera"},
        {"nombre": "Tiago", "apellido": "Lopez", "equipo": "Belgrano", "categoria": "Primera"},
        {"nombre": "Patricio", "apellido": "Mondonio", "equipo": "Chañarense", "categoria": "Primera"},
        {"nombre": "Andres", "apellido": "Mondino", "equipo": "Federacion", "categoria": "Primera"},
        {"nombre": "Francisco", "apellido": "Mancinelli", "equipo": "Centenario", "categoria": "Primera"},
        {"nombre": "Guillermo", "apellido": "Garay", "equipo": "9 de julio", "categoria": "Primera"},
        {"nombre": "Jose Martin", "apellido": "Pellegrino", "equipo": "Deportivo", "categoria": "Primera"},
        {"nombre": "Lautaro", "apellido": "Gomez Diaz", "equipo": "Godeken", "categoria": "Primera"},
    ]

    for jugador_data in jugadores:
        equipo = Equipo.query.filter_by(nombre=jugador_data["equipo"]).first()
        if not equipo:
            print(f"⚠️ Equipo '{jugador_data['equipo']}' no encontrado. Jugador no cargado.")
            continue

        # Verificar si el jugador ya existe
        jugador_existente = Jugador.query.filter_by(
            nombre=jugador_data["nombre"],
            apellido=jugador_data["apellido"],
            equipo_id=equipo.id,
            categoria=jugador_data["categoria"]
        ).first()

        if jugador_existente:
            print(f"ℹ️ Jugador {jugador_data['nombre']} {jugador_data['apellido']} ya existe. Saltado.")
            continue

        jugador = Jugador(
            nombre=jugador_data["nombre"],
            apellido=jugador_data["apellido"],
            equipo_id=equipo.id,
            categoria=jugador_data["categoria"]
        )
        db.session.add(jugador)

    db.session.commit()
    print("✅ Jugadores cargados correctamente.")