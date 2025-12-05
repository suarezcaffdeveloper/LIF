from flask import Blueprint, render_template, jsonify, json,request, redirect, url_for, flash
from ..models.models import (
    Equipo, Partido, Jugador, Club, Video, Noticia, Usuario, JugadorEquipo,
    TablaPosiciones, EstadoJugadorPartido
)
#import jsonify
from ..database.db import db
from sqlalchemy import func
import datetime
from datetime import datetime
from seeds.puntajes import cargar_puntajes_por_categoria
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

views = Blueprint('views', __name__)

@views.route('/')
def index():
    clubes = Club.query.all()
    return render_template('index.html', clubes=clubes)

@views.route('/fixture/<bloque>')
@views.route('/fixture/<bloque>/<categoria>')
def fixture(bloque, categoria=None):

    bloques = {
        "mayores": ["Primera", "Reserva"],
        "inferiores": ["Quinta", "Sexta", "Septima"]
    }

    # ===============================
    # ✅ VALIDAR BLOQUE
    # ===============================
    if bloque not in bloques:
        flash("Bloque inválido", "danger")
        return redirect(url_for("views.index"))

    categorias_bloque = bloques[bloque]

    partidos = []   # ✅ BLINDAJE TOTAL → evita el UnboundLocalError

    # ===============================
    # ✅ SI SE PIDE UNA CATEGORÍA
    # ===============================
    if categoria:
        if categoria not in categorias_bloque:
            flash("Categoría inválida", "danger")
            return redirect(url_for("views.index"))

        partidos = (
            Partido.query
            .filter(Partido.categoria == categoria)
            .order_by(Partido.jornada, Partido.fecha_partido)
            .all()
        )

        titulo = f"Fixture {categoria}"
        mostrar_resultados = True

    # ===============================
    # ✅ SI SE PIDE EL BLOQUE COMPLETO
    # ===============================
    else:
        partidos = (
            Partido.query
            .filter(Partido.categoria.in_(categorias_bloque))
            .order_by(Partido.jornada, Partido.fecha_partido)
            .all()
        )

        titulo = f"Fixture {bloque.capitalize()}"
        mostrar_resultados = True

    # ===============================
    # ✅ AGRUPAR POR JORNADA
    # ===============================
    fechas_partidos = {}

    for partido in partidos:
        fecha_key = f"Jornada {partido.jornada}"
        fechas_partidos.setdefault(fecha_key, []).append(partido)

    return render_template(
        "fixture_general.html",
        fechas_partidos=fechas_partidos,
        titulo=titulo,
        mostrar_resultados=mostrar_resultados
    )



def consulta_estadistica(columna, categoria, limite=15):
    return (
        db.session.query(
            Jugador.numero_carnet,
            Jugador.nombre,
            Jugador.apellido,
            Club.nombre.label("club_nombre"),
            func.sum(columna).label("total")
        )
        .join(EstadoJugadorPartido, EstadoJugadorPartido.id_jugador == Jugador.numero_carnet)
        .join(Partido, Partido.id == EstadoJugadorPartido.id_partido)
        .join(Club, Club.id == Jugador.club_id)
        .filter(func.lower(Partido.categoria) == categoria.lower())
        .group_by(
            Jugador.numero_carnet,
            Jugador.nombre,
            Jugador.apellido,
            Club.nombre
        )
        .order_by(func.sum(columna).desc())
        .limit(limite)
        .all()
    )


@views.route('/goleadores/<categoria>')
def mostrar_estadisticas(categoria):

    goles = consulta_estadistica(EstadoJugadorPartido.cant_goles, categoria, limite=15)
    amarillas = consulta_estadistica(EstadoJugadorPartido.tarjetas_amarillas, categoria, limite=10)
    rojas = consulta_estadistica(EstadoJugadorPartido.tarjetas_rojas, categoria, limite=10)

    return render_template(
        'goleadores.html',
        categoria=categoria,
        goles=goles,
        amarillas=amarillas,
        rojas=rojas
    )

@views.route('/tabla_posiciones/<categoria>')
def tabla_posiciones(categoria):
    
    #cargar_puntajes_por_categoria(categoria)

    tabla = (
        TablaPosiciones.query
        .filter_by(categoria=categoria)
        .order_by(
            TablaPosiciones.cantidad_puntos.desc(),
            TablaPosiciones.diferencia_gol.desc(),
            TablaPosiciones.goles_a_favor.desc()
        )
        .all()
    )

    return render_template('tabla_posiciones.html', tabla=tabla, categoria=categoria)

"""@views.route("/cargar_resultados", methods=["GET", "POST"])
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
"""
#LOGIN
# ---------------- REGISTRO ----------------
@views.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        rol = request.form['rol']

        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'warning')
            return redirect(url_for('views.register'))

        nuevo_usuario = Usuario(
            nombre_completo=nombre_completo,
            email=email,
            rol=rol
        )
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso. Ahora podés iniciar sesión.', 'success')
        return redirect(url_for('views.login'))

    return render_template('register.html')

# ---------------- LOGIN ----------------

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(contraseña):
            login_user(usuario)
            flash('Inicio de sesión exitoso.', 'success')
            if usuario.rol == 'usuario':
                return render_template('index.html')
            elif usuario.rol == 'administrador':
                return render_template('adminview.html')
            else:
                return render_template('periodistaview.html')
        else:
            flash('Credenciales incorrectas.', 'danger')
            return redirect(url_for('views.login'))

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@views.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('views.login'))

# ---------------- DASHBOARD ----------------
@views.route('/dashboard')
@login_required
def dashboard():
    if current_user.rol == 'administrador':
        return render_template('adminview.html', usuario=current_user)
    elif current_user.rol == 'periodista':
        return render_template('periodistaview.html', usuario=current_user)
    else:
        return render_template('index.html', usuario=current_user)
    
# ---------------- ADMIN VIEW ----------------
@views.route('/adminview')
@login_required
def adminview():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))
    return render_template('adminview.html', usuario=current_user)

@views.route("/cargar_clubes", methods=["GET", "POST"])
def cargar_clubes():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        localidad = request.form.get("localidad")
        escudo_url = request.form.get("escudo_url") or None

        club_existente = Club.query.filter_by(nombre=nombre).first()
        if club_existente:
            flash("El club ya existe en la base de datos.", "danger")
            return redirect(url_for("views.cargar_clubes"))

        nuevo_club = Club(
            nombre=nombre,
            localidad=localidad,
            escudo_url=escudo_url
        )

        db.session.add(nuevo_club)
        db.session.commit()

        flash("Club cargado correctamente.", "success")
        return redirect(url_for("views.cargar_clubes"))

    return render_template("plantillasAdmin/cargar_clubes.html")
    
@views.route("/cargar_equipos", methods=["GET", "POST"])
def cargar_equipos():
    if request.method == "POST":

        # Convertir a enteros y limpiar datos
        try:
            club_id = int(request.form.get("club_id"))
        except (TypeError, ValueError):
            flash("Club inválido.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        categoria = request.form.get("categoria")

        if not categoria:
            flash("Debe seleccionar una categoría.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        # Verificar que el club exista
        club = Club.query.get(club_id)
        if not club:
            flash("El club seleccionado no existe.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        # Validar duplicado
        existe = Equipo.query.filter_by(club_id=club_id, categoria=categoria).first()
        if existe:
            flash("Ese equipo ya existe para ese club.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        # Crear equipo
        nuevo_equipo = Equipo(
            club_id=club_id,
            categoria=categoria
        )

        db.session.add(nuevo_equipo)
        db.session.commit()

        flash("Equipo cargado correctamente.", "success")
        return redirect(url_for("views.cargar_equipos"))

    # GET: Mostrar formulario
    clubes = Club.query.order_by(Club.nombre.asc()).all()
    return render_template("plantillasAdmin/cargar_equipos.html", clubes=clubes)


@views.route('/cargar_jugadores', methods=['GET', 'POST'])
def cargar_jugadores():
    clubes = Club.query.order_by(Club.nombre).all()

    if request.method == 'POST':
        numero_carnet = request.form.get('numeroCarnet')
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        fecha_nacimiento = request.form.get('fechaNacimiento')
        club_id = request.form.get('club_id')

        if not numero_carnet or not nombre or not apellido or not club_id:
            flash("Todos los campos obligatorios deben estar completos.", "danger")
            return redirect(url_for('views.cargar_jugadores'))

        jugador_existente_carnet = Jugador.query.filter_by(numero_carnet=numero_carnet).first()
        if jugador_existente_carnet:
            flash("Ya existe un jugador con ese número de carnet.", "danger")
            return redirect(url_for('views.cargar_jugadores'))

        jugador_duplicado = Jugador.query.filter_by(
            nombre=nombre,
            apellido=apellido,
            club_id=club_id
        ).first()

        if jugador_duplicado:
            flash("Ese jugador ya está registrado en este club.", "danger")
            return redirect(url_for('views.cargar_jugadores'))

        fecha_nac = None
        if fecha_nacimiento:
            try:
                fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            except ValueError:
                flash("La fecha de nacimiento no es válida.", "danger")
                return redirect(url_for('views.cargar_jugadores'))

        nuevo_jugador = Jugador(
            numero_carnet=numero_carnet,
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nac,
            club_id=club_id
        )

        db.session.add(nuevo_jugador)
        db.session.commit()

        flash("Jugador cargado correctamente.", "success")
        return redirect(url_for('views.cargar_jugadores'))

    return render_template("plantillasAdmin/cargar_jugadores.html", clubes=clubes)

@views.route('/obtener_datos_club/<int:club_id>')
def obtener_datos_club(club_id):
    jugadores = Jugador.query.filter_by(club_id=club_id).order_by(Jugador.apellido).all()
    equipos = Equipo.query.filter_by(club_id=club_id).order_by(Equipo.categoria).all()

    return {
        "jugadores": [
            {
                "numero_carnet": j.numero_carnet,
                "nombre": j.nombre,
                "apellido": j.apellido
            } for j in jugadores
        ],
        "equipos": [
            {
                "id": e.id,
                "categoria": e.categoria
            } for e in equipos
        ]
    }
    
@views.route('/asignar_jugador_categoria', methods=['GET', 'POST'])
def asignar_jugador_categoria():
    clubes = Club.query.order_by(Club.nombre).all()

    if request.method == 'POST':
        numero_carnet = request.form.get('numero_carnet')
        equipo_id = request.form.get('equipo_id')

        if not numero_carnet or not equipo_id:
            flash("Debe seleccionar un jugador y una categoría.", "danger")
            return redirect(url_for('views.asignar_jugador_categoria'))

        # Validar si esa relación ya existe
        existe = JugadorEquipo.query.filter_by(
            numero_carnet=numero_carnet,
            equipo_id=equipo_id
        ).first()

        if existe:
            flash("Este jugador ya está asignado a esa categoría.", "warning")
            return redirect(url_for('views.asignar_jugador_categoria'))

        nuevo = JugadorEquipo(
            numero_carnet=numero_carnet,
            equipo_id=equipo_id
        )

        db.session.add(nuevo)
        db.session.commit()

        flash("Jugador asignado correctamente a la categoría.", "success")
        return redirect(url_for('views.asignar_jugador_categoria'))

    return render_template("plantillasAdmin/cargar_jugador_equipo.html", clubes=clubes)

@views.route('/cargar_fixture_mayores', methods=['GET'])
def cargar_fixture_mayores_view():
    # Traer equipos REALES (tabla Equipo) solo de Primera y Reserva
    equipos = (
        Equipo.query
        .filter(Equipo.categoria.in_(["Primera", "Reserva"]))
        .order_by(Equipo.club_id)
        .all()
    )

    # Traer todos los clubes
    clubes = Club.query.all()

    # Total de equipos = equipos de Primera (un equipo por club)
    total_equipos = Equipo.query.filter_by(categoria="Primera").count()
    total_jornadas = total_equipos - 1  # todos contra todos

    # Construir diccionario: club_id → {categoria → equipo_id}
    equipos_por_club = {}
    for equipo in equipos:
        club_id = equipo.club_id
        if club_id not in equipos_por_club:
            equipos_por_club[club_id] = {}
        equipos_por_club[club_id][equipo.categoria] = equipo.id

    return render_template(
        "plantillasAdmin/cargar_fixture_mayores.html",
        equipos=equipos,
        clubes=clubes,
        total_jornadas=total_jornadas,
        equipos_por_club=equipos_por_club
    )



@views.route('/cargar_fixture_mayores', methods=['POST'])
def cargar_fixture_mayores():
    jornada = int(request.form.get("jornada"))

    # IDs de los clubes elegidos en el formulario
    club_local_id = int(request.form.get("club_local"))
    club_visitante_id = int(request.form.get("club_visitante"))

    fecha = request.form.get("fecha")
    hora = request.form.get("hora")

    # Validación: no puede jugar un club contra sí mismo
    if club_local_id == club_visitante_id:
        flash("Un club no puede enfrentarse a sí mismo.", "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    # Obtener los equipos REALES de Primera y Reserva para cada club
    local_primera = Equipo.query.filter_by(club_id=club_local_id, categoria="Primera").first()
    local_reserva  = Equipo.query.filter_by(club_id=club_local_id, categoria="Reserva").first()
    visita_primera = Equipo.query.filter_by(club_id=club_visitante_id, categoria="Primera").first()
    visita_reserva = Equipo.query.filter_by(club_id=club_visitante_id, categoria="Reserva").first()

    # Validación: si algún equipo falta, es un error del modelo de datos
    if not (local_primera and local_reserva and visita_primera and visita_reserva):
        flash("Error: faltan equipos de Primera o Reserva para uno de los clubes.", "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    # Evitar que ya hayan jugado anteriormente (en cualquier categoría)
    enfrentado = Partido.query.filter(
        ((Partido.equipo_local_id.in_([local_primera.id, local_reserva.id])) &
         (Partido.equipo_visitante_id.in_([visita_primera.id, visita_reserva.id]))) |
        ((Partido.equipo_local_id.in_([visita_primera.id, visita_reserva.id])) &
         (Partido.equipo_visitante_id.in_([local_primera.id, local_reserva.id])))
    ).first()

    if enfrentado:
        flash("Estos clubes ya se enfrentaron en alguna jornada o tienen otro partido asignado.", "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    # Evitar que algún equipo ya tenga partido en la misma jornada
    conflicto = Partido.query.filter(
        (Partido.jornada == jornada) &
        (
            Partido.equipo_local_id.in_([local_primera.id, local_reserva.id, visita_primera.id, visita_reserva.id]) |
            Partido.equipo_visitante_id.in_([local_primera.id, local_reserva.id, visita_primera.id, visita_reserva.id])
        )
    ).first()

    if conflicto:
        flash("Uno de los equipos ya tiene partido en esta jornada.", "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    # Crear partidos para Primera y Reserva
    partido_primera = Partido(
        fecha_partido=fecha,
        hora_partido=hora,
        jornada=jornada,
        categoria="Primera",
        equipo_local_id=local_primera.id,
        equipo_visitante_id=visita_primera.id,
        jugado=False
    )

    partido_reserva = Partido(
        fecha_partido=fecha,
        hora_partido=hora,
        jornada=jornada,
        categoria="Reserva",
        equipo_local_id=local_reserva.id,
        equipo_visitante_id=visita_reserva.id,
        jugado=False
    )

    db.session.add(partido_primera)
    db.session.add(partido_reserva)
    db.session.commit()

    flash("Partidos cargados correctamente para Primera y Reserva.", "success")
    return redirect(url_for("views.cargar_fixture_mayores_view"))


@views.route('/fixture/equipos_disponibles/<int:jornada>', methods=['GET'])
def equipos_disponibles(jornada):
    # Equipos ya ocupados esa jornada
    partidos = Partido.query.filter_by(jornada=jornada).all()

    equipos_ocupados = {p.equipo_local_id for p in partidos} | \
                       {p.equipo_visitante_id for p in partidos}

    # Equipos disponibles solo de categorías Mayores
    equipos_disponibles = Equipo.query.filter(
        Equipo.categoria.in_(["Primera", "Reserva"]),
        ~Equipo.id.in_(equipos_ocupados)
    ).all()

    return jsonify([
        {"id": eq.id, "nombre": eq.club.nombre}
        for eq in equipos_disponibles
    ])

@views.route('/cargar_fixture_inferiores', methods=['GET', 'POST'])
@login_required
def cargar_fixture_inferiores():
    clubes = Club.query.all()
    total_jornadas = len(clubes) - 1

    CATEGORIAS_INFERIORES = {"Quinta", "Sexta", "Septima"}

    if request.method == 'POST':
        jornada = int(request.form['jornada'])
        fecha = request.form.get('fecha') or None
        hora = request.form.get('hora') or None

        local_id = int(request.form['local'])
        visitante_id = int(request.form['visitante'])

        # --- VALIDACIÓN 1: Local y visitante NO pueden ser el mismo club ---
        if local_id == visitante_id:
            flash("El club local y visitante no pueden ser el mismo.", "error")
            return redirect(url_for('views.cargar_fixture_inferiores'))

        # Obtener planteles
        equipos_local = Equipo.query.filter_by(club_id=local_id).all()
        equipos_visit = Equipo.query.filter_by(club_id=visitante_id).all()

        categorias_local = {e.categoria for e in equipos_local}
        categorias_visit = {e.categoria for e in equipos_visit}

        categorias_comunes = categorias_local.intersection(categorias_visit)

        # Filtrar solo inferiores
        categorias_inferiores_comunes = categorias_comunes.intersection(CATEGORIAS_INFERIORES)

        if not categorias_inferiores_comunes:
            flash("Los clubes no comparten categorías de inferiores.", "error")
            return redirect(url_for('views.cargar_fixture_inferiores'))

        # --- VALIDACIÓN 2: VERIFICAR SI YA JUGARON ENTRE SÍ ---
        for categoria in categorias_inferiores_comunes:
            equipo_local = next(e for e in equipos_local if e.categoria == categoria)
            equipo_visitante = next(e for e in equipos_visit if e.categoria == categoria)

            partido_existente = Partido.query.filter(
                ((Partido.equipo_local_id == equipo_local.id) &
                 (Partido.equipo_visitante_id == equipo_visitante.id)) |
                ((Partido.equipo_local_id == equipo_visitante.id) &
                 (Partido.equipo_visitante_id == equipo_local.id))
            ).first()

            if partido_existente:
                flash(
                    f"Ya existe un partido entre {equipo_local.club.nombre} y "
                    f"{equipo_visitante.club.nombre}. No pueden volver a enfrentarse.",
                    "error"
                )
                return redirect(url_for('views.cargar_fixture_inferiores'))

        # --- VALIDACIÓN 3: NO PUEDEN JUGAR MÁS DE UNA VEZ EN LA MISMA JORNADA ---
        for categoria in categorias_inferiores_comunes:
            equipo_local = next(e for e in equipos_local if e.categoria == categoria)
            equipo_visitante = next(e for e in equipos_visit if e.categoria == categoria)

            partido_misma_fecha_local = Partido.query.filter_by(
                jornada=jornada, equipo_local_id=equipo_local.id
            ).first()

            partido_misma_fecha_visit_local = Partido.query.filter_by(
                jornada=jornada, equipo_visitante_id=equipo_local.id
            ).first()

            partido_misma_fecha_visit = Partido.query.filter_by(
                jornada=jornada, equipo_visitante_id=equipo_visitante.id
            ).first()

            partido_misma_fecha_local2 = Partido.query.filter_by(
                jornada=jornada, equipo_local_id=equipo_visitante.id
            ).first()

            if (partido_misma_fecha_local or partido_misma_fecha_visit_local or
                partido_misma_fecha_visit or partido_misma_fecha_local2):

                flash(
                    f"Uno de los clubes ya tiene un partido cargado en la jornada {jornada}.",
                    "error"
                )
                return redirect(url_for('views.cargar_fixture_inferiores'))

        # --- SI TODO ESTÁ OK → GENERAR PARTIDOS ---
        partidos_generados = 0

        for categoria in categorias_inferiores_comunes:
            equipo_local = next(e for e in equipos_local if e.categoria == categoria)
            equipo_visitante = next(e for e in equipos_visit if e.categoria == categoria)

            partido = Partido(
                jornada=jornada,
                fecha_partido=fecha,
                hora_partido=hora,
                categoria=categoria,
                equipo_local_id=equipo_local.id,
                equipo_visitante_id=equipo_visitante.id
            )

            db.session.add(partido)
            partidos_generados += 1

        db.session.commit()
        flash(f"Se generaron {partidos_generados} partidos de inferiores.", "success")
        return redirect(url_for('views.cargar_fixture_inferiores'))

    return render_template(
        'plantillasAdmin/cargar_fixture_inferiores.html',
        clubes=clubes,
        total_jornadas=total_jornadas
    )
    
# -----------------------------------------
# 1) Pantalla principal (única plantilla)
# -----------------------------------------
@views.route('/cargar_estadisticas_mayores')
def cargar_estadisticas_mayores():
    jornadas = db.session.query(Partido.jornada).distinct().order_by(Partido.jornada).all()
    jornadas = [j[0] for j in jornadas]
    return render_template('plantillasAdmin/cargar_estadisticas_mayores.html', jornadas=jornadas)


@views.route("/api/cruces_por_jornada/<int:jornada>")
def cruces_por_jornada(jornada):

    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.categoria.in_(["Primera", "Reserva"])
    ).all()

    cruces = {}

    for p in partidos:
        key = f"{p.equipo_local.club.nombre} vs {p.equipo_visitante.club.nombre}"

        if key not in cruces:
            cruces[key] = {
                "local": p.equipo_local.club.nombre,
                "visitante": p.equipo_visitante.club.nombre,
                "id_reserva": None,
                "id_primera": None
            }

        if p.categoria == "Reserva":
            cruces[key]["id_reserva"] = p.id
        else:
            cruces[key]["id_primera"] = p.id

    # Convertir en lista y elegir un ID representativo (el de reserva o primera)
    respuesta = []
    for key, c in cruces.items():
        id_representativo = c["id_reserva"] or c["id_primera"]
        respuesta.append({
            "id": id_representativo,
            "local": c["local"],
            "visitante": c["visitante"],
            "id_reserva": c["id_reserva"],
            "id_primera": c["id_primera"]
        })

    return jsonify(respuesta)

# -----------------------------------------
# 2) Obtener cruces de la jornada
# -----------------------------------------
@views.route("/api/info_cruce/<int:cruce_id>")
def info_cruce(cruce_id):

    # 1) Buscar el partido base (puede ser primera o reserva)
    partido_base = Partido.query.get(cruce_id)
    if not partido_base:
        return jsonify({"error": "Cruce no encontrado"}), 404

    jornada = partido_base.jornada

    # IDENTIFICAR LOS CLUBES DEL CRUCE
    local_club_id = partido_base.equipo_local.club_id
    visitante_club_id = partido_base.equipo_visitante.club_id

    print("\n🔎 Buscando cruce por CLUBES:")
    print("Jornada:", jornada)
    print("Local club:", local_club_id, partido_base.equipo_local.club.nombre)
    print("Visitante club:", visitante_club_id, partido_base.equipo_visitante.club.nombre)

    # 2) Buscar TODOS los equipos del club local y visitante
    equipos_local = Equipo.query.filter_by(club_id=local_club_id).all()
    equipos_visitante = Equipo.query.filter_by(club_id=visitante_club_id).all()

    ids_equipos_local = [e.id for e in equipos_local]
    ids_equipos_visitante = [e.id for e in equipos_visitante]

    # 3) Buscar los partidos de PRIMERA y RESERVA por club (correcto)
    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.equipo_local_id.in_(ids_equipos_local),
        Partido.equipo_visitante_id.in_(ids_equipos_visitante),
        Partido.categoria.in_(["Primera", "Reserva"])
    ).all()

    print("Partidos encontrados:", len(partidos))
    for p in partidos:
        print(f" - ID {p.id} | cat: {p.categoria} | local eq: {p.equipo_local_id} | vis eq: {p.equipo_visitante_id}")

    # 4) Identificar cada categoría
    partido_primera = next((p for p in partidos if p.categoria.lower() == "primera"), None)
    partido_reserva = next((p for p in partidos if p.categoria.lower() == "reserva"), None)

    return jsonify({
        "id_primera": partido_primera.id if partido_primera else None,
        "id_reserva": partido_reserva.id if partido_reserva else None,
        "local_id": local_club_id,
        "local_nombre": partido_base.equipo_local.club.nombre,
        "visitante_id": visitante_club_id,
        "visitante_nombre": partido_base.equipo_visitante.club.nombre,
        "jornada": jornada   # <--- AÑADIDO
    })

# -----------------------------------------
# 3) Obtener datos del cruce (partidos + jugadores)
# -----------------------------------------
@views.route('/get_partidos_cruce', methods=['POST'])
def get_partidos_cruce():

    data = request.json

    jornada = data.get("jornada")
    local = data.get("local")        # Puede venir ID o nombre
    visitante = data.get("visitante")  # Puede venir ID o nombre

    print("📌 Datos recibidos → Jornada:", jornada, "| Local:", local, "| Visitante:", visitante)

    # ===== VALIDACIONES BÁSICAS =====
    if not jornada or not local or not visitante:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    # ===== CONVERTIR NOMBRES A IDs =====
    def obtener_club_id(valor):
        """Convierte nombre de club a ID si valor es str."""
        if isinstance(valor, int):
            return valor  # Ya es ID

        if isinstance(valor, str):
            club = Club.query.filter_by(nombre=valor).first()
            if not club:
                raise ValueError(f"Club '{valor}' no encontrado")
            return club.id

        raise ValueError("Valor inválido para club")

    try:
        local_id = obtener_club_id(local)
        visitante_id = obtener_club_id(visitante)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    # ===== OBTENER EQUIPOS ASOCIADOS A CADA CLUB =====
    ids_equipos_local = [e.id for e in Equipo.query.filter_by(club_id=local_id).all()]
    ids_equipos_visitante = [e.id for e in Equipo.query.filter_by(club_id=visitante_id).all()]

    print("🏷️ Equipos del LOCAL:", ids_equipos_local)
    print("🏷️ Equipos del VISITANTE:", ids_equipos_visitante)

    # ===== BUSCAR SOLO PARTIDOS PRIMERA / RESERVA =====
    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.equipo_local_id.in_(ids_equipos_local),
        Partido.equipo_visitante_id.in_(ids_equipos_visitante),
        Partido.categoria.in_(["Primera", "Reserva"])
    ).all()

    print("📌 Partidos encontrados:", len(partidos))

    respuesta = {}

    for p in partidos:
        categoria = p.categoria.lower()  # "primera" / "reserva"

        print(
            f"   → Partido ID {p.id} | Cat: {p.categoria} | "
            f"{p.equipo_local.club.nombre} ({p.equipo_local.id}) vs "
            f"{p.equipo_visitante.club.nombre} ({p.equipo_visitante.id})"
        )

        respuesta[categoria] = {
            "id": p.id,
            "id_equipo_local": p.equipo_local.id,
            "id_equipo_visitante": p.equipo_visitante.id,
            "goles_local": p.goles_local,
            "goles_visitante": p.goles_visitante
        }

    return jsonify(respuesta)


@views.route("/api/jugadores_por_equipo/<int:equipo_id>")
def jugadores_por_equipo(equipo_id):

    jug_eq = (
        JugadorEquipo.query
        .filter_by(equipo_id=equipo_id)
        .join(Jugador)
        .order_by(Jugador.apellido.asc(), Jugador.nombre.asc())
        .all()
    )

    jugadores = [
        {
            "id": je.jugador.numero_carnet,  
            "nombre": f"{je.jugador.apellido}, {je.jugador.nombre}",
            "club": je.jugador.club.nombre if je.jugador.club else None
        }
        for je in jug_eq
    ]

    return jsonify(jugadores)

# -----------------------------------------
# 4) Guardar resultados
# -----------------------------------------
def validar_y_guardar_estadisticas(data, categoria):
    id_partido = data.get("partido_id")
    goles_local = int(data.get("goles_local", 0))
    goles_visitante = int(data.get("goles_visitante", 0))

    goleadores_local = data.get("goleadores_local", [])
    goleadores_visitante = data.get("goleadores_visitante", [])

    amarillas_local = data.get("amarillas_local", [])
    amarillas_visitante = data.get("amarillas_visitante", [])

    rojas_local = data.get("rojas_local", [])
    rojas_visitante = data.get("rojas_visitante", [])

    # 1. Buscar partido
    partido = Partido.query.get(id_partido)
    if not partido:
        return {"success": False, "message": "Partido no encontrado"}, 404

    # 2. Validar categoría
    if partido.categoria.lower() != categoria:
        return {
            "success": False,
            "message": f"Este endpoint solo guarda datos de {categoria.capitalize()}."
        }, 400

    # 3. Validar si ya fue jugado
    if partido.jugado:
        return {
            "success": False,
            "message": f"El partido de {categoria.capitalize()} ya fue cargado."
        }, 400

    # 4. Verificar suma de goles
    total_local = sum(int(g["goles"]) for g in goleadores_local)
    total_visitante = sum(int(g["goles"]) for g in goleadores_visitante)

    if total_local != goles_local or total_visitante != goles_visitante:
        return {
            "success": False,
            "message": "Los goles no coinciden con los goleadores."
        }, 400

    # 5. Guardar goles + marcar como jugado
    partido.goles_local = goles_local
    partido.goles_visitante = goles_visitante
    partido.jugado = True

    # 6. Unificar estadísticas por jugador
    stats = {}

    def ensure(jid):
        if jid not in stats:
            stats[jid] = {"cant_goles": 0, "tarjetas_amarillas": 0, "tarjetas_rojas": 0}

    for item in goleadores_local + goleadores_visitante:
        jugador_id = item.get("jugador_id")
        goles = int(item.get("goles", 0))
        if jugador_id:
            ensure(jugador_id)
            stats[jugador_id]["cant_goles"] += goles

    for jugador in amarillas_local + amarillas_visitante:
        ensure(jugador)
        stats[jugador]["tarjetas_amarillas"] += 1

    for jugador in rojas_local + rojas_visitante:
        ensure(jugador)
        stats[jugador]["tarjetas_rojas"] += 1

    # 7. Insertar registros
    for jugador_id, valores in stats.items():
        registro = EstadoJugadorPartido(
            id_partido=id_partido,
            id_jugador=jugador_id,
            cant_goles=valores["cant_goles"],
            tarjetas_amarillas=valores["tarjetas_amarillas"],
            tarjetas_rojas=valores["tarjetas_rojas"]
        )
        db.session.add(registro)

    db.session.commit()

    return {
        "success": True,
        "message": "Estadísticas guardadas correctamente"
    }, 200


@views.route("/api/guardar_reserva", methods=["POST"])
def guardar_reserva():
    data = request.json
    response, code = validar_y_guardar_estadisticas(data, "reserva")
    return jsonify(response), code


@views.route("/api/guardar_primera", methods=["POST"])
def guardar_primera():
    data = request.json
    response, code = validar_y_guardar_estadisticas(data, "primera")
    return jsonify(response), code


# ---------------------------
#   INFERIORES
# ---------------------------
@views.route('/cargar_estadisticas_inferiores', methods=['GET', 'POST'])
def cargar_estadisticas_inferiores(id_partido):

    partido = Partido.query.get_or_404(id_partido)
    jugadores_local = Jugador.query.filter_by(id_equipo=partido.id_equipo_local).all()
    jugadores_visitante = Jugador.query.filter_by(id_equipo=partido.id_equipo_visitante).all()

    if request.method == "POST":

        partido.goles_local = request.form.get("goles_local")
        partido.goles_visitante = request.form.get("goles_visitante")

        for jugador_id in request.form.getlist("jugador_id"):
            goles = request.form.get(f"goles_{jugador_id}", 0)
            amarilla = request.form.get(f"amarilla_{jugador_id}", 0)
            roja = request.form.get(f"roja_{jugador_id}", 0)

            estado = EstadoJugadorPartido(
                id_partido=id_partido,
                id_jugador=jugador_id,
                goles=int(goles),
                amarilla=int(amarilla),
                roja=int(roja)
            )
            db.session.add(estado)

        db.session.commit()
        flash("Estadísticas cargadas correctamente", "success")
        return redirect(url_for("views.fixture_inferiores"))

    return render_template(
        "plantillasAdmin/cargar_estadisticas_inferiores.html",
        partido=partido,
        jugadores_local=jugadores_local,
        jugadores_visitante=jugadores_visitante
    )


@views.route('/cargar_video', methods=['GET', 'POST'])
@login_required
def cargar_video():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))
    
    usuarios = Usuario.query.all()
    id_autor = current_user.id_usuario

    if request.method == 'POST':
        titulo = request.form['titulo_video']
        url = request.form['url']
        descripcion = request.form['descripcion']
        fecha_subida = request.form['fecha_subida']
        id_autor = request.form['id_autor']
        jornada_jugada = request.form['jornada_jugada']

        video = Video(
            titulo_video=titulo,
            url=url,
            descripcion=descripcion,
            fecha_subida=fecha_subida,
            id_autor=id_autor,
            jornada_jugada=jornada_jugada
        )

        db.session.add(video)
        db.session.commit()
        flash('✅ Video agregado correctamente.', 'success')
        return redirect(url_for('views.cargar_video'))

    return render_template('plantillasAdmin/cargar_video.html', usuario=current_user, usuarios=usuarios)


@views.route('/cargar_noticia', methods=['GET', 'POST'])
@login_required
def cargar_noticia():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))

    from app.models.models import Noticia, Usuario
    usuarios = Usuario.query.all()

    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        fecha_publicacion = request.form['fecha_publicacion']
        id_autor = request.form['id_autor']
        categoria = request.form['categoria']
        imagen_url = request.form['imagen_url']

        nueva_noticia = Noticia(
            titulo=titulo,
            contenido=contenido,
            fecha_publicacion=fecha_publicacion,
            id_autor=id_autor,
            categoria=categoria,
            imagen_url=imagen_url
        )

        db.session.add(nueva_noticia)
        db.session.commit()

        flash('📰 Noticia cargada correctamente.', 'success')
        return redirect(url_for('views.cargar_noticia'))

    return render_template('plantillasAdmin/cargar_noticia.html', usuario=current_user, usuarios=usuarios)

@views.route('/cargar_resultados_admin')
@login_required
def cargar_resultados_admin():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))
    return render_template('plantillasAdmin/cargar_resultados.html', usuario=current_user)