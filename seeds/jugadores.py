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
        {"nombre": "Tomás", "apellido": "Benítez", "equipo": "Cafferatense", "categoria": "Reserva"},
        {"nombre": "Ezequiel", "apellido": "Ramos", "equipo": "Cafferatense", "categoria": "Reserva"},
        {"nombre": "Lucas", "apellido": "Martínez", "equipo": "Cafferatense", "categoria": "Reserva"},

        {"nombre": "Matías", "apellido": "Gómez", "equipo": "Cafferatense", "categoria": "Quinta"},
        {"nombre": "Nicolás", "apellido": "Pereyra", "equipo": "Cafferatense", "categoria": "Quinta"},
        {"nombre": "Agustín", "apellido": "Vega", "equipo": "Cafferatense", "categoria": "Quinta"},

        {"nombre": "Facundo", "apellido": "Silva", "equipo": "Cafferatense", "categoria": "Sexta"},
        {"nombre": "Emiliano", "apellido": "Toledo", "equipo": "Cafferatense", "categoria": "Sexta"},
        {"nombre": "Bruno", "apellido": "Carrizo", "equipo": "Cafferatense", "categoria": "Sexta"},

        {"nombre": "Santiago", "apellido": "Reynoso", "equipo": "Cafferatense", "categoria": "Septima"},
        {"nombre": "Franco", "apellido": "Leiva", "equipo": "Cafferatense", "categoria": "Septima"},
        {"nombre": "Dylan", "apellido": "Ferreyra", "equipo": "Cafferatense", "categoria": "Septima"},

        {"nombre": "Lautaro", "apellido": "Zalazar", "equipo": "Centenario", "categoria": "Reserva"},
        {"nombre": "Matheo", "apellido": "Domínguez", "equipo": "Centenario", "categoria": "Reserva"},
        {"nombre": "Iván", "apellido": "Correa", "equipo": "Centenario", "categoria": "Reserva"},

        {"nombre": "Axel", "apellido": "Quiroga", "equipo": "Centenario", "categoria": "Quinta"},
        {"nombre": "Cristian", "apellido": "Benítez", "equipo": "Centenario", "categoria": "Quinta"},
        {"nombre": "Tomás", "apellido": "Lucero", "equipo": "Centenario", "categoria": "Quinta"},

        {"nombre": "Julián", "apellido": "Moreno", "equipo": "Centenario", "categoria": "Sexta"},
        {"nombre": "Simón", "apellido": "García", "equipo": "Centenario", "categoria": "Sexta"},
        {"nombre": "Alan", "apellido": "Roldán", "equipo": "Centenario", "categoria": "Sexta"},

        {"nombre": "Enzo", "apellido": "Páez", "equipo": "Centenario", "categoria": "Septima"},
        {"nombre": "Thiago", "apellido": "Molina", "equipo": "Centenario", "categoria": "Septima"},
        {"nombre": "Bautista", "apellido": "Campos", "equipo": "Centenario", "categoria": "Septima"},

        {"nombre": "Ramiro", "apellido": "Sosa", "equipo": "Alianza", "categoria": "Reserva"},
        {"nombre": "Luciano", "apellido": "Gaitán", "equipo": "Alianza", "categoria": "Reserva"},
        {"nombre": "Matías", "apellido": "Bermúdez", "equipo": "Alianza", "categoria": "Reserva"},

        {"nombre": "Franco", "apellido": "Medina", "equipo": "Alianza", "categoria": "Quinta"},
        {"nombre": "Emanuel", "apellido": "Giménez", "equipo": "Alianza", "categoria": "Quinta"},
        {"nombre": "Lucio", "apellido": "Varela", "equipo": "Alianza", "categoria": "Quinta"},

        {"nombre": "Kevin", "apellido": "Romero", "equipo": "Alianza", "categoria": "Sexta"},
        {"nombre": "Máximo", "apellido": "Ríos", "equipo": "Alianza", "categoria": "Sexta"},
        {"nombre": "Nahuel", "apellido": "Ortiz", "equipo": "Alianza", "categoria": "Sexta"},

        {"nombre": "Bruno", "apellido": "Sánchez", "equipo": "Alianza", "categoria": "Septima"},
        {"nombre": "Tobías", "apellido": "Ojeda", "equipo": "Alianza", "categoria": "Septima"},
        {"nombre": "Ian", "apellido": "Gallardo", "equipo": "Alianza", "categoria": "Septima"},

        {"nombre": "Leandro", "apellido": "Vega", "equipo": "Arteaga", "categoria": "Reserva"},
        {"nombre": "Ezequiel", "apellido": "Rossi", "equipo": "Arteaga", "categoria": "Reserva"},
        {"nombre": "Cristian", "apellido": "Reyes", "equipo": "Arteaga", "categoria": "Reserva"},

        {"nombre": "Álvaro", "apellido": "Montoya", "equipo": "Arteaga", "categoria": "Quinta"},
        {"nombre": "Dylan", "apellido": "Maidana", "equipo": "Arteaga", "categoria": "Quinta"},
        {"nombre": "Lautaro", "apellido": "Gómez", "equipo": "Arteaga", "categoria": "Quinta"},

        {"nombre": "Ignacio", "apellido": "Fernández", "equipo": "Arteaga", "categoria": "Sexta"},
        {"nombre": "Ramiro", "apellido": "Ponce", "equipo": "Arteaga", "categoria": "Sexta"},
        {"nombre": "Emanuel", "apellido": "Toledo", "equipo": "Arteaga", "categoria": "Sexta"},

        {"nombre": "Thiago", "apellido": "Mena", "equipo": "Arteaga", "categoria": "Septima"},
        {"nombre": "Simón", "apellido": "Rojas", "equipo": "Arteaga", "categoria": "Septima"},
        {"nombre": "Facundo", "apellido": "Leone", "equipo": "Arteaga", "categoria": "Septima"},

        {"nombre": "Julián", "apellido": "Morales", "equipo": "Godeken", "categoria": "Reserva"},
        {"nombre": "Ezequiel", "apellido": "Herrera", "equipo": "Godeken", "categoria": "Reserva"},
        {"nombre": "Nicolás", "apellido": "Rivas", "equipo": "Godeken", "categoria": "Reserva"},

        {"nombre": "Tomás", "apellido": "Rojas", "equipo": "Godeken", "categoria": "Quinta"},
        {"nombre": "Santino", "apellido": "Molina", "equipo": "Godeken", "categoria": "Quinta"},
        {"nombre": "Bruno", "apellido": "Vega", "equipo": "Godeken", "categoria": "Quinta"},

        {"nombre": "Lautaro", "apellido": "Pérez", "equipo": "Godeken", "categoria": "Sexta"},
        {"nombre": "Iván", "apellido": "Moreno", "equipo": "Godeken", "categoria": "Sexta"},
        {"nombre": "Dylan", "apellido": "Silva", "equipo": "Godeken", "categoria": "Sexta"},

        {"nombre": "Emanuel", "apellido": "Campos", "equipo": "Godeken", "categoria": "Septima"},
        {"nombre": "Nicolás", "apellido": "Vega", "equipo": "Godeken", "categoria": "Septima"},
        {"nombre": "Luca", "apellido": "Arias", "equipo": "Godeken", "categoria": "Septima"},

        {"nombre": "Tomás", "apellido": "Guerra", "equipo": "Chañarense", "categoria": "Reserva"},
        {"nombre": "Franco", "apellido": "Valdez", "equipo": "Chañarense", "categoria": "Reserva"},
        {"nombre": "Emanuel", "apellido": "Ruiz", "equipo": "Chañarense", "categoria": "Reserva"},

        {"nombre": "Luciano", "apellido": "Maldonado", "equipo": "Chañarense", "categoria": "Quinta"},
        {"nombre": "Matías", "apellido": "Roldán", "equipo": "Chañarense", "categoria": "Quinta"},
        {"nombre": "Álvaro", "apellido": "Benítez", "equipo": "Chañarense", "categoria": "Quinta"},

        {"nombre": "Ezequiel", "apellido": "Herrera", "equipo": "Chañarense", "categoria": "Sexta"},
        {"nombre": "Nicolás", "apellido": "Zárate", "equipo": "Chañarense", "categoria": "Sexta"},
        {"nombre": "Dylan", "apellido": "Campos", "equipo": "Chañarense", "categoria": "Sexta"},

        {"nombre": "Facundo", "apellido": "Pereira", "equipo": "Chañarense", "categoria": "Septima"},
        {"nombre": "Ian", "apellido": "Ramos", "equipo": "Chañarense", "categoria": "Septima"},
        {"nombre": "Santino", "apellido": "Reinoso", "equipo": "Chañarense", "categoria": "Septima"},

        {"nombre": "Bruno", "apellido": "Maldonado", "equipo": "Independiente", "categoria": "Reserva"},
        {"nombre": "Tomás", "apellido": "Rossi", "equipo": "Independiente", "categoria": "Reserva"},
        {"nombre": "Lautaro", "apellido": "Soria", "equipo": "Independiente", "categoria": "Reserva"},

        {"nombre": "Ezequiel", "apellido": "Aguirre", "equipo": "Independiente", "categoria": "Quinta"},
        {"nombre": "Matías", "apellido": "Luna", "equipo": "Independiente", "categoria": "Quinta"},
        {"nombre": "Agustín", "apellido": "Paz", "equipo": "Independiente", "categoria": "Quinta"},

        {"nombre": "Luciano", "apellido": "Mena", "equipo": "Independiente", "categoria": "Sexta"},
        {"nombre": "Franco", "apellido": "Godoy", "equipo": "Independiente", "categoria": "Sexta"},
        {"nombre": "Iván", "apellido": "López", "equipo": "Independiente", "categoria": "Sexta"},

        {"nombre": "Dylan", "apellido": "Pérez", "equipo": "Independiente", "categoria": "Septima"},
        {"nombre": "Nahuel", "apellido": "Reyes", "equipo": "Independiente", "categoria": "Septima"},
        {"nombre": "Simón", "apellido": "Vega", "equipo": "Independiente", "categoria": "Septima"},

        {"nombre": "Thiago", "apellido": "Fernández", "equipo": "9 de julio", "categoria": "Reserva"},
        {"nombre": "Franco", "apellido": "Sánchez", "equipo": "9 de julio", "categoria": "Reserva"},
        {"nombre": "Emiliano", "apellido": "Cabrera", "equipo": "9 de julio", "categoria": "Reserva"},

        {"nombre": "Ramiro", "apellido": "Benítez", "equipo": "9 de julio", "categoria": "Quinta"},
        {"nombre": "Santiago", "apellido": "Gómez", "equipo": "9 de julio", "categoria": "Quinta"},
        {"nombre": "Tomás", "apellido": "Moreno", "equipo": "9 de julio", "categoria": "Quinta"},

        {"nombre": "Alan", "apellido": "Ponce", "equipo": "9 de julio", "categoria": "Sexta"},
        {"nombre": "Lucio", "apellido": "Maidana", "equipo": "9 de julio", "categoria": "Sexta"},
        {"nombre": "Nicolás", "apellido": "Vera", "equipo": "9 de julio", "categoria": "Sexta"},

        {"nombre": "Ezequiel", "apellido": "Campos", "equipo": "9 de julio", "categoria": "Septima"},
        {"nombre": "Mateo", "apellido": "Rivas", "equipo": "9 de julio", "categoria": "Septima"},
        {"nombre": "Bruno", "apellido": "Correa", "equipo": "9 de julio", "categoria": "Septima"},

        {"nombre": "Agustín", "apellido": "Leiva", "equipo": "Deportivo", "categoria": "Reserva"},
        {"nombre": "Tomás", "apellido": "Roldán", "equipo": "Deportivo", "categoria": "Reserva"},
        {"nombre": "Dylan", "apellido": "Pereira", "equipo": "Deportivo", "categoria": "Reserva"},

        {"nombre": "Emanuel", "apellido": "Vega", "equipo": "Deportivo", "categoria": "Quinta"},
        {"nombre": "Thiago", "apellido": "Romero", "equipo": "Deportivo", "categoria": "Quinta"},
        {"nombre": "Franco", "apellido": "Maldonado", "equipo": "Deportivo", "categoria": "Quinta"},

        {"nombre": "Lautaro", "apellido": "Ponce", "equipo": "Deportivo", "categoria": "Sexta"},
        {"nombre": "Matías", "apellido": "Benítez", "equipo": "Deportivo", "categoria": "Sexta"},
        {"nombre": "Luciano", "apellido": "Toledo", "equipo": "Deportivo", "categoria": "Sexta"},

        {"nombre": "Ramiro", "apellido": "Soria", "equipo": "Deportivo", "categoria": "Septima"},
        {"nombre": "Iván", "apellido": "Rojas", "equipo": "Deportivo", "categoria": "Septima"},
        {"nombre": "Facundo", "apellido": "Luna", "equipo": "Deportivo", "categoria": "Septima"},

        {"nombre": "Santiago", "apellido": "Godoy", "equipo": "Belgrano", "categoria": "Reserva"},
        {"nombre": "Nicolás", "apellido": "López", "equipo": "Belgrano", "categoria": "Reserva"},
        {"nombre": "Ezequiel", "apellido": "Arias", "equipo": "Belgrano", "categoria": "Reserva"},

        {"nombre": "Tomás", "apellido": "Benítez", "equipo": "Belgrano", "categoria": "Quinta"},
        {"nombre": "Lautaro", "apellido": "Morales", "equipo": "Belgrano", "categoria": "Quinta"},
        {"nombre": "Ramiro", "apellido": "Campos", "equipo": "Belgrano", "categoria": "Quinta"},

        {"nombre": "Lucio", "apellido": "Vega", "equipo": "Belgrano", "categoria": "Sexta"},
        {"nombre": "Dylan", "apellido": "Reyes", "equipo": "Belgrano", "categoria": "Sexta"},
        {"nombre": "Bruno", "apellido": "Paz", "equipo": "Belgrano", "categoria": "Sexta"},

        {"nombre": "Franco", "apellido": "Mena", "equipo": "Belgrano", "categoria": "Septima"},
        {"nombre": "Thiago", "apellido": "Ponce", "equipo": "Belgrano", "categoria": "Septima"},
        {"nombre": "Iván", "apellido": "Cabrera", "equipo": "Belgrano", "categoria": "Septima"},

        {"nombre": "Agustín", "apellido": "Moreno", "equipo": "Huracan", "categoria": "Reserva"},
        {"nombre": "Lautaro", "apellido": "Sosa", "equipo": "Huracan", "categoria": "Reserva"},
        {"nombre": "Matías", "apellido": "Roldán", "equipo": "Huracan", "categoria": "Reserva"},

        {"nombre": "Nicolás", "apellido": "Benítez", "equipo": "Huracan", "categoria": "Quinta"},
        {"nombre": "Ezequiel", "apellido": "Campos", "equipo": "Huracan", "categoria": "Quinta"},
        {"nombre": "Santiago", "apellido": "García", "equipo": "Huracan", "categoria": "Quinta"},

        {"nombre": "Dylan", "apellido": "Vega", "equipo": "Huracan", "categoria": "Sexta"},
        {"nombre": "Ramiro", "apellido": "Maldonado", "equipo": "Huracan", "categoria": "Sexta"},
        {"nombre": "Iván", "apellido": "Morales", "equipo": "Huracan", "categoria": "Sexta"},

        {"nombre": "Bruno", "apellido": "Pereyra", "equipo": "Huracan", "categoria": "Septima"},
        {"nombre": "Luciano", "apellido": "Rojas", "equipo": "Huracan", "categoria": "Septima"},
        {"nombre": "Thiago", "apellido": "Reynoso", "equipo": "Huracan", "categoria": "Septima"},

        {"nombre": "Santino", "apellido": "Campos", "equipo": "Federacion", "categoria": "Reserva"},
        {"nombre": "Tomás", "apellido": "Giménez", "equipo": "Federacion", "categoria": "Reserva"},
        {"nombre": "Emanuel", "apellido": "Ramos", "equipo": "Federacion", "categoria": "Reserva"},

        {"nombre": "Dylan", "apellido": "Leiva", "equipo": "Federacion", "categoria": "Quinta"},
        {"nombre": "Matías", "apellido": "Toledo", "equipo": "Federacion", "categoria": "Quinta"},
        {"nombre": "Bruno", "apellido": "Maldonado", "equipo": "Federacion", "categoria": "Quinta"},

        {"nombre": "Nicolás", "apellido": "Roldán", "equipo": "Federacion", "categoria": "Sexta"},
        {"nombre": "Lucio", "apellido": "Vera", "equipo": "Federacion", "categoria": "Sexta"},
        {"nombre": "Franco", "apellido": "Godoy", "equipo": "Federacion", "categoria": "Sexta"},

        {"nombre": "Ezequiel", "apellido": "Romero", "equipo": "Federacion", "categoria": "Septima"},
        {"nombre": "Thiago", "apellido": "López", "equipo": "Federacion", "categoria": "Septima"},
        {"nombre": "Ramiro", "apellido": "Soria", "equipo": "Federacion", "categoria": "Septima"}
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