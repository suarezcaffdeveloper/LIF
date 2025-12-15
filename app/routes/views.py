from flask import Blueprint, current_app,render_template, jsonify, json,request, redirect, url_for, flash, abort
from ..models.models import (
    Equipo, Partido, Jugador, Club, Video, Noticia, Usuario, JugadorEquipo, TablaPosiciones,
     EstadoJugadorPartido, Temporada, Torneo, Fase
)
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
#import jsonify
from ..database.db import db
from sqlalchemy import func, or_, and_
import datetime
from sqlalchemy.orm import joinedload
from app.utils.email_utils import enviar_mail_bienvenida, enviar_mail_jornada, jornada_completa
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

views = Blueprint('views', __name__)

@views.route('/')
def index():
    clubes = Club.query.all()

    # Últimas 6 noticias ordenadas por fecha
    noticias = Noticia.query.order_by(Noticia.fecha_publicacion.desc()).limit(3).all()

    # Últimos 6 videos
    videos = Video.query.order_by(Video.fecha_subida.desc()).limit(3).all()

    return render_template(
        'index.html',
        clubes=clubes,
        noticias=noticias,
        videos=videos
    )
  
@views.route('/noticias')
def todas_noticias():
    noticias = Noticia.query.order_by(Noticia.fecha_publicacion.desc()).all()
    return render_template('noticias.html', noticias=noticias)


@views.route('/videos')
def todos_videos():
    videos = Video.query.order_by(Video.fecha_subida.desc()).all()
    return render_template('videos.html', videos=videos)


# ============================
# VISTA PANEL CARGA TORNEOS, FASES Y TEMPORADAS
# ============================
@views.route('/cargar_parametros', methods=['GET'])
def cargar_parametros_view():
    torneos = Torneo.query.order_by(Torneo.nombre).all()
    fases = Fase.query.order_by(Fase.nombre).all()
    temporadas = Temporada.query.order_by(Temporada.nombre).all()
    
    return render_template(
        'plantillasAdmin/cargar_parametros.html',
        torneos=torneos,
        fases=fases,
        temporadas=temporadas
    )

@views.route('/admin/temporadas', methods=['GET'])
def administrar_temporadas_view():
    temporadas = Temporada.query.order_by(Temporada.nombre.desc()).all()
    return render_template("plantillasAdmin/administrar_temporadas.html", temporadas=temporadas)

@views.route('/admin/temporadas', methods=['POST'])
def crear_temporada():
    nombre = request.form.get("nombre")

    if not nombre or not nombre.isdigit():
        flash("Nombre de temporada inválido.", "danger")
        return redirect(url_for("views.administrar_temporadas_view"))

    # Convertir a int
    nombre_int = int(nombre)

    # Desactivar la temporada activa actual
    temporada_activa = Temporada.query.filter_by(activa=True).first()
    if temporada_activa:
        temporada_activa.activa = False
        db.session.add(temporada_activa)

    # Crear la nueva temporada y activarla
    nueva_temporada = Temporada(nombre=nombre_int, activa=True)
    db.session.add(nueva_temporada)
    db.session.commit()  # Necesitamos commit para obtener el ID de la temporada

    # Crear torneos automáticamente
    torneos = []
    for torneo_nombre in ["Apertura", "Clausura"]:
        torneo = Torneo(nombre=torneo_nombre, temporada_id=nueva_temporada.id)
        db.session.add(torneo)
        torneos.append(torneo)

    db.session.commit()  # Commit para obtener IDs de torneos

    # Crear fases automáticamente para cada torneo
    fases_predeterminadas = ["Regular", "Cuartos", "Semifinal", "Final", "Finalísima"]

    for torneo in torneos:
        for orden, fase_nombre in enumerate(fases_predeterminadas, start=1):
            fase = Fase(
                nombre=fase_nombre,
                torneo_id=torneo.id,
                orden=orden,
                ida_vuelta=(fase_nombre in ["Cuartos", "Semifinal", "Final", "Finalísima"])
            )
            db.session.add(fase)

    db.session.commit()

    flash(f"Temporada {nombre} creada y activada correctamente.", "success")
    return redirect(url_for("views.administrar_temporadas_view"))

# ============================
@views.route('/fixture/<bloque>')
@views.route('/fixture/<bloque>/<categoria>')
def fixture(bloque, categoria=None):
    TORNEO_APERTURA_ID = 9  # Reemplazar si cambia el torneo

    bloques = {
        "mayores": ["Primera", "Reserva"],
        "inferiores": ["Quinta", "Sexta", "Septima"]
    }

    if bloque not in bloques:
        flash("Bloque inválido", "danger")
        return redirect(url_for("views.index"))

    # Normalizamos categorías
    categorias_bloque_raw = bloques[bloque]
    categorias_bloque = [c.strip().lower() for c in categorias_bloque_raw]

    partidos = []

    # Si se pidió categoría específica
    if categoria:
        if categoria not in categorias_bloque_raw:
            flash("Categoría inválida", "danger")
            return redirect(url_for("views.index"))

        categoria_db = categoria.strip().lower()
        partidos = (
            Partido.query
            .filter(
                func.lower(func.trim(Partido.categoria)) == categoria_db,
                Partido.torneo_id == TORNEO_APERTURA_ID
            )
            .order_by(Partido.jornada, Partido.fecha_partido)
            .all()
        )
        titulo = f"Fixture {categoria}"
    else:
        # Bloque completo
        sub = (
            db.session.query(func.min(Partido.id).label("pid"))
            .filter(
                func.lower(func.trim(Partido.categoria)).in_(categorias_bloque),
                Partido.torneo_id == TORNEO_APERTURA_ID
            )
            .group_by(
                Partido.jornada,
                Partido.equipo_local_id,
                Partido.equipo_visitante_id
            )
        ).subquery()

        partidos = (
            Partido.query
            .filter(Partido.id.in_(sub))
            .order_by(Partido.jornada, Partido.fecha_partido)
            .all()
        )
        titulo = f"Fixture {bloque.capitalize()}"

    # Agrupar partidos por jornada
    fechas_partidos = {}
    for partido in partidos:
        fecha_key = f"Jornada {partido.jornada}"
        fechas_partidos.setdefault(fecha_key, []).append(partido)

    return render_template(
        "fixture_general.html",
        fechas_partidos=fechas_partidos,
        titulo=titulo,
        mostrar_resultados=True
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


# ========================== NUEVA FUNCIÓN ===============================
#   Calcula automáticamente:
#   - equipo con más goles (solo en la tabla mostrada)
#   - equipo con más amarillas (solo tabla mostrada)
#   - equipo con más rojas (solo tabla mostrada)
# ======================================================================

def calcular_estadisticas(goles, amarillas, rojas):
    goles_por_equipo = defaultdict(int)
    amarillas_por_equipo = defaultdict(int)
    rojas_por_equipo = defaultdict(int)

    # Sumatoria de GOLES (solo los que APARECEN en la tabla)
    for _, _, _, club, total in goles:
        goles_por_equipo[club] += total

    # Sumatoria de AMARILLAS
    for _, _, _, club, total in amarillas:
        amarillas_por_equipo[club] += total

    # Sumatoria de ROJAS
    for _, _, _, club, total in rojas:
        rojas_por_equipo[club] += total

    # Equipo con mejor goleadores
    mejor_goleo_equipo = max(goles_por_equipo, key=goles_por_equipo.get) if goles_por_equipo else "—"
    mejor_goleo_total = goles_por_equipo.get(mejor_goleo_equipo, 0)

    # Equipo más amonestado
    mas_amonestados_equipo = max(amarillas_por_equipo, key=amarillas_por_equipo.get) if amarillas_por_equipo else "—"
    mas_amonestados_total = amarillas_por_equipo.get(mas_amonestados_equipo, 0)

    # Equipo más expulsado
    mas_expulsados_equipo = max(rojas_por_equipo, key=rojas_por_equipo.get) if rojas_por_equipo else "—"
    mas_expulsados_total = rojas_por_equipo.get(mas_expulsados_equipo, 0)

    # 📌 Devolvemos TODO dentro de "stats"
    return {
        "stats": {
            "goles": {
                "titulo": "Equipo con más goles",
                "equipo": mejor_goleo_equipo,
                "valor": mejor_goleo_total,
                "icon": "⚽",
                "descripcion": "(Solo jugadores listados arriba)"
            },
            "amarillas": {
                "titulo": "Equipo con más amonestaciones",
                "equipo": mas_amonestados_equipo,
                "valor": mas_amonestados_total,
                "icon": "🟨",
                "descripcion": "(Solo jugadores listados arriba)"
            },
            "rojas": {
                "titulo": "Equipo con más expulsiones",
                "equipo": mas_expulsados_equipo,
                "valor": mas_expulsados_total,
                "icon": "🟥",
                "descripcion": "(Solo jugadores listados arriba)"
            }
        }
    }


# ========================== RUTA PRINCIPAL ==============================

@views.route('/goleadores/<categoria>')
def mostrar_estadisticas(categoria):

    goles = consulta_estadistica(EstadoJugadorPartido.cant_goles, categoria, limite=15)
    amarillas = consulta_estadistica(EstadoJugadorPartido.tarjetas_amarillas, categoria, limite=10)
    rojas = consulta_estadistica(EstadoJugadorPartido.tarjetas_rojas, categoria, limite=10)

    # Calculamos estadísticas basadas SOLO en lo que se muestra
    estad = calcular_estadisticas(goles, amarillas, rojas)

    return render_template(
        'goleadores.html',
        categoria=categoria,
        goles=goles,
        amarillas=amarillas,
        rojas=rojas,
        stats=estad["stats"]   # 👈 AHORA SÍ EXISTE Y FUNCIONA
    )

# -----------------------------------------# TABLA DE POSICIONES
# ===========================================
# RECALCULAR TABLA DE POSICIONES EN MEMORIA
# ===========================================
def recalcular_tabla_posiciones(categoria):
    """
    Recalcula la tabla de posiciones de la categoría indicada.
    Devuelve lista de equipos con estadísticas completas.
    """
    categoria = categoria.lower()

    # 1️⃣ Traer todos los equipos de la categoría
    equipos = Equipo.query.filter(func.lower(Equipo.categoria) == categoria).all()
    if not equipos:
        return []

    tabla = []
    for e in equipos:
        tabla.append({
            'id_equipo': e.id,
            'nombre_equipo': e.club.nombre,
            'categoria': e.categoria,
            'partidos_jugados': 0,
            'partidos_ganados': 0,
            'partidos_empatados': 0,
            'partidos_perdidos': 0,
            'goles_a_favor': 0,
            'goles_en_contra': 0,
            'cantidad_puntos': 0,
            'diferencia_gol': 0
        })

    equipos_map = {e['id_equipo']: e for e in tabla}

    # 2️⃣ Traer partidos jugados de esta categoría
    partidos = Partido.query.filter(
        func.lower(Partido.categoria) == categoria,
        Partido.jugado == True
    ).all()

    # 3️⃣ Recorrer partidos y calcular estadísticas
    for p in partidos:
        local = equipos_map.get(p.equipo_local_id)
        visita = equipos_map.get(p.equipo_visitante_id)
        if not local or not visita:
            continue

        # PJ
        local['partidos_jugados'] += 1
        visita['partidos_jugados'] += 1

        # GF / GC
        local['goles_a_favor'] += p.goles_local
        local['goles_en_contra'] += p.goles_visitante
        visita['goles_a_favor'] += p.goles_visitante
        visita['goles_en_contra'] += p.goles_local

        # Resultados y puntos
        if p.goles_local > p.goles_visitante:
            local['partidos_ganados'] += 1
            visita['partidos_perdidos'] += 1
            local['cantidad_puntos'] += 3
        elif p.goles_local < p.goles_visitante:
            visita['partidos_ganados'] += 1
            local['partidos_perdidos'] += 1
            visita['cantidad_puntos'] += 3
        else:
            local['partidos_empatados'] += 1
            visita['partidos_empatados'] += 1
            local['cantidad_puntos'] += 1
            visita['cantidad_puntos'] += 1

        # Diferencia de gol
        local['diferencia_gol'] = local['goles_a_favor'] - local['goles_en_contra']
        visita['diferencia_gol'] = visita['goles_a_favor'] - visita['goles_en_contra']

    # 4️⃣ Ordenar tabla
    tabla.sort(key=lambda x: (-x['cantidad_puntos'], -x['diferencia_gol'], -x['goles_a_favor'], x['nombre_equipo']))

    return tabla


# =========================
# CALCULAR RACHAS
# =========================
def calcular_rachas(tabla, categoria):
    """
    Devuelve un diccionario con rachas de los últimos 5 partidos de cada equipo.
    """
    rachas = {}
    for equipo in tabla:
        equipo_db = Equipo.query.filter(
            func.lower(Equipo.categoria) == categoria.lower(),
            Equipo.id == equipo['id_equipo']
        ).first()

        tendencia = []
        if equipo_db:
            # Últimos 5 partidos jugados
            partidos_ultimos = Partido.query.filter(
                func.lower(Partido.categoria) == categoria.lower(),
                Partido.jugado == True,
                or_(
                    Partido.equipo_local_id == equipo_db.id,
                    Partido.equipo_visitante_id == equipo_db.id
                )
            ).order_by(Partido.fecha_partido.desc()).limit(5).all()

            for p in partidos_ultimos:
                if p.equipo_local_id == equipo_db.id:
                    gf, gc = p.goles_local, p.goles_visitante
                else:
                    gf, gc = p.goles_visitante, p.goles_local

                if gf > gc:
                    tendencia.append("G")
                elif gf == gc:
                    tendencia.append("E")
                else:
                    tendencia.append("P")

        rachas[equipo['nombre_equipo']] = tendencia

    return rachas
# ===========================================
# RUTA DE RECALCULO MANUAL (DEBUG)
# ===========================================
@views.route('/recalcular_tabla/<categoria>')
def recalcular_tabla_manual(categoria):
    categoria = categoria.lower()
    categorias_validas = ['primera', 'reserva', 'quinta', 'sexta', 'septima']

    if categoria not in categorias_validas:
        return f"Categoría inválida: {categoria}", 400

    recalcular_tabla_posiciones(categoria)
    return f"Tabla {categoria} recalculada"


# ===========================================
# TABLA DE POSICIONES
# ===========================================
@views.route('/tabla_posiciones/<categoria>')
def tabla_posiciones(categoria):
    categoria = categoria.lower()
    categorias_validas = ['primera', 'reserva', 'quinta', 'sexta', 'septima']

    if categoria not in categorias_validas:
        flash("La categoría solicitada no existe.", "danger")
        return redirect(url_for('views.index'))

    tabla = recalcular_tabla_posiciones(categoria)

    if not tabla:
        flash(f"No hay datos cargados para {categoria}.", "warning")
        return render_template(
            'tabla_posiciones.html',
            tabla=[],
            categoria=categoria,
            stats=None,
            rachas={},
            cruces=[]
        )

    # Estadísticas destacadas
    stats = {
        "mas_goleador": max(tabla, key=lambda e: e['goles_a_favor']),
        "menos_goleado": min(tabla, key=lambda e: e['goles_en_contra']),
        "mejor_diferencia": max(tabla, key=lambda e: e['diferencia_gol']),
    }

    # Rachas
    rachas = calcular_rachas(tabla, categoria)

    # Cruces
    cruces = []
    if len(tabla) >= 8:
        cruces = [
            (tabla[0], tabla[7]),
            (tabla[1], tabla[6]),
            (tabla[2], tabla[5]),
            (tabla[3], tabla[4]),
        ]

    return render_template(
        'tabla_posiciones.html',
        tabla=tabla,
        categoria=categoria,
        stats=stats,
        rachas=rachas,
        cruces=cruces
    )

# -----------------------------------------
#LOGIN
# ---------------- REGISTRO ----------------
@views.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_completo = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        verifypassword = request.form['verifypassword']

        # 🔒 Rol fijo por seguridad
        rol = "usuario"

        # Validación de contraseñas
        if password != verifypassword:
            flash('Las contraseñas no coinciden.', 'warning')
            return render_template('register.html', nombre=nombre_completo, email=email)

        # Verificar email existente
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'warning')
            return render_template('register.html', nombre=nombre_completo, email=email)

        try:
            # Crear usuario
            nuevo_usuario = Usuario(
                nombre_completo=nombre_completo,
                email=email,
                rol=rol
            )
            nuevo_usuario.set_password(password)

            db.session.add(nuevo_usuario)
            db.session.commit()

            # Envío de email (no crítico)
            try:
                enviar_mail_bienvenida(email, nombre_completo)
            except Exception as e:
                print("⚠ Error enviando email:", e)
                flash(
                    "Usuario registrado, pero no se pudo enviar el email de bienvenida.",
                    "warning"
                )

            flash('Registro exitoso. Ahora podés iniciar sesión.', 'success')
            return redirect(url_for('views.login'))

        except Exception as e:
            db.session.rollback()
            print("❌ Error al registrar usuario:", e)
            flash("Ocurrió un error al registrar el usuario.", "danger")
            return redirect(url_for('views.register'))

    return render_template('register.html')



# ---------------- LOGIN ----------------
@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            flash("El email no está registrado.", "warning")
            return redirect(url_for('views.login'))

        # Verifica contraseña
        if not usuario.check_password(password):
            flash("Contraseña incorrecta.", "danger")
            return redirect(url_for('views.login'))

        # Iniciar sesión
        login_user(usuario)

        # Redirigir según el rol
        rol = usuario.rol.lower().strip()  # Normalizamos capitalización y espacios

        if rol == "administrador":
            return redirect(url_for('views.adminview'))
        
        if rol == "periodista":
            return redirect(url_for('views.panel_periodista'))

        # Si no es administrador → va a la página normal
        return redirect(url_for('views.index'))

    return render_template('login.html')


# ---------------- LOGOUT ----------------
@views.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('views.login'))

# ---------------- DASHBOARD ----------------
@views.route('/dashboard')
@login_required
def dashboard():
    role = current_user.rol

    if role == 'administrador':
        return render_template('adminview.html', usuario=current_user)

    if role == 'periodista':
        return render_template('panelperiodista.html', usuario=current_user)

    # usuario común
    return render_template('index.html', usuario=current_user)
    
#-------------------------PERIODISTA VIEW-----------------------
from functools import wraps

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.rol not in roles:
                return abort(403)  # acceso denegado
            return f(*args, **kwargs)
        return wrapper
    return decorator

@views.route('/panel_periodista')
@login_required
@role_required('periodista')
def panel_periodista():
    return render_template('panelperiodista.html')
from app.utils.email_utils import enviar_mail_periodista


import secrets
import string

def generar_password(longitud=10):
    """Genera una contraseña aleatoria segura."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

@views.route('/crear_periodista', methods=['GET', 'POST'])
@login_required
def crear_periodista():
    from app.utils.email_utils import enviar_mail_periodista

    if current_user.rol != "administrador":
        flash("No tienes permisos para acceder a esta página.", "danger")
        return redirect(url_for('views.dashboard'))

    if request.method == 'POST':
        nombre = request.form['nombre_completo']
        email = request.form['email']
        email_confirm = request.form['email_confirm']

        # Verificar que los emails coincidan
        if email != email_confirm:
            flash("Los correos electrónicos no coinciden.", "danger")
            # Renderizamos el template con los valores ingresados
            return render_template(
                "plantillasAdmin/crear_periodista.html",
                nombre=nombre,
                email=email
            )

        # Verificar si ya existe
        if Usuario.query.filter_by(email=email).first():
            flash("El email ya está registrado.", "danger")
            return render_template(
                "plantillasAdmin/crear_periodista.html",
                nombre=nombre,
                email=email
            )

        # Generar contraseña automáticamente
        import secrets, string
        caracteres = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(caracteres) for _ in range(12))

        periodista = Usuario(
            nombre_completo=nombre,
            email=email,
            rol='periodista'
        )
        periodista.set_password(password)
        db.session.add(periodista)
        db.session.commit()

        # Enviar mail con contraseña generada
        enviar_mail_periodista(email, nombre, password)

        flash("Periodista creado y credenciales enviadas por email.", "success")
        return redirect(url_for('views.crear_periodista'))

    # GET: simplemente renderizamos template vacío
    return render_template("plantillasAdmin/crear_periodista.html", nombre="", email="")

    
    

# ---------------- ADMIN VIEW ----------------
@views.route('/adminview')
@login_required
def adminview():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))
    return render_template('adminview.html', usuario=current_user)



#-------------------------CARGAR CLUBES-----------------------#
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


#-------------------------CARGAR EQUIPOS-----------------------#    
@views.route("/cargar_equipos", methods=["GET", "POST"])
def cargar_equipos():
    if request.method == "POST":

        try:
            club_id = int(request.form.get("club_id"))
        except (TypeError, ValueError):
            flash("Club inválido.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        categoria = request.form.get("categoria")

        if not categoria:
            flash("Debe seleccionar una categoría.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        # Verificar club
        club = Club.query.get(club_id)
        if not club:
            flash("El club seleccionado no existe.", "danger")
            return redirect(url_for("views.cargar_equipos"))

        # Validar duplicado
        existe = Equipo.query.filter_by(club_id=club_id, categoria=categoria).first()
        if existe:
            flash(f"La categoría {categoria} ya está cargada para este club.", "warning")
            return redirect(url_for("views.cargar_equipos"))

        # Crear equipo
        nuevo_equipo = Equipo(club_id=club_id, categoria=categoria)

        db.session.add(nuevo_equipo)
        db.session.commit()

        flash("Equipo cargado correctamente.", "success")
        return redirect(url_for("views.cargar_equipos"))

    # GET → cargar clubes
    clubes = Club.query.order_by(Club.nombre.asc()).all()
    return render_template("plantillasAdmin/cargar_equipos.html", clubes=clubes)


@views.route("/categorias_cargadas/<int:club_id>")
def categorias_cargadas(club_id):
    equipos = Equipo.query.filter_by(club_id=club_id).all()
    categorias = [e.categoria for e in equipos]
    return jsonify(categorias)


#-------------------------CARGAR JUGADORES-----------------------#
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
                fecha_nac = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
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

    return jsonify({
        "jugadores": [
            {
                "numero_carnet": j.numero_carnet,
                "nombre": j.nombre,
                "apellido": j.apellido
            }
            for j in jugadores
        ],
        "equipos": [
            {
                "id": e.id,
                "categoria": e.categoria
            }
            for e in equipos
        ]
    })

# ============================================================
#   ASIGNAR JUGADOR A CATEGORÍA
# ============================================================
@views.route('/asignar_jugador_categoria', methods=['GET', 'POST'])
def asignar_jugador_categoria():
    clubes = Club.query.order_by(Club.nombre).all()

    if request.method == 'POST':

        es_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        numero_carnet = request.form.get('numero_carnet')
        equipo_id = request.form.get('equipo_id')

        if not numero_carnet or not equipo_id:
            mensaje = "Debe seleccionar un jugador y una categoría."
            if es_ajax:
                return jsonify({"ok": False, "msg": mensaje}), 400
            flash(mensaje, "danger")
            return redirect(url_for('views.asignar_jugador_categoria'))

        existe = JugadorEquipo.query.filter_by(
            numero_carnet=numero_carnet,
            equipo_id=equipo_id
        ).first()

        if existe:
            mensaje = "Este jugador ya está asignado a esa categoría."
            if es_ajax:
                return jsonify({"ok": False, "msg": mensaje}), 400
            flash(mensaje, "warning")
            return redirect(url_for('views.asignar_jugador_categoria'))

        nuevo = JugadorEquipo(
            numero_carnet=numero_carnet,
            equipo_id=equipo_id
        )

        db.session.add(nuevo)
        db.session.commit()

        jugador = Jugador.query.filter_by(numero_carnet=numero_carnet).first()
        nombre_completo = f"{jugador.apellido}, {jugador.nombre}"

        if es_ajax:
            return jsonify({
                "ok": True,
                "nombre": nombre_completo
            })

        flash("Jugador asignado correctamente.", "success")
        return redirect(url_for('views.asignar_jugador_categoria'))

    return render_template("plantillasAdmin/cargar_jugador_equipo.html", clubes=clubes)


#-------------------------JUGADORES POR EQUIPO-----------------------#
@views.route("/api/jugadores_por_equipo/<int:equipo_id>")
def jugadores_por_equipo(equipo_id):
    try:
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

    except Exception as e:
        print("❌ ERROR jugadores_por_equipo:", e)
        return jsonify({"error": str(e)}), 500

@views.route('/info_jugador/<int:carnet>')
def info_jugador(carnet):

    j = Jugador.query.get(carnet)

    if not j:
        return jsonify({"error": "Jugador no encontrado"}), 404

    return jsonify({
        "numero_carnet": j.numero_carnet,
        "nombre": j.nombre,
        "apellido": j.apellido,
        "fecha_nacimiento": j.fecha_nacimiento.strftime("%d/%m/%Y") if j.fecha_nacimiento else "-",
        "club": j.club.nombre
    })


#-------------------------CARGAR FIXTURE MAYORES-----------------------#
# ============================
# PANEL DE CARGA DE PARTIDOS
# ============================
@views.route('/cargar_fixture_mayores', methods=['GET'])
def cargar_fixture_mayores_view():
    temporada_activa = Temporada.query.filter_by(activa=True).first()
    if not temporada_activa:
        flash("No hay temporada activa. Primero cree una temporada.", "danger")
        return redirect(url_for("views.administrar_temporadas_view"))

    torneos = Torneo.query.filter_by(temporada_id=temporada_activa.id).order_by(Torneo.nombre).all()
    fases = Fase.query.join(Torneo)\
        .filter(Torneo.temporada_id == temporada_activa.id)\
        .with_entities(Fase.id, Fase.nombre, Fase.orden)\
        .group_by(Fase.nombre, Fase.id, Fase.orden)\
        .order_by(Fase.orden).all()

    clubes = Club.query.order_by(Club.nombre).all()
    equipos = Equipo.query.filter(Equipo.categoria.in_(["primera", "reserva"])).order_by(Equipo.club_id).all()

    # Equipos por club y categoría
    equipos_por_club = {}
    for e in equipos:
        equipos_por_club.setdefault(e.club_id, {})[e.categoria] = e.id

    # Cantidad de equipos de Primera
    total_equipos = Equipo.query.filter_by(categoria="primera").count()
    # Número de jornadas (ida y vuelta)
    total_jornadas = max((total_equipos - 1) * 2, 0)

    return render_template(
        "plantillasAdmin/cargar_fixture_mayores.html",
        torneos=torneos,
        fases=fases,
        clubes=clubes,
        equipos_por_club=equipos_por_club,
        total_jornadas=total_jornadas,
        temporada_activa=temporada_activa
    )


# =========================
# VALIDAR FASE PARA CARGA
# =========================
def validar_fase_para_carga(torneo_id, fase_id):
    fase = Fase.query.get(fase_id)
    if not fase:
        return False, "Fase inválida"

    if fase.orden == 1:
        return True, ""

    # Validar fases anteriores
    fases_previas = Fase.query.filter(Fase.torneo_id==torneo_id, Fase.orden < fase.orden).all()
    for f in fases_previas:
        partidos_fase = Partido.query.filter_by(fase_id=f.id).all()
        if not partidos_fase:
            return False, f"No se puede cargar {fase.nombre}. No hay partidos cargados de la fase {f.nombre}."
        if any(not p.jugado for p in partidos_fase):
            return False, f"No se puede cargar {fase.nombre}. Todos los partidos de la fase {f.nombre} deben estar jugados."
    return True, ""


# =========================
# GUARDAR PARTIDO MAYORES
# =========================
@views.route('/guardar_partido_mayores', methods=['POST'])
@login_required
def guardar_partido_mayores():
    data = request.form
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400

    try:
        jornada = int(data.get("jornada") or 0)
        local_id = int(data.get("club_local") or 0)
        visitante_id = int(data.get("club_visitante") or 0)

        if not jornada or not local_id or not visitante_id:
            return jsonify({"error": "Complete todos los campos."}), 400
        if local_id == visitante_id:
            return jsonify({"error": "El club local y visitante no pueden ser el mismo."}), 400

        fecha = datetime.strptime(data.get("fecha"), "%Y-%m-%d").date() if data.get("fecha") else None
        hora = datetime.strptime(data.get("hora"), "%H:%M").time() if data.get("hora") else None

        # Traer equipos de Primera y Reserva
        categorias = ["primera", "reserva"]
        equipos = {}
        for cat in categorias:
            eq_local = Equipo.query.filter_by(club_id=local_id, categoria=cat).first()
            eq_visita = Equipo.query.filter_by(club_id=visitante_id, categoria=cat).first()
            if not eq_local or not eq_visita:
                return jsonify({"error": f"Faltan equipos de {cat} para uno de los clubes."}), 400
            equipos[f"{cat}_local"] = eq_local
            equipos[f"{cat}_visita"] = eq_visita

        # Traer torneos Apertura y Clausura
        torneo_apertura = Torneo.query.filter_by(nombre="Apertura").first()
        torneo_clausura = Torneo.query.filter_by(nombre="Clausura").first()
        if not torneo_apertura or not torneo_clausura:
            return jsonify({"error": "No se encontraron torneos Apertura o Clausura."}), 400

        generados = []

        # Validar cruces existentes en Apertura
        for cat in categorias:
            local_eq = equipos[f"{cat}_local"]
            visita_eq = equipos[f"{cat}_visita"]
            existente = Partido.query.filter(
                Partido.torneo_id == torneo_apertura.id,
                Partido.categoria == cat,
                ((Partido.equipo_local_id==local_eq.id) & (Partido.equipo_visitante_id==visita_eq.id)) |
                ((Partido.equipo_local_id==visita_eq.id) & (Partido.equipo_visitante_id==local_eq.id))
            ).first()
            if existente:
                return jsonify({"error": f"El cruce {local_eq.club.nombre} vs {visita_eq.club.nombre} ya fue cargado en {cat}."}), 400

        # Función auxiliar para crear partidos
        def crear_partido(local_eq, visita_eq, torneo_obj, categoria):
            p = Partido(
                fecha_partido=fecha,
                hora_partido=hora,
                jornada=jornada,
                categoria=categoria,
                equipo_local_id=local_eq.id,
                equipo_visitante_id=visita_eq.id,
                torneo_id=torneo_obj.id,
                fase_id=None,
                jugado=False
            )
            db.session.add(p)
            return {
                "categoria": categoria,
                "local": local_eq.club.nombre,
                "visitante": visita_eq.club.nombre,
                "torneo": torneo_obj.nombre,
                "fase": ""
            }

        # Crear partidos Apertura
        for cat in categorias:
            generados.append(crear_partido(equipos[f"{cat}_local"], equipos[f"{cat}_visita"], torneo_apertura, cat))
        # Crear partidos Clausura invertidos
        for cat in categorias:
            generados.append(crear_partido(equipos[f"{cat}_visita"], equipos[f"{cat}_local"], torneo_clausura, cat))

        db.session.commit()
        return jsonify({"success": True, "msg": f"Se generaron {len(generados)} partidos.", "partidos": generados})

    except Exception as e:
        db.session.rollback()
        print("❌ Error guardar_partido_mayores:", e)
        return jsonify({"error": "Error interno del servidor"}), 500


# =========================
# FIXTURE OCUPADOS MAYORES
# =========================
@views.route('/fixture/ocupados/<int:jornada>', methods=['GET'])
def fixture_ocupados(jornada):
    partidos = Partido.query.filter_by(jornada=jornada).filter(
        func.lower(func.trim(Partido.categoria)).in_(["primera", "reserva"])
    ).all()

    ocupados_club_ids = set()
    cruces = {}

    for p in partidos:
        eq_local = Equipo.query.get(p.equipo_local_id)
        eq_visita = Equipo.query.get(p.equipo_visitante_id)
        if not eq_local or not eq_visita or not eq_local.club or not eq_visita.club:
            continue

        # IDs ordenados para evitar duplicados
        local_id, visita_id = sorted([eq_local.club.id, eq_visita.club.id])
        ocupados_club_ids.update([local_id, visita_id])
        clave = (local_id, visita_id)

        if clave not in cruces:
            cruces[clave] = {
                "local_club_id": eq_local.club.id,
                "local_club_nombre": eq_local.club.nombre,
                "visitante_club_id": eq_visita.club.id,
                "visitante_club_nombre": eq_visita.club.nombre,
                "fecha": p.fecha_partido.isoformat() if p.fecha_partido else None,
                "hora": p.hora_partido.strftime("%H:%M") if p.hora_partido else None,
                "categorias": set(),
                "jugado": p.jugado,
                "torneo": p.torneo.nombre if p.torneo else "",
                "fase": p.fase.nombre if p.fase else ""
            }

        cruces[clave]["categorias"].add(p.categoria.strip().lower())
        if p.jugado:
            cruces[clave]["jugado"] = True

    resultados = []
    for c in cruces.values():
        c["categorias"] = list(c["categorias"])
        c["local"] = c["local_club_nombre"]
        c["visitante"] = c["visitante_club_nombre"]
        resultados.append(c)

    return jsonify({"ocupados": list(ocupados_club_ids), "partidos": resultados})




# ====================================================
# CARGAR FIXTURE INFERIORES
# ====================================================
@views.route('/cargar_fixture_inferiores', methods=['GET'])
@login_required
def cargar_fixture_inferiores():
    clubes = Club.query.order_by(Club.nombre).all()
    total_jornadas = len(clubes) - 1

    return render_template(
        'plantillasAdmin/cargar_fixture_inferiores.html',
        clubes=clubes,
        total_jornadas=total_jornadas
    )


# =========================
# FIXTURE OCUPADOS INFERIORES
# =========================
CATEGORIAS_INFERIORES = ["Quinta", "Sexta", "Septima"]
@views.route("/fixture_ocupados_inferiores/<int:jornada>")
@login_required
def fixture_ocupados_inferiores(jornada):
    """
    Retorna clubes ocupados y partidos cargados de la jornada para categorías inferiores.
    """
    try:
        categorias_validas = {c.lower() for c in CATEGORIAS_INFERIORES}

        partidos = (
            Partido.query
            .filter(
                Partido.jornada == jornada,
                func.lower(Partido.categoria).in_(categorias_validas)
            )
            .all()
        )

        cruces = {}
        ocupados_club_ids = set()

        for p in partidos:
            eq_local = p.equipo_local
            eq_visit = p.equipo_visitante
            if not eq_local or not eq_visit or not eq_local.club or not eq_visit.club:
                continue

            local_id = eq_local.club.id
            visitante_id = eq_visit.club.id
            ocupados_club_ids.update([local_id, visitante_id])

            clave = tuple(sorted([local_id, visitante_id]))
            if clave not in cruces:
                cruces[clave] = {
                    "local_club_id": local_id,
                    "local_club_nombre": eq_local.club.nombre,
                    "visitante_club_id": visitante_id,
                    "visitante_club_nombre": eq_visit.club.nombre,
                    "fecha": p.fecha_partido.isoformat() if p.fecha_partido else None,
                    "hora": p.hora_partido.strftime("%H:%M") if p.hora_partido else None,
                    "categorias": [],
                    "jugado": p.jugado
                }
            cat = p.categoria.lower()
            if cat not in cruces[clave]["categorias"]:
                cruces[clave]["categorias"].append(cat)

            if p.jugado:
                cruces[clave]["jugado"] = True

        return jsonify({
            "ok": True,
            "ocupados": list(ocupados_club_ids),
            "partidos": list(cruces.values())
        })

    except Exception as e:
        print("❌ ERROR fixture_ocupados_inferiores:", e)
        return jsonify({"ok": False, "ocupados": [], "partidos": [], "msg": "Error interno del servidor"}), 500


# ====================================================
# GUARDAR PARTIDO INFERIORES
# ====================================================
@views.route('/guardar_partido_inferiores', methods=['POST'])
@login_required
def guardar_partido_inferiores():
    data = request.form or request.get_json()
    if not data:
        return jsonify({"error": "No se enviaron datos"}), 400

    try:
        torneo_apertura = Torneo.query.filter_by(nombre="Apertura").first()
        torneo_clausura = Torneo.query.filter_by(nombre="Clausura").first()
        if not torneo_apertura:
            return jsonify({"error": "No se encontró el torneo Apertura"}), 400

        jornada = int(data.get("jornada"))
        local_id = int(data.get("club_local") or data.get("local_id"))
        visitante_id = int(data.get("club_visitante") or data.get("visitante_id"))
        if local_id == visitante_id:
            return jsonify({"error": "El club local y visitante no pueden ser el mismo."}), 400

        fecha_raw = data.get("fecha")
        hora_raw = data.get("hora")
        fecha = datetime.strptime(fecha_raw, "%Y-%m-%d").date() if fecha_raw else None
        hora = datetime.strptime(hora_raw, "%H:%M").time() if hora_raw else None

        equipos_local = Equipo.query.filter_by(club_id=local_id).all()
        equipos_visit = Equipo.query.filter_by(club_id=visitante_id).all()
        categorias_validas = {c.lower() for c in CATEGORIAS_INFERIORES}

        categorias_local = {e.categoria.lower(): e for e in equipos_local if e.categoria and e.categoria.lower() in categorias_validas}
        categorias_visit = {e.categoria.lower(): e for e in equipos_visit if e.categoria and e.categoria.lower() in categorias_validas}

        categorias_comunes = set(categorias_local.keys()).intersection(categorias_visit.keys())
        if not categorias_comunes:
            return jsonify({"error": "Los clubes no comparten categorías de inferiores."}), 400

        generados = []

        for categoria_key in categorias_comunes:
            eq_local = categorias_local[categoria_key]
            eq_visit = categorias_visit[categoria_key]

            ya_enfrentados = Partido.query.filter(
                func.lower(Partido.categoria) == categoria_key,
                Partido.torneo_id.in_([torneo_apertura.id, torneo_clausura.id if torneo_clausura else -1]),
                ((Partido.equipo_local_id == eq_local.id) & (Partido.equipo_visitante_id == eq_visit.id)) |
                ((Partido.equipo_local_id == eq_visit.id) & (Partido.equipo_visitante_id == eq_local.id))
            ).first()
            if ya_enfrentados:
                continue

            # Apertura
            p_apertura = Partido(
                jornada=jornada,
                fecha_partido=fecha,
                hora_partido=hora,
                categoria=eq_local.categoria,
                equipo_local_id=eq_local.id,
                equipo_visitante_id=eq_visit.id,
                torneo_id=torneo_apertura.id,
                jugado=False
            )
            db.session.add(p_apertura)
            generados.append({"categoria": eq_local.categoria, "local": eq_local.club.nombre, "visitante": eq_visit.club.nombre, "torneo": "Apertura"})

            # Clausura invertido
            if torneo_clausura:
                p_clausura = Partido(
                    jornada=jornada,
                    fecha_partido=fecha,
                    hora_partido=hora,
                    categoria=eq_local.categoria,
                    equipo_local_id=eq_visit.id,
                    equipo_visitante_id=eq_local.id,
                    torneo_id=torneo_clausura.id,
                    jugado=False
                )
                db.session.add(p_clausura)
                generados.append({"categoria": eq_local.categoria, "local": eq_visit.club.nombre, "visitante": eq_local.club.nombre, "torneo": "Clausura"})

        if not generados:
            return jsonify({"error": "No se generaron partidos nuevos."}), 400

        db.session.commit()
        return jsonify({"success": True, "msg": f"Se generaron {len(generados)} partidos.", "partidos": generados})

    except Exception as e:
        db.session.rollback()
        print("❌ ERROR guardar_partido_inferiores:", e)
        return jsonify({"error": "Error interno del servidor"}), 500

    
# -----------------------------------------
# 1) Página de carga
# -----------------------------------------
@views.route('/cargar_estadisticas_mayores')
def cargar_estadisticas_mayores():
    jornadas = db.session.query(Partido.jornada)\
        .join(Torneo)\
        .join(Temporada)\
        .filter(Temporada.activa == True, Torneo.nombre == "Apertura")\
        .distinct().order_by(Partido.jornada).all()
    jornadas = [j[0] for j in jornadas]
    return render_template('plantillasAdmin/cargar_estadisticas_mayores.html', jornadas=jornadas)


# -----------------------------------------
# 2) Cruces pendientes (solo torneo activo)
# -----------------------------------------
@views.route("/api/cruces_pendientes_mayores/<int:jornada>")
def cruces_pendientes_mayores(jornada):
    torneo_activo = Torneo.query.join(Temporada)\
        .filter(Temporada.activa==True, Torneo.nombre=="Apertura").first()
    if not torneo_activo:
        return jsonify([])

    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.torneo_id == torneo_activo.id,
        Partido.categoria.in_(["primera","reserva"]),
        Partido.jugado == False
    ).all()

    cruces = {}
    for p in partidos:
        if not p.equipo_local or not p.equipo_visitante:
            continue
        # clave única por combinación de clubes (sin importar el orden)
        key = tuple(sorted([p.equipo_local.club_id, p.equipo_visitante.club_id]))
        if key not in cruces:
            cruces[key] = {
                "texto": f"{p.equipo_local.club.nombre} vs {p.equipo_visitante.club.nombre}",
                "id_representativa": p.id,
                "primera": None,
                "reserva": None
            }
        if p.categoria.lower() == "primera":
            cruces[key]["primera"] = p.id
        elif p.categoria.lower() == "reserva":
            cruces[key]["reserva"] = p.id

    respuesta = []
    for c in cruces.values():
        if c["primera"] or c["reserva"]:
            respuesta.append({
                "id": c["id_representativa"],
                "texto": c["texto"],
                "primera": c["primera"],
                "reserva": c["reserva"]
            })
    return jsonify(respuesta)


# -----------------------------------------
# 3) Información de un cruce
# -----------------------------------------
@views.route("/api/info_cruce/<int:cruce_id>")
def info_cruce(cruce_id):
    try:
        partido_base = Partido.query.get(cruce_id)
        if not partido_base:
            return jsonify({"error": "Cruce no encontrado"}), 404

        jornada = partido_base.jornada
        torneo_activo = Torneo.query.join(Temporada)\
            .filter(Temporada.activa==True, Torneo.nombre=="Apertura").first()
        if not torneo_activo or partido_base.torneo_id != torneo_activo.id:
            return jsonify({"error": "Este cruce no pertenece al torneo activo"}), 400

        # Identificar clubes
        local_club_id = partido_base.equipo_local.club_id
        visitante_club_id = partido_base.equipo_visitante.club_id

        # Buscar todos los equipos de ambos clubes
        equipos_local = Equipo.query.filter_by(club_id=local_club_id).all()
        equipos_visitante = Equipo.query.filter_by(club_id=visitante_club_id).all()

        ids_equipos_local = [e.id for e in equipos_local]
        ids_equipos_visitante = [e.id for e in equipos_visitante]

        # Buscar partidos Primera/Reserva entre esos equipos en la misma jornada y torneo activo
        partidos = Partido.query.filter(
            Partido.jornada == jornada,
            Partido.torneo_id == torneo_activo.id,
            Partido.equipo_local_id.in_(ids_equipos_local),
            Partido.equipo_visitante_id.in_(ids_equipos_visitante),
            Partido.categoria.in_(["primera", "reserva"])
        ).all()

        partido_primera = next((p for p in partidos if p.categoria.lower() == "primera"), None)
        partido_reserva = next((p for p in partidos if p.categoria.lower() == "reserva"), None)

        return jsonify({
            "primera": {
                "id": partido_primera.id if partido_primera else None,
                "jugado": partido_primera.jugado if partido_primera else True,
                "local": partido_primera.equipo_local_id if partido_primera else None,
                "visitante": partido_primera.equipo_visitante_id if partido_primera else None,
            },
            "reserva": {
                "id": partido_reserva.id if partido_reserva else None,
                "jugado": partido_reserva.jugado if partido_reserva else True,
                "local": partido_reserva.equipo_local_id if partido_reserva else None,
                "visitante": partido_reserva.equipo_visitante_id if partido_reserva else None,
            },
            "local_id": local_club_id,
            "local_nombre": partido_base.equipo_local.club.nombre,
            "visitante_id": visitante_club_id,
            "visitante_nombre": partido_base.equipo_visitante.club.nombre,
            "jornada": jornada
        })
    except Exception as e:
        print("❌ ERROR info_cruce:", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------------------
# 4) Guardar resultados (reutilizable)
# -----------------------------------------
def validar_y_guardar_estadisticas(data, categoria):
    try:
        id_partido = int(data.get("partido_id"))
    except Exception:
        return {"success": False, "message": "partido_id inválido"}, 400

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

    # 2. Validar torneo activo (solo Apertura)
    torneo_activo = Torneo.query.join(Temporada).filter(
        Temporada.activa==True, Torneo.nombre=="Apertura"
    ).first()
    if not torneo_activo or partido.torneo_id != torneo_activo.id:
        return {"success": False, "message": "Este endpoint solo guarda partidos del Apertura."}, 400

    # 3. Validar categoría
    if partido.categoria.lower() != categoria.lower():
        return {"success": False, "message": f"Este endpoint solo guarda datos de {categoria.capitalize()}."}, 400

    # 4. Verificar si ya fue jugado
    if partido.jugado:
        return {"success": False, "message": f"El partido de {categoria.capitalize()} ya fue cargado."}, 400

    # 5. Verificar suma de goles
    total_local = sum(int(g.get("goles", 0)) for g in goleadores_local)
    total_visitante = sum(int(g.get("goles", 0)) for g in goleadores_visitante)
    if total_local != goles_local or total_visitante != goles_visitante:
        return {"success": False, "message": "Los goles no coinciden con los goleadores."}, 400

    # 6. Guardar goles y marcar jugado
    partido.goles_local = goles_local
    partido.goles_visitante = goles_visitante
    partido.jugado = True
    db.session.flush()

    # 7. Estadísticas por jugador
    stats = {}
    def ensure(jid):
        if jid not in stats:
            stats[jid] = {"cant_goles": 0, "tarjetas_amarillas": 0, "tarjetas_rojas": 0}

    for item in (goleadores_local + goleadores_visitante):
        jugador_id = item.get("jugador_id")
        if jugador_id is None:
            continue
        goles = int(item.get("goles", 0))
        ensure(jugador_id)
        stats[jugador_id]["cant_goles"] += goles

    for j in amarillas_local + amarillas_visitante:
        ensure(j)
        stats[j]["tarjetas_amarillas"] += 1

    for j in rojas_local + rojas_visitante:
        ensure(j)
        stats[j]["tarjetas_rojas"] += 1

    # 8. Guardar en DB y enviar mail si corresponde
    try:
        for jugador_id, valores in stats.items():
            registro = EstadoJugadorPartido(
                id_jugador=int(jugador_id),
                id_partido=int(id_partido),
                cant_goles=int(valores["cant_goles"]),
                tarjetas_amarillas=int(valores["tarjetas_amarillas"]),
                tarjetas_rojas=int(valores["tarjetas_rojas"])
            )
            db.session.add(registro)

        db.session.flush()  # flush antes de enviar mail

        # 🔥 Solo verifica jornadas de Mayores
        if categoria.lower() == "mayores" and jornada_completa(partido.jornada, categoria):
            usuarios = Usuario.query.filter_by(rol="usuario").all()
            try:
                enviar_mail_jornada(usuarios, partido.jornada, categoria)
            except Exception as e:
                print("❌ ERROR al enviar mail:", e)

        db.session.commit()

        recalcular_tabla_posiciones(partido.categoria)

        return {"success": True, "message": "Estadísticas guardadas correctamente"}, 200

    except IntegrityError as e:
        db.session.rollback()
        msg = str(e.orig) if getattr(e, "orig", None) else str(e)
        if "estado_jugador_partido_pkey" in msg or "duplicate key value" in msg.lower():
            return {"success": False, "message": "Ya existen estadísticas para alguno de estos jugadores en este partido."}, 400
        return {"success": False, "message": "Error de integridad en la base de datos"}, 500
    except Exception as e:
        db.session.rollback()
        print("❌ ERROR guardar estadisticas:", e)
        return {"success": False, "message": "Error interno del servidor"}, 500



# -----------------------------------------
# 5) Endpoints específicos para cada categoría
# -----------------------------------------
@views.route("/api/guardar_primera", methods=["POST"])
def guardar_primera():
    data = request.get_json() or {}
    resp, code = validar_y_guardar_estadisticas(data, "primera")
    return jsonify(resp), code

@views.route("/api/guardar_reserva", methods=["POST"])
def guardar_reserva():
    data = request.get_json() or {}
    resp, code = validar_y_guardar_estadisticas(data, "reserva")
    return jsonify(resp), code

# ---------------------------
#   INFERIORES
# ---------------------------
# ====================================================
# CARGAR INTERFAZ
# ====================================================
# ====================================================
# CARGAR ESTADÍSTICAS INFERIORES
# ====================================================
@views.route('/cargar_estadisticas_inferiores')
def cargar_estadisticas_inferiores():
    categorias_inferiores = ["quinta", "sexta", "septima"]

    jornadas = (
        db.session.query(Partido.jornada)
        .filter(db.func.lower(Partido.categoria).in_(categorias_inferiores))
        .distinct()
        .order_by(Partido.jornada)
        .all()
    )

    jornadas = [j[0] for j in jornadas]

    return render_template(
        'plantillasAdmin/cargar_estadisticas_inferiores.html',
        jornadas=jornadas
    )

# ====================================================
# CRUCES POR JORNADA
# ====================================================
@views.route("/api/cruces_por_jornada_inferiores/<int:jornada>")
def cruces_por_jornada_inferiores(jornada):
    categorias = ["quinta", "sexta", "septima"]

    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        db.func.lower(Partido.categoria).in_(categorias)
    ).all()

    print("Jornada seleccionada:", jornada)
    print("Partidos encontrados:", partidos)

    cruces = {}

    for p in partidos:
        local = p.equipo_local.club.nombre if p.equipo_local and p.equipo_local.club else "Desconocido"
        visitante = p.equipo_visitante.club.nombre if p.equipo_visitante and p.equipo_visitante.club else "Desconocido"
        key = f"{local} vs {visitante}"

        if key not in cruces:
            cruces[key] = {
                "local": local,
                "visitante": visitante,
                "id_quinta": None,
                "id_sexta": None,
                "id_septima": None
            }

        cat = p.categoria.lower()
        if cat == "quinta":
            cruces[key]["id_quinta"] = p.id
        elif cat == "sexta":
            cruces[key]["id_sexta"] = p.id
        elif cat == "septima":
            cruces[key]["id_septima"] = p.id

    respuesta = []
    for c in cruces.values():
        id_repr = c["id_quinta"] or c["id_sexta"] or c["id_septima"]
        respuesta.append({
            "id": id_repr,
            "local": c["local"],
            "visitante": c["visitante"],
            "id_quinta": c["id_quinta"],
            "id_sexta": c["id_sexta"],
            "id_septima": c["id_septima"]
        })

    return jsonify(respuesta)

# ====================================================
# INFO CRUCE
# ====================================================
@views.route("/api/info_cruce_inferiores/<int:id_representativo>")
def info_cruce_inferiores(id_representativo):
    p = Partido.query.get_or_404(id_representativo)

    return jsonify({
        "jornada": p.jornada,
        "local_id": p.equipo_local.club.id if p.equipo_local and p.equipo_local.club else None,
        "visitante_id": p.equipo_visitante.club.id if p.equipo_visitante and p.equipo_visitante.club else None,
        "local_nombre": p.equipo_local.club.nombre if p.equipo_local and p.equipo_local.club else "Desconocido",
        "visitante_nombre": p.equipo_visitante.club.nombre if p.equipo_visitante and p.equipo_visitante.club else "Desconocido"
    })

# ====================================================
# PARTIDOS DEL CRUCE
# ====================================================
@views.route('/get_partidos_cruce_inferiores', methods=['POST'])
def get_partidos_cruce_inferiores():
    data = request.get_json()
    jornada = data.get("jornada")
    local_club_id = data.get("local")
    visitante_club_id = data.get("visitante")
    categorias = ["quinta", "sexta", "septima"]

    try:
        partidos = Partido.query.filter(
            Partido.jornada == jornada,
            Partido.equipo_local.has(club_id=local_club_id),
            Partido.equipo_visitante.has(club_id=visitante_club_id),
            db.func.lower(Partido.categoria).in_(categorias)
        ).all()

        respuesta = {}

        for p in partidos:
            categoria = p.categoria.lower()

            jugadores_local = [
                {"id": je.jugador.numero_carnet,
                 "nombre": f"{je.jugador.nombre} {je.jugador.apellido}"}
                for je in JugadorEquipo.query.filter_by(equipo_id=p.equipo_local_id).all()
            ]

            jugadores_visitante = [
                {"id": je.jugador.numero_carnet,
                 "nombre": f"{je.jugador.nombre} {je.jugador.apellido}"}
                for je in JugadorEquipo.query.filter_by(equipo_id=p.equipo_visitante_id).all()
            ]

            respuesta[categoria.capitalize()] = {
                "partido_id": p.id,
                "id_equipo_local": p.equipo_local_id,
                "id_equipo_visitante": p.equipo_visitante_id,
                "equipo_local": p.equipo_local.club.nombre if p.equipo_local and p.equipo_local.club else "Desconocido",
                "equipo_visitante": p.equipo_visitante.club.nombre if p.equipo_visitante and p.equipo_visitante.club else "Desconocido",
                "jugadores_local": jugadores_local,
                "jugadores_visitante": jugadores_visitante,
                "goles_local": p.goles_local,
                "goles_visitante": p.goles_visitante
            }

        return jsonify(respuesta)

    except Exception as e:
        db.session.rollback()
        print("❌ ERROR get_partidos_cruce_inferiores:", e)
        return jsonify({"success": False, "message": "Error interno"}), 500

# ====================================================
# CRUCES PENDIENTES
# ====================================================
@views.route("/api/cruces_pendientes/<int:jornada>")
def cruces_pendientes(jornada):
    torneo_nombre = request.args.get("torneo", "Apertura")
    categorias = ["quinta", "sexta", "septima"]

    partidos = (
        Partido.query
        .join(Torneo)
        .filter(
            Partido.jornada == jornada,
            Partido.jugado == False,
            Torneo.nombre == torneo_nombre,
            db.func.lower(Partido.categoria).in_(categorias)
        )
        .all()
    )

    cruces = {}
    for p in partidos:
        key = tuple(sorted([
            p.equipo_local.club.nombre if p.equipo_local and p.equipo_local.club else "Desconocido",
            p.equipo_visitante.club.nombre if p.equipo_visitante and p.equipo_visitante.club else "Desconocido"
        ]))

        if key not in cruces:
            cruces[key] = {
                "id": p.id,
                "texto": f"{key[0]} vs {key[1]}"
            }

    return jsonify(list(cruces.values()))

#-----------------------------------------
# CARGAR PARTIDOS PLAYOFF
#-----------------------------------------
@views.route("/api/playoff/jornadas_disponibles", methods=["GET"])
def jornadas_disponibles():
    torneo_id = request.args.get("torneo_id", type=int)
    fase_id = request.args.get("fase_id", type=int)
    categoria = request.args.get("categoria", type=str)

    if not torneo_id or not fase_id or not categoria:
        return jsonify({"success": False, "message": "Faltan parámetros"}), 400

    # Obtener jornadas ya cargadas
    partidos = Partido.query.filter_by(
        torneo_id=torneo_id,
        fase_id=fase_id,
        categoria=categoria.lower()
    ).all()

    jornadas_existentes = [p.jornada for p in partidos]

    opciones = []
    if 1 not in jornadas_existentes:
        opciones.append({"valor": 1, "label": "Ida"})
    if 2 not in jornadas_existentes:
        opciones.append({"valor": 2, "label": "Vuelta"})

    return jsonify({"success": True, "opciones": opciones})


@views.route("/api/playoff/crear_partido", methods=["POST"])
def crear_partido_playoff():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="JSON inválido"), 400

        # ============== CAMPOS OBLIGATORIOS ==============
        required = ["torneo_id","fase_id","categoria","club_local_id","club_visitante_id"]
        for campo in required:
            if not data.get(campo):
                return jsonify(success=False, message=f"Falta el campo obligatorio: {campo}"), 400

        # ============== NORMALIZAR CATEGORÍA ==============
        categoria = data["categoria"].lower().strip()
        if categoria not in ("primera", "reserva"):
            return jsonify(success=False, message="Categoría inválida"), 400

        if data["club_local_id"] == data["club_visitante_id"]:
            return jsonify(success=False, message="El club local y visitante no pueden ser el mismo"), 400

        # ============== TORNEO Y FASE ==============
        torneo = Torneo.query.get(data["torneo_id"])
        if not torneo:
            return jsonify(success=False, message="Torneo inexistente"), 404

        fase = Fase.query.get(data["fase_id"])
        if not fase or fase.torneo_id != torneo.id:
            return jsonify(success=False, message="Fase inexistente para este torneo"), 404

        # ============== JORNADA ==============
        jornada = int(data.get("jornada", 1))
        if fase.ida_vuelta and jornada not in (1,2):
            return jsonify(success=False, message="La fase ida/vuelta solo permite jornada 1 o 2"), 400
        if not fase.ida_vuelta:
            jornada = 1

        # ============== CLUBES ==============
        club_local = Club.query.get(data["club_local_id"])
        club_visitante = Club.query.get(data["club_visitante_id"])
        if not club_local or not club_visitante:
            return jsonify(success=False, message="Club inexistente"), 404

        equipo_local = Equipo.query.filter_by(club_id=club_local.id, categoria=categoria).first()
        equipo_visitante = Equipo.query.filter_by(club_id=club_visitante.id, categoria=categoria).first()
        if not equipo_local or not equipo_visitante:
            return jsonify(success=False, message="Alguno de los clubes no tiene equipo cargado para esa categoría"), 400

        # ============== VALIDAR SECUENCIA DE FASES ==============
        fases_ordenadas = ["Cuartos de Final", "Semifinal", "Final", "Finalísima"]
        idx = fases_ordenadas.index(fase.nombre)
        if idx > 0:
            # Validar que haya partidos cargados en la fase anterior para la misma categoría
            fase_anterior = Fase.query.filter_by(nombre=fases_ordenadas[idx-1], torneo_id=torneo.id).first()
            if not fase_anterior:
                return jsonify(success=False, message=f"No existe la fase anterior: {fases_ordenadas[idx-1]}"), 400
            partidos_ant = Partido.query.filter_by(fase_id=fase_anterior.id, categoria=categoria).all()
            if len(partidos_ant) == 0:
                return jsonify(success=False, message=f"No se pueden cargar partidos de {fase.nombre} antes de completar {fases_ordenadas[idx-1]}"), 400

        # ============== DUPLICADOS ==============
        existe = Partido.query.filter_by(
            torneo_id=torneo.id,
            fase_id=fase.id,
            categoria=categoria,
            equipo_local_id=equipo_local.id,
            equipo_visitante_id=equipo_visitante.id,
            jornada=jornada
        ).first()
        if existe:
            return jsonify(success=False, message="Este partido ya existe en esta fase"), 409

        # ============== FECHA Y HORA ==============
        fecha = None
        hora = None
        if data.get("fecha_partido"):
            try:
                fecha = datetime.strptime(data["fecha_partido"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify(success=False, message="Formato de fecha inválido (YYYY-MM-DD)"), 400
        if data.get("hora_partido"):
            try:
                hora = datetime.strptime(data["hora_partido"], "%H:%M").time()
            except ValueError:
                return jsonify(success=False, message="Formato de hora inválido (HH:MM)"), 400

        # ============== CREAR PARTIDO(S) ==============
        partidos_creados = []

        if fase.ida_vuelta:
            # Crear ida
            partido_ida = Partido(
                torneo_id=torneo.id,
                fase_id=fase.id,
                categoria=categoria,
                jornada=1,
                equipo_local_id=equipo_local.id,
                equipo_visitante_id=equipo_visitante.id,
                fecha_partido=fecha,
                hora_partido=hora,
                goles_local=0,
                goles_visitante=0,
                jugado=False
            )
            db.session.add(partido_ida)
            partidos_creados.append(partido_ida)

            # Crear vuelta (local y visitante invertidos)
            partido_vuelta = Partido(
                torneo_id=torneo.id,
                fase_id=fase.id,
                categoria=categoria,
                jornada=2,
                equipo_local_id=equipo_visitante.id,
                equipo_visitante_id=equipo_local.id,
                fecha_partido=fecha,
                hora_partido=hora,
                goles_local=0,
                goles_visitante=0,
                jugado=False
            )
            db.session.add(partido_vuelta)
            partidos_creados.append(partido_vuelta)
        else:
            # Partido único
            partido = Partido(
                torneo_id=torneo.id,
                fase_id=fase.id,
                categoria=categoria,
                jornada=1,
                equipo_local_id=equipo_local.id,
                equipo_visitante_id=equipo_visitante.id,
                fecha_partido=fecha,
                hora_partido=hora,
                goles_local=0,
                goles_visitante=0,
                jugado=False
            )
            db.session.add(partido)
            partidos_creados.append(partido)

        db.session.commit()

        return jsonify(success=True, message="Partido(s) creado(s) correctamente", ids=[p.id for p in partidos_creados])
    
    except Exception as e:
        print("ERROR crear_partido_playoff:", e)
        return jsonify(success=False, message="Error interno del servidor"), 500

# ===========================================
# VISTA HTML: CARGA DE PARTIDOS PLAYOFF
# ===========================================
@views.route("/crear_partido_playoff", methods=["GET"])
def vista_crear_partido_playoff():

    torneos = Torneo.query.order_by(Torneo.id.desc()).all()

    clubes = Club.query.order_by(Club.nombre).all()
    categorias = ["Primera","Reserva"]

    fases = []
    fases_ordenadas = ["Cuartos de Final","Semifinal","Final","Finalísima"]

    # Mostrar fases solo si se cumplen las secuencias
    for nombre_fase in fases_ordenadas:
        fase_obj = Fase.query.filter_by(nombre=nombre_fase).first()
        if not fase_obj:
            continue

        # Validar secuencia (excepto cuartos)
        if nombre_fase != "Cuartos de Final":
            idx = fases_ordenadas.index(nombre_fase)
            fase_anterior = Fase.query.filter_by(nombre=fases_ordenadas[idx-1]).first()
            if not fase_anterior:
                continue
            # Chequear que haya partidos de la fase anterior
            if not Partido.query.filter_by(fase_id=fase_anterior.id).first():
                continue

        fases.append(fase_obj)

    return render_template(
        "plantillasAdmin/cargar_partidos_playoff.html",
        torneos=torneos,
        fases=fases,
        clubes=clubes,
        categorias=categorias
    )

@views.route("/playoff/partidos", methods=["GET"])
def vista_partidos_playoff():
    torneos = Torneo.query.order_by(Torneo.id.desc()).all()
    fases = Fase.query.filter(Fase.nombre.in_([
        "Cuartos de Final", "Semifinal", "Final", "Finalísima"
    ])).order_by(Fase.orden).all()

    # Traer todos los partidos de playoff
    partidos = (
        Partido.query
        .join(Fase)
        .join(Torneo, Partido.torneo_id == Torneo.id)
        .filter(Fase.nombre.in_([
            "Cuartos de Final", "Semifinal", "Final", "Finalísima"
        ]))
        .order_by(Torneo.id.desc(), Fase.orden, Partido.jornada)
        .all()
    )

    return render_template(
        "plantillasAdmin/ver_partidos_playoff.html",
        torneos=torneos,
        fases=fases,
        partidos=partidos
    )

# VIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDEOVIDE

@views.route('/cargar_video', methods=['GET', 'POST'])
@login_required
def cargar_video():
    if current_user.rol not in ["administrador", "periodista"]:
        flash("Acceso denegado.", "danger")
        return redirect(url_for("views.index"))

    if request.method == "POST":
        titulo = request.form.get("titulo_video")
        url_video = request.form.get("url")
        descripcion = request.form.get("descripcion")

        jornada_jugada = request.form.get("jornada_jugada")

        # 👉 Si viene vacío, lo convertimos en None
        if not jornada_jugada:
            jornada_jugada = None
        else:
            jornada_jugada = int(jornada_jugada)

        video = Video(
            titulo_video=titulo,
            url=url_video,
            descripcion=descripcion,
            jornada_jugada=jornada_jugada,
            id_autor=current_user.id_usuario
        )

        db.session.add(video)
        db.session.commit()

        flash("🎥 Video cargado correctamente.", "success")
        return redirect(url_for("views.cargar_video"))

    return render_template("plantillasAdmin/cargar_video.html", usuario=current_user)


import datetime
from werkzeug.utils import secure_filename
import os
from slugify import slugify


#-----------------------------------------
# NOTICIAS - CARGAR NOTICIAS CON IMAGENES
#-----------------------------------------

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route('/cargar_noticia', methods=['GET', 'POST'])
@login_required
def cargar_noticia():

    if current_user.rol not in ["administrador", "periodista"]:
        flash("Acceso denegado.", "danger")
        return redirect(url_for("views.index"))

    if request.method == "POST":
        titulo = request.form.get("titulo")
        contenido = request.form.get("contenido")
        categoria = request.form.get("categoria")

        file = request.files.get("imagen")
        imagen_url = None

        if file and file.filename != "" and allowed_file(file.filename):

            upload_folder = os.path.join(
                current_app.root_path,
                "static",
                "uploads",
                "noticias"
            )

            os.makedirs(upload_folder, exist_ok=True)

            filename = secure_filename(file.filename)
            new_filename = f"{int(datetime.datetime.utcnow().timestamp())}_{filename}"

            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)

            # 👉 GUARDAMOS URL PÚBLICA (CORRECTO)
            imagen_url = f"/static/uploads/noticias/{new_filename}"

        slug = slugify(titulo)

        noticia = Noticia(
            titulo=titulo,
            contenido=contenido,
            categoria=categoria,
            imagen_url=imagen_url,
            id_autor=current_user.id_usuario,
            slug=slug
        )

        db.session.add(noticia)
        db.session.commit()

        flash("📰 Noticia cargada correctamente.", "success")
        return redirect(url_for("views.cargar_noticia"))

    return render_template(
        "plantillasAdmin/cargar_noticia.html",
        usuario=current_user
    )
@views.route('/noticia/<int:noticia_id>')
def noticia_detalle(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    return render_template('noticia_detalle.html', noticia=noticia)

@views.route('/cargar_resultados_admin')
@login_required
def cargar_resultados_admin():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))
    return render_template('plantillasAdmin/cargar_resultados.html', usuario=current_user)