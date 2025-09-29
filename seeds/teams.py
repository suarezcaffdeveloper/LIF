from app.models.models import Equipo
from app.database.db import db

def cargar_equipos():
    if not Equipo.query.first():
        equipos = [
            {"nombre": "Cafferatense", "localidad": "Cafferata"},
            {"nombre": "Centenario", "localidad": "San José de la Esquina"},
            {"nombre": "Alianza", "localidad": "Arteaga"},
            {"nombre": "Arteaga", "localidad": "Arteaga"},
            {"nombre": "Godeken", "localidad": "Godeken"},
            {"nombre": "Chañarense", "localidad": "Chañar Ladeado"},
            {"nombre": "Independiente", "localidad": "Chañar Ladeado"},
            {"nombre": "9 de julio", "localidad": "Beravebu"},
            {"nombre": "Deportivo", "localidad": "Beravebu"},
            {"nombre": "Belgrano", "localidad": "San José de la Esquina"},
            {"nombre": "Huracan", "localidad": "Los Quirquinchos"},
            {"nombre": "Federacion", "localidad": "Los Quirquinchos"}
        ]
        for equipo_data in equipos:
            equipo = Equipo(nombre=equipo_data["nombre"], localidad=equipo_data["localidad"])
            db.session.add(equipo)
        db.session.commit()
        print("✅ Equipos cargados correctamente.")
    else:
        print("ℹ️ Ya hay equipos cargados.")