from app import create_app
from app.database.db import db
from seeds.puntajes import cargar_puntajes
from seeds.goleadores import cargar_goleadores
from seeds.jugadores import cargar_jugadores
from seeds.teams import cargar_equipos
from seeds.fixture import generar_fixtures

app = create_app()

with app.app_context():
    db.create_all() 
    cargar_equipos()
    cargar_puntajes()
    cargar_goleadores()
    cargar_jugadores()
    generar_fixtures()

if __name__ == '__main__':
    app.run(debug=True)

