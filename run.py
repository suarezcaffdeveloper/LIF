from app import create_app
from app.database.db import db

#from seeds.fixture import generar_fixtures
from app.utils.generar_json_datos_partidos import cargar_eventos_jugadores_desde_json, cargar_resultados_partidos_desde_json

#from app.utils.cargar_datos_prueba import cargar_datos_desde_json

app = create_app()

with app.app_context():
    db.create_all() 
    #cargar_goleadores()
    #generar_fixtures()
    #cargar_eventos_jugadores_desde_json()
    #cargar_resultados_partidos_desde_json()
    #cargar_datos_tabla_posiciones()
    #cargar_datos_desde_json()

if __name__ == '__main__':
    app.run(debug=True)

