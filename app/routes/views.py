from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models.models import (
    Equipo, Partido, Jugador, Video, Noticia, Usuario,
    TablaPosiciones, EstadoJugadorPartido
)
from ..database.db import db
from sqlalchemy import func

views = Blueprint('views', __name__)

@views.route('/')
def index():
    equipos = Equipo.query.all()
    return render_template('index.html', equipos=equipos)

@views.route('/fixture/<bloque>')
@views.route('/fixture/<bloque>/<categoria>')
def fixture(bloque, categoria=None):
    # Definimos las categorías que pertenecen a cada bloque
    bloques = {
        "mayores": ["Primera", "Reserva"],
        "inferiores": ["quinta", "sexta", "septima"]
    }

    if bloque not in bloques:
        flash("Bloque inválido", "danger")
        return redirect(url_for("views.index"))

    categorias_bloque = bloques[bloque]

    if categoria:
        if categoria not in categorias_bloque:
            flash("Categoría inválida", "danger")
            return redirect(url_for("views.index"))
        partidos = Partido.query.filter_by(categoria=categoria).order_by(Partido.jornada).all()
        titulo = f"Fixture {categoria.capitalize()}"
    else:
        # Si no se elige categoría, mostramos todas del bloque
        partidos = Partido.query.filter(Partido.categoria.in_(categorias_bloque)).order_by(Partido.jornada).all()
        titulo = f"Fixture {bloque.capitalize()}"

    fechas_partidos = {}
    for partido in partidos:
        fecha_key = f"Jornada {partido.jornada}"
        fechas_partidos.setdefault(fecha_key, []).append(partido)

    return render_template("fixture_general.html", fechas_partidos=fechas_partidos, titulo=titulo)



@views.route('/goleadores/<categoria>')
def mostrar_estadisticas(categoria):
    goles = (
        db.session.query(
            Jugador,
            func.sum(EstadoJugadorPartido.cant_goles).label('total_goles')
        )
        .join(EstadoJugadorPartido)
        .join(EstadoJugadorPartido.partido)
        .filter(func.lower(Partido.categoria) == categoria.lower())
        .group_by(Jugador.id)
        .order_by(func.sum(EstadoJugadorPartido.cant_goles).desc())
        .all()
    )

    amarillas = (
        db.session.query(
            Jugador,
            func.sum(EstadoJugadorPartido.tarjetas_amarillas).label('total_amarillas')
        )
        .join(EstadoJugadorPartido)
        .join(EstadoJugadorPartido.partido)
        .filter(func.lower(Partido.categoria) == categoria.lower())
        .group_by(Jugador.id)
        .order_by(func.sum(EstadoJugadorPartido.tarjetas_amarillas).desc())
        .limit(5)
    )

    rojas = (
        db.session.query(
            Jugador,
            func.sum(EstadoJugadorPartido.tarjetas_rojas).label('total_rojas')
        )
        .join(EstadoJugadorPartido)
        .join(EstadoJugadorPartido.partido)
        .filter(func.lower(Partido.categoria) == categoria.lower())
        .group_by(Jugador.id)
        .order_by(func.sum(EstadoJugadorPartido.tarjetas_rojas).desc())
        .limit(5)
    )

    return render_template(
        'goleadores.html',
        categoria=categoria,
        goles=goles,
        amarillas=amarillas,
        rojas=rojas
    )

@views.route('/tabla_posiciones')
def tabla_posiciones():
    tabla = TablaPosiciones.query.order_by(
        TablaPosiciones.cantidad_puntos.desc(),
        TablaPosiciones.diferencia_gol.desc()
    ).all()
    return render_template('tabla_posiciones.html', tabla=tabla)

@views.route("/cargar_resultados", methods=["GET", "POST"])
def cargar_resultados():
    if request.method == "POST":
        try:
            for i in range(1, 4):
                partido_id = request.form.get(f"partido_{i}")
                goles_local = int(request.form.get(f"goles_local_{i}", 0))
                goles_visitante = int(request.form.get(f"goles_visitante_{i}", 0))

                partido = Partido.query.get(int(partido_id))
                partido.goles_local = goles_local
                partido.goles_visitante = goles_visitante
                partido.jugado = True

                goleadores = request.form.getlist(f"goleador_{i}[]")
                goles_por_jugador = request.form.getlist(f"goles_{i}[]")

                for jugador_id, cantidad in zip(goleadores, goles_por_jugador):
                    if jugador_id and cantidad:
                        estado = EstadoJugadorPartido(
                            id_jugador=int(jugador_id),
                            id_partido=partido.id,
                            cant_goles=int(cantidad)
                        )
                        db.session.add(estado)

            db.session.commit()
            flash("✅ Resultados cargados correctamente", "success")
            return redirect(url_for("views.cargar_resultados"))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al cargar los resultados: {e}", "danger")
            return redirect(url_for("views.cargar_resultados"))

    partidos = Partido.query.filter_by(jugado=False).order_by(Partido.fecha_partido).all()
    jugadores = Jugador.query.order_by(Jugador.nombre).all()
    return render_template("cargar_resultados.html", partidos=partidos, jugadores=jugadores)
