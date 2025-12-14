from flask import Blueprint, current_app,render_template, jsonify, json,request, redirect, url_for, flash, abort
from ..models.models import (
    Equipo, Partido, Jugador, Club, Video, Noticia, Usuario, JugadorEquipo,
    TablaPosiciones, EstadoJugadorPartido
)
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
#import jsonify
from ..database.db import db
from sqlalchemy import func, or_, and_
import datetime
from datetime import datetime
from seeds.puntajes import cargar_puntajes_por_categoria
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
    # Subconsulta que obtiene el ID mínimo por cruce único
        sub = (
            db.session.query(func.min(Partido.id).label("pid"))
            .join(Equipo, Equipo.id == Partido.equipo_local_id)
            .join(Club, Club.id == Equipo.club_id)
            .filter(Partido.categoria.in_(categorias_bloque))
            .group_by(
                Partido.jornada,
                Partido.equipo_local_id,
                Partido.equipo_visitante_id
            )
        ).subquery()

        # Traer solo los partidos únicos
        partidos = (
            Partido.query
            .filter(Partido.id.in_(sub))
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
@views.route('/tabla_posiciones/<categoria>')
def tabla_posiciones(categoria):

    categoria = categoria.capitalize()
    categorias_validas = ['Primera', 'Reserva', 'Quinta', 'Sexta', 'Septima']

    if categoria not in categorias_validas:
        flash("La categoría solicitada no existe.", "danger")
        return redirect(url_for('views.index'))

    # === 1) Obtener la tabla ordenada como corresponde ===
    tabla = (
        TablaPosiciones.query
        .filter(TablaPosiciones.categoria == categoria)
        .order_by(
            TablaPosiciones.cantidad_puntos.desc(),
            TablaPosiciones.diferencia_gol.desc(),
            TablaPosiciones.goles_a_favor.desc(),
            TablaPosiciones.nombre_equipo.asc()
        )
        .all()
    )

    if not tabla:
        flash(f"No hay datos cargados para {categoria}.", "warning")
        return render_template(
            'tabla_posiciones.html',
            tabla=[],
            categoria=categoria
        )

    # =====================================================
    #               2) ESTADÍSTICAS GENERALES
    # =====================================================

    stats = {
        "mas_goleador": max(tabla, key=lambda e: e.goles_a_favor),
        "menos_goleado": min(tabla, key=lambda e: e.goles_en_contra),
        "mejor_diferencia": max(tabla, key=lambda e: e.diferencia_gol),
    }

    # =====================================================
    #              3) RACHAS / TENDENCIAS
    # =====================================================

    rachas = {}

    for equipo in tabla:
        equipo_db = Equipo.query.filter_by(categoria=categoria)\
                                .join(Club).filter(Club.nombre == equipo.nombre_equipo)\
                                .first()

        if not equipo_db:
            rachas[equipo.nombre_equipo] = []
            continue

        # Últimos 5 partidos del equipo
        partidos = (
            Partido.query
            .filter(
                Partido.categoria == categoria,
                ((Partido.equipo_local_id == equipo_db.id) |
                 (Partido.equipo_visitante_id == equipo_db.id)),
                Partido.jugado == True
            )
            .order_by(Partido.fecha_partido.desc())
            .limit(5)
            .all()
        )

        tendencia = []
        for p in partidos:
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

        rachas[equipo.nombre_equipo] = tendencia

    # =====================================================
    #               4) CRUCES TEÓRICOS
    # =====================================================

    cruces = []
    if len(tabla) >= 8:
        cruces = [
            (tabla[0], tabla[7]),
            (tabla[1], tabla[6]),
            (tabla[2], tabla[5]),
            (tabla[3], tabla[4])
        ]

    # =====================================================
    #               RENDER FINAL
    # =====================================================

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
    from app.utils.email_utils import enviar_mail_bienvenida

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
@views.route('/cargar_fixture_mayores', methods=['GET'])
def cargar_fixture_mayores_view():
    equipos = (
        Equipo.query
        .filter(Equipo.categoria.in_(["Primera", "Reserva"]))
        .order_by(Equipo.club_id)
        .all()
    )
    clubes = Club.query.all()

    total_equipos = Equipo.query.filter_by(categoria="Primera").count()
    total_jornadas = total_equipos - 1  

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
from sqlalchemy import or_, and_

# POST: corregido para convertir '' -> None y validar fechas
@views.route('/cargar_fixture_mayores', methods=['POST'])
def cargar_fixture_mayores():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        jornada = int(request.form.get("jornada"))
    except (TypeError, ValueError):
        if is_ajax:
            return jsonify({"ok": False, "msg": "Jornada inválida."}), 400
        flash("Jornada inválida.", "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    club_local_id = int(request.form.get("club_local"))
    club_visitante_id = int(request.form.get("club_visitante"))

    fecha_raw = request.form.get("fecha")
    hora_raw = request.form.get("hora")

    fecha = fecha_raw.strip() if fecha_raw and fecha_raw.strip() else None
    hora = hora_raw.strip() if hora_raw and hora_raw.strip() else None

    if fecha:
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            if is_ajax:
                return jsonify({"ok": False, "msg": "Formato de fecha inválido."}), 400
            flash("Formato de fecha inválido.", "error")
            return redirect(url_for("views.cargar_fixture_mayores_view"))

    if hora:
        try:
            hora = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            if is_ajax:
                return jsonify({"ok": False, "msg": "Formato de hora inválido."}), 400
            flash("Formato de hora inválido.", "error")
            return redirect(url_for("views.cargar_fixture_mayores_view"))

    if club_local_id == club_visitante_id:
        msg = "Un club no puede enfrentarse a sí mismo."
        if is_ajax:
            return jsonify({"ok": False, "msg": msg}), 400
        flash(msg, "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    local_primera = Equipo.query.filter_by(club_id=club_local_id, categoria="Primera").first()
    local_reserva = Equipo.query.filter_by(club_id=club_local_id, categoria="Reserva").first()
    visita_primera = Equipo.query.filter_by(club_id=club_visitante_id, categoria="Primera").first()
    visita_reserva = Equipo.query.filter_by(club_id=club_visitante_id, categoria="Reserva").first()

    if not (local_primera and local_reserva and visita_primera and visita_reserva):
        msg = "Error: faltan equipos de Primera o Reserva para uno de los clubes."
        if is_ajax:
            return jsonify({"ok": False, "msg": msg}), 400
        flash(msg, "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    enfrentado = Partido.query.filter(
        ((Partido.equipo_local_id.in_([local_primera.id, local_reserva.id])) &
         (Partido.equipo_visitante_id.in_([visita_primera.id, visita_reserva.id]))) |
        ((Partido.equipo_local_id.in_([visita_primera.id, visita_reserva.id])) &
         (Partido.equipo_visitante_id.in_([local_primera.id, local_reserva.id])))
    ).first()

    if enfrentado:
        msg = "Estos clubes ya se enfrentaron en otra jornada."
        if is_ajax:
            return jsonify({"ok": False, "msg": msg}), 400
        flash(msg, "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    conflicto = Partido.query.filter(
        (Partido.jornada == jornada) & (
            Partido.equipo_local_id.in_([local_primera.id, local_reserva.id, visita_primera.id, visita_reserva.id]) |
            Partido.equipo_visitante_id.in_([local_primera.id, local_reserva.id, visita_primera.id, visita_reserva.id])
        )
    ).first()

    if conflicto:
        msg = "Uno de los equipos ya tiene partido en esta jornada."
        if is_ajax:
            return jsonify({"ok": False, "msg": msg}), 400
        flash(msg, "error")
        return redirect(url_for("views.cargar_fixture_mayores_view"))

    p1 = Partido(
        fecha_partido=fecha,
        hora_partido=hora,
        jornada=jornada,
        categoria="Primera",
        equipo_local_id=local_primera.id,
        equipo_visitante_id=visita_primera.id,
        jugado=False
    )

    p2 = Partido(
        fecha_partido=fecha,
        hora_partido=hora,
        jornada=jornada,
        categoria="Reserva",
        equipo_local_id=local_reserva.id,
        equipo_visitante_id=visita_reserva.id,
        jugado=False
    )

    db.session.add_all([p1, p2])
    db.session.commit()

    # --------------------------
    # SI ES AJAX → DEVOLVER JSON
    # --------------------------
    if is_ajax:
        return jsonify({"ok": True, "msg": "Partidos cargados correctamente."})

    flash("Partidos cargados correctamente.", "success")
    return redirect(url_for("views.cargar_fixture_mayores_view"))


@views.route('/fixture/ocupados/<int:jornada>', methods=['GET'])
def fixture_ocupados(jornada):
    partidos = Partido.query.filter_by(jornada=jornada).filter(
        Partido.categoria.in_(["Primera", "Reserva"])
    ).all()

    ocupados_club_ids = set()
    cruces = {}

    for p in partidos:
        eq_local = Equipo.query.get(p.equipo_local_id)
        eq_visita = Equipo.query.get(p.equipo_visitante_id)

        if not eq_local or not eq_visita or not eq_local.club or not eq_visita.club:
            continue

        local_id = eq_local.club.id
        visita_id = eq_visita.club.id

        ocupados_club_ids.add(local_id)
        ocupados_club_ids.add(visita_id)

        clave = (local_id, visita_id)

        if clave not in cruces:
            cruces[clave] = {
                "local_club_id": local_id,
                "local_club_nombre": eq_local.club.nombre,
                "visitante_club_id": visita_id,
                "visitante_club_nombre": eq_visita.club.nombre,
                "fecha": p.fecha_partido.isoformat() if p.fecha_partido else None,
                "hora": p.hora_partido.strftime("%H:%M") if p.hora_partido else None,
                "categorias": set(),
                "jugado": False
            }

        cruces[clave]["categorias"].add(p.categoria)
        if p.jugado:
            cruces[clave]["jugado"] = True

    resultados = []
    for c in cruces.values():
        c["categorias"] = list(c["categorias"])
        c["local"] = c["local_club_nombre"]
        c["visitante"] = c["visitante_club_nombre"]
        resultados.append(c)

    return jsonify({
        "ocupados": list(ocupados_club_ids),
        "partidos": resultados
    })


@views.route('/fixture/equipos_disponibles/<int:jornada>', methods=['GET'])
def equipos_disponibles(jornada):
    partidos = Partido.query.filter_by(jornada=jornada).all()

    equipos_ocupados = {p.equipo_local_id for p in partidos} | \
                       {p.equipo_visitante_id for p in partidos}

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

        if local_id == visitante_id:
            flash("El club local y visitante no pueden ser el mismo.", "danger")
            return redirect(url_for('views.cargar_fixture_inferiores'))

        equipos_local = Equipo.query.filter_by(club_id=local_id).all()
        equipos_visit = Equipo.query.filter_by(club_id=visitante_id).all()

        categorias_local = {e.categoria for e in equipos_local}
        categorias_visit = {e.categoria for e in equipos_visit}

        categorias_comunes = categorias_local.intersection(categorias_visit)
        categorias_inferiores_comunes = categorias_comunes.intersection(CATEGORIAS_INFERIORES)

        if not categorias_inferiores_comunes:
            flash("Los clubes no comparten categorías de inferiores.", "danger")
            return redirect(url_for('views.cargar_fixture_inferiores'))

        for categoria in categorias_inferiores_comunes:
            eq_local = next(e for e in equipos_local if e.categoria == categoria)
            eq_visit = next(e for e in equipos_visit if e.categoria == categoria)

            partido_exist = Partido.query.filter(
                ((Partido.equipo_local_id == eq_local.id) &
                 (Partido.equipo_visitante_id == eq_visit.id)) |
                ((Partido.equipo_local_id == eq_visit.id) &
                 (Partido.equipo_visitante_id == eq_local.id))
            ).first()

            if partido_exist:
                flash(f"Ya existen partidos entre {eq_local.club.nombre} y {eq_visit.club.nombre}.", "danger")
                return redirect(url_for('views.cargar_fixture_inferiores'))

        for categoria in categorias_inferiores_comunes:
            eq_local = next(e for e in equipos_local if e.categoria == categoria)
            eq_visit = next(e for e in equipos_visit if e.categoria == categoria)

            conflicto = Partido.query.filter(
                (Partido.jornada == jornada) &
                (
                    (Partido.equipo_local_id == eq_local.id) |
                    (Partido.equipo_local_id == eq_visit.id) |
                    (Partido.equipo_visitante_id == eq_local.id) |
                    (Partido.equipo_visitante_id == eq_visit.id)
                )
            ).first()

            if conflicto:
                flash(f"Uno de los equipos ya tiene un partido en la jornada {jornada}.", "danger")
                return redirect(url_for('views.cargar_fixture_inferiores'))

        partidos_generados = 0
        for categoria in categorias_inferiores_comunes:
            eq_local = next(e for e in equipos_local if e.categoria == categoria)
            eq_visit = next(e for e in equipos_visit if e.categoria == categoria)

            partido = Partido(
                jornada=jornada,
                fecha_partido=fecha,
                hora_partido=hora,
                categoria=categoria,
                equipo_local_id=eq_local.id,
                equipo_visitante_id=eq_visit.id
            )

            db.session.add(partido)
            partidos_generados += 1

        db.session.commit()

        flash(f"Se generaron {partidos_generados} partidos para inferiores.", "success")
        return redirect(url_for('views.cargar_fixture_inferiores'))

    return render_template(
        'plantillasAdmin/cargar_fixture_inferiores.html',
        clubes=clubes,
        total_jornadas=total_jornadas
    )

@views.route('/guardar_partido_inferiores', methods=['POST'])
@login_required
def guardar_partido_inferiores():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se enviaron datos JSON"}), 400

    try:
        jornada = int(data.get("jornada"))
        fecha = data.get("fecha") or None
        hora = data.get("hora") or None

        local_id = int(data.get("local_id"))
        visitante_id = int(data.get("visitante_id"))

        CATEGORIAS_INFERIORES = {"Quinta", "Sexta", "Septima"}

        if local_id == visitante_id:
            return jsonify({"error": "El club local y visitante no pueden ser el mismo."}), 400

        equipos_local = Equipo.query.filter_by(club_id=local_id).all()
        equipos_visit = Equipo.query.filter_by(club_id=visitante_id).all()

        categorias_local = {e.categoria for e in equipos_local}
        categorias_visit = {e.categoria for e in equipos_visit}

        categorias_comunes = categorias_local.intersection(categorias_visit)
        categorias_inferiores = categorias_comunes.intersection(CATEGORIAS_INFERIORES)

        if not categorias_inferiores:
            return jsonify({"error": "Los clubes no comparten categorías de inferiores."}), 400

        for categoria in categorias_inferiores:
            eq_local = next(e for e in equipos_local if e.categoria == categoria)
            eq_visit = next(e for e in equipos_visit if e.categoria == categoria)

            existe = Partido.query.filter(
                ((Partido.equipo_local_id == eq_local.id) &
                 (Partido.equipo_visitante_id == eq_visit.id)) |
                ((Partido.equipo_local_id == eq_visit.id) &
                 (Partido.equipo_visitante_id == eq_local.id))
            ).first()

            if existe:
                return jsonify({
                    "error": f"Ya existe un partido entre {eq_local.club.nombre} y {eq_visit.club.nombre} en {categoria}."
                }), 400

        for categoria in categorias_inferiores:
            eq_local = next(e for e in equipos_local if e.categoria == categoria)
            eq_visit = next(e for e in equipos_visit if e.categoria == categoria)

            conflicto = Partido.query.filter(
                (Partido.jornada == jornada) &
                (
                    (Partido.equipo_local_id == eq_local.id) |
                    (Partido.equipo_local_id == eq_visit.id) |
                    (Partido.equipo_visitante_id == eq_local.id) |
                    (Partido.equipo_visitante_id == eq_visit.id)
                )
            ).first()

            if conflicto:
                return jsonify({
                    "error": f"Uno de los equipos ya tiene un partido en la jornada {jornada}."
                }), 400

        generados = []
        for categoria in categorias_inferiores:
            eq_local = next(e for e in equipos_local if e.categoria == categoria)
            eq_visit = next(e for e in equipos_visit if e.categoria == categoria)

            partido = Partido(
                jornada=jornada,
                fecha_partido=fecha,
                hora_partido=hora,
                categoria=categoria,
                equipo_local_id=eq_local.id,
                equipo_visitante_id=eq_visit.id
            )

            db.session.add(partido)
            generados.append({
                "categoria": categoria,
                "local": eq_local.club.nombre,
                "visitante": eq_visit.club.nombre
            })

        db.session.commit()

        return jsonify({
            "success": True,
            "msg": f"Se generaron {len(generados)} partidos.",
            "partidos": generados
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error en servidor: {str(e)}"}), 500

    
@views.route("/fixture_ocupados_inferiores/<int:jornada>")
def fixture_ocupados_inferiores(jornada):

    try:
        categorias_inferiores = ["Quinta", "Sexta", "Septima"]

        partidos = (
            Partido.query
            .filter(
                Partido.jornada == jornada,
                Partido.categoria.in_(categorias_inferiores)
            )
            .order_by(Partido.categoria)
            .all()
        )

        ocupados_club_ids = set()
        cruces = {}

        for p in partidos:

            eq_local = Equipo.query.get(p.equipo_local_id)
            eq_visita = Equipo.query.get(p.equipo_visitante_id)

            # Evitar errores por datos corruptos o relaciones incompletas
            if not eq_local or not eq_visita or not eq_local.club or not eq_visita.club:
                print(f"⚠ Partido {p.id} omitido por datos faltantes")
                continue

            local_club = eq_local.club
            visitante_club = eq_visita.club

            local_id = local_club.id
            visita_id = visitante_club.id

            # Registrar clubes ocupados
            ocupados_club_ids.add(local_id)
            ocupados_club_ids.add(visita_id)

            # Clave única del cruce
            clave = (local_id, visita_id)

            # Crear el cruce si no existe aún
            if clave not in cruces:
                cruces[clave] = {
                    "local_club_id": local_id,
                    "local_club_nombre": eq_local.club.nombre,
                    "visitante_club_id": visita_id,
                    "visitante_club_nombre": eq_visita.club.nombre,
                    "fecha": p.fecha_partido.isoformat() if p.fecha_partido else None,
                    "hora": p.hora_partido.strftime("%H:%M") if p.hora_partido else None,
                    "categorias": set(),
                    "jugado": False
                }

            # Agregar categoría presente en este cruce
            cruces[clave]["categorias"].add(p.categoria)

            # Si algún partido del cruce está jugado → marcar cruce como jugado
            if p.jugado:
                cruces[clave]["jugado"] = True

        # Convertir sets a listas antes de enviar JSON
        lista_partidos = []
        for c in cruces.values():
            c["categorias"] = list(c["categorias"])
            lista_partidos.append(c)

        return jsonify({
            "ok": True,
            "ocupados": list(ocupados_club_ids),
            "partidos": lista_partidos
        })

    except Exception as e:
        print("❌ ERROR EN fixture_ocupados_inferiores:", e)

        # Nunca romper al frontend
        return jsonify({
            "ok": False,
            "ocupados": [],
            "partidos": [],
            "msg": "Error interno del servidor"
        }), 500
    
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
    """Ruta opcional que devuelve todos los cruces (sin filtrar por jugado).
    La dejamos por compatibilidad si la necesitás en algún flujo.
    """
    try:
        partidos = Partido.query.filter(
            Partido.jornada == jornada,
            Partido.categoria.in_(["Primera", "Reserva"])
        ).all()

        cruces = {}

        for p in partidos:
            # defensivo: verificar relaciones
            if not p.equipo_local or not p.equipo_visitante or not p.equipo_local.club or not p.equipo_visitante.club:
                continue

            key = f"{p.equipo_local.club.nombre} vs {p.equipo_visitante.club.nombre}"

            if key not in cruces:
                cruces[key] = {
                    "local": p.equipo_local.club.nombre,
                    "visitante": p.equipo_visitante.club.nombre,
                    "id_reserva": None,
                    "id_primera": None
                }

            if p.categoria and p.categoria.lower() == "reserva":
                cruces[key]["id_reserva"] = p.id
            elif p.categoria and p.categoria.lower() == "primera":
                cruces[key]["id_primera"] = p.id

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
    except Exception as e:
        print("❌ ERROR cruces_por_jornada:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------------------
# 2) Obtener cruces de la jornada (info de un cruce)
# -----------------------------------------
@views.route("/api/info_cruce/<int:cruce_id>")
def info_cruce(cruce_id):
    try:
        partido_base = Partido.query.get(cruce_id)
        if not partido_base:
            return jsonify({"error": "Cruce no encontrado"}), 404

        jornada = partido_base.jornada

        # Identificar clubes
        local_club_id = partido_base.equipo_local.club_id
        visitante_club_id = partido_base.equipo_visitante.club_id

        # Buscar todos los equipos de ambos clubes
        equipos_local = Equipo.query.filter_by(club_id=local_club_id).all()
        equipos_visitante = Equipo.query.filter_by(club_id=visitante_club_id).all()

        ids_equipos_local = [e.id for e in equipos_local]
        ids_equipos_visitante = [e.id for e in equipos_visitante]

        # Buscar partidos Primera/Reserva entre esos equipos en la misma jornada
        partidos = Partido.query.filter(
            Partido.jornada == jornada,
            Partido.equipo_local_id.in_(ids_equipos_local),
            Partido.equipo_visitante_id.in_(ids_equipos_visitante),
            Partido.categoria.in_(["Primera", "Reserva"])
        ).all()

        partido_primera = next((p for p in partidos if p.categoria and p.categoria.lower() == "primera"), None)
        partido_reserva = next((p for p in partidos if p.categoria and p.categoria.lower() == "reserva"), None)

        return jsonify({
            "id_primera": partido_primera.id if partido_primera else None,
            "id_reserva": partido_reserva.id if partido_reserva else None,
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
# 3) Obtener datos del cruce (partidos + jugadores)
# -----------------------------------------
@views.route("/get_partidos_cruce", methods=["POST"])
def get_partidos_cruce():
    data = request.get_json() or {}
    rep_id = data.get("representative_id")

    if not rep_id:
        return jsonify({"error":"Falta representative_id"}), 400

    ref = Partido.query.get(rep_id)
    if not ref:
        return jsonify({"error":"Cruce no encontrado"}), 404

    partidos = Partido.query.filter(
        Partido.jornada == ref.jornada,
        Partido.equipo_local.has(club_id=ref.equipo_local.club_id),
        Partido.equipo_visitante.has(club_id=ref.equipo_visitante.club_id),
        Partido.categoria.in_(["Primera","Reserva"])
    ).all()

    resp = {}
    for p in partidos:
        resp[p.categoria.lower()] = {
            "id": p.id,
            "id_equipo_local": p.equipo_local_id,
            "id_equipo_visitante": p.equipo_visitante_id
        }

    return jsonify(resp)
# -----------------------------------------
# Cruces pendientes (MAYORES) -> devuelve solo cruces con al menos una categoría no jugada
# -----------------------------------------
@views.route("/api/cruces_pendientes_mayores/<int:jornada>")
def cruces_pendientes_mayores(jornada):
    categorias = ["Primera","Reserva"]
    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.categoria.in_(categorias)
    ).all()

    cruces = {}

    for p in partidos:
        local = p.equipo_local.club.nombre
        visitante = p.equipo_visitante.club.nombre
        key = f"{local} vs {visitante}"

        if key not in cruces:
            cruces[key] = {
                "texto": key,
                "id": p.id,
                "primera": None,
                "reserva": None
            }

        cruces[key][p.categoria.lower()] = p.jugado

    respuesta = []
    for c in cruces.values():
        pendiente = any(v is False for v in [c["primera"], c["reserva"]] if v is not None)
        if pendiente:
            respuesta.append({ "id": c["id"], "texto": c["texto"] })

    return jsonify(respuesta)


"""@views.route("/api/jugadores_por_equipo/<int:equipo_id>")
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
        return jsonify({"error": str(e)}), 500"""

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

    # 2. Validar categoría (coincidir insensitivo)
    if not partido.categoria or partido.categoria.lower() != categoria.lower():
        return {"success": False, "message": f"Este endpoint solo guarda datos de {categoria.capitalize()}."}, 400

    # 3. Validar si ya fue jugado
    if partido.jugado:
        return {"success": False, "message": f"El partido de {categoria.capitalize()} ya fue cargado."}, 400

    # 4. Verificar suma de goles
    total_local = sum(int(g.get("goles", 0)) for g in goleadores_local)
    total_visitante = sum(int(g.get("goles", 0)) for g in goleadores_visitante)

    if total_local != goles_local or total_visitante != goles_visitante:
        return {"success": False, "message": "Los goles no coinciden con los goleadores."}, 400

    # 5. Marcar partido, asignar goles
    partido.goles_local = goles_local
    partido.goles_visitante = goles_visitante
    partido.jugado = True

    # 6. Unificar estadísticas por jugador
    stats = {}

    def ensure(jid):
        if jid not in stats:
            stats[jid] = {"cant_goles": 0, "tarjetas_amarillas": 0, "tarjetas_rojas": 0}

    # goleadores (esperamos lista de {jugador_id, goles})
    for item in (goleadores_local + goleadores_visitante):
        jugador_id = item.get("jugador_id") or item.get("id") or item.get("numero_carnet")
        if jugador_id is None:
            continue
        goles = int(item.get("goles", 0))
        ensure(jugador_id)
        stats[jugador_id]["cant_goles"] += goles

    # tarjetas (esperamos listas de ids: [7, 10, ...])
    for j in amarillas_local + amarillas_visitante:
        ensure(j)
        stats[j]["tarjetas_amarillas"] += 1

    for j in rojas_local + rojas_visitante:
        ensure(j)
        stats[j]["tarjetas_rojas"] += 1

    # 7. Insertar/guardar registros
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

        db.session.commit()
        return {"success": True, "message": "Estadísticas guardadas correctamente"}, 200

    except IntegrityError as e:
        db.session.rollback()
        # Duplicado de PK -> partido/jugador ya registrado
        msg = str(e.orig) if getattr(e, "orig", None) else str(e)
        if "estado_jugador_partido_pkey" in msg or "duplicate key value" in msg.lower():
            return {"success": False, "message": "Ya existen estadísticas para alguno de estos jugadores en este partido."}, 400
        return {"success": False, "message": "Error de integridad en la base de datos"}, 500

    except Exception as e:
        db.session.rollback()
        print("❌ ERROR guardar estadisticas:", e)
        return {"success": False, "message": "Error interno del servidor"}, 500


@views.route("/api/guardar_primera", methods=["POST"])
@views.route("/api/guardar_reserva", methods=["POST"])
def guardar_categoria():
    data = request.get_json() or {}
    partido_id = data.get("partido_id")

    partido = Partido.query.get(partido_id)
    if not partido:
        return jsonify(success=False, message="Partido no encontrado"), 404

    partido.jugado = True
    db.session.commit()

    return jsonify(success=True)

# ---------------------------
#   INFERIORES
# ---------------------------
@views.route('/cargar_estadisticas_inferiores')
def cargar_estadisticas_inferiores():
    jornadas = db.session.query(Partido.jornada).distinct().order_by(Partido.jornada).all()
    jornadas = [j[0] for j in jornadas]
    return render_template('plantillasAdmin/cargar_estadisticas_inferiores.html', jornadas=jornadas)


@views.route("/api/cruces_por_jornada_inferiores/<int:jornada>")
def cruces_por_jornada_inferiores(jornada):

    categorias = ["Quinta", "Sexta", "Septima"]

    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.categoria.in_(categorias)
    ).all()

    cruces = {}

    for p in partidos:
        local = p.equipo_local.club.nombre
        visitante = p.equipo_visitante.club.nombre

        key = f"{local} vs {visitante}"

        if key not in cruces:
            cruces[key] = {
                "local": local,
                "visitante": visitante,
                "id_quinta": None,
                "id_sexta": None,
                "id_septima": None
            }

        if p.categoria == "Quinta":
            cruces[key]["id_quinta"] = p.id
        elif p.categoria == "Sexta":
            cruces[key]["id_sexta"] = p.id
        elif p.categoria == "Septima":
            cruces[key]["id_septima"] = p.id
    print (f"partidos encontrados {cruces}")
    respuesta = []

    for key, c in cruces.items():

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



@views.route("/api/info_cruce_inferiores/<int:id_representativo>")
def info_cruce_inferiores(id_representativo):

    partido_ref = Partido.query.get_or_404(id_representativo)

    data = {
        "jornada": partido_ref.jornada,
        "local_id": partido_ref.equipo_local.club.id,
        "visitante_id": partido_ref.equipo_visitante.club.id,
        "local_nombre": partido_ref.equipo_local.club.nombre,
        "visitante_nombre": partido_ref.equipo_visitante.club.nombre
    }

    return jsonify(data)


@views.route('/get_partidos_cruce_inferiores', methods=['POST'])
def get_partidos_cruce_inferiores():

    data = request.get_json()

    jornada = data.get("jornada")
    local_id = data.get("local")
    visitante_id = data.get("visitante")

    categorias = ["Quinta", "Sexta", "Septima"]

    partidos = Partido.query.filter(
        Partido.jornada == jornada,
        Partido.equipo_local.has(club_id=local_id),
        Partido.equipo_visitante.has(club_id=visitante_id),
        Partido.categoria.in_(categorias)
    ).all()

    respuesta = {}

    for p in partidos:
        jugadores_local = JugadorEquipo.query.filter_by(equipo_id=p.equipo_local_id).all()
        jugadores_visitante = JugadorEquipo.query.filter_by(equipo_id=p.equipo_visitante_id).all()

        respuesta[p.categoria] = {
            "partido_id": p.id,
            "id_equipo_local": p.equipo_local_id,
            "id_equipo_visitante": p.equipo_visitante_id,
            "equipo_local": p.equipo_local.club.nombre,
            "equipo_visitante": p.equipo_visitante.club.nombre,

            "jugadores_local": [
                {"id": je.jugador.numero_carnet, "nombre": f"{je.jugador.nombre} {je.jugador.apellido}"}
                for je in jugadores_local
            ],

            "jugadores_visitante": [
                {"id": je.jugador.numero_carnet, "nombre": f"{je.jugador.nombre} {je.jugador.apellido}"}
                for je in jugadores_visitante
            ],

            "goles_local": p.goles_local,
            "goles_visitante": p.goles_visitante
        }

    return jsonify(respuesta)

@views.route("/api/cruces_pendientes/<int:jornada>")
def cruces_pendientes(jornada):
    try:
        categorias = ["Quinta", "Sexta", "Septima"]

        partidos = Partido.query.filter(
            Partido.jornada == jornada,
            Partido.categoria.in_(categorias)
        ).all()

        cruces = {}

        for p in partidos:
            # Validaciones defensivas
            if not (p.equipo_local and p.equipo_visitante):
                continue
            if not (p.equipo_local.club and p.equipo_visitante.club):
                continue

            local = p.equipo_local.club.nombre
            visitante = p.equipo_visitante.club.nombre
            key = f"{local} vs {visitante}"

            print(
                f"[DEBUG] Jornada {jornada} | cat={p.categoria:<7} | "
                f"local='{local}' | visitante='{visitante}' | jugado={p.jugado}"
            )

            if key not in cruces:
                cruces[key] = {
                    "texto": key,
                    "id_representativo": p.id,  # siempre existe al menos 1
                    "quinta": None,
                    "sexta": None,
                    "septima": None
                }

            # Guardamos si ya se cargó o no el resultado
            if p.categoria == "Quinta":
                cruces[key]["quinta"] = p.jugado
            elif p.categoria == "Sexta":
                cruces[key]["sexta"] = p.jugado
            elif p.categoria == "Septima":
                cruces[key]["septima"] = p.jugado

        respuesta = []

        for c in cruces.values():
            # 🔥 si alguna categoría NO está jugada → cruce pendiente
            pendiente = any(
                (v is not None and v is not True)
                for v in (c["quinta"], c["sexta"], c["septima"])
            )

            if pendiente:
                respuesta.append({
                    "id": c["id_representativo"],
                    "texto": c["texto"]
                })

        return jsonify(respuesta)

    except Exception as e:
        print("❌ ERROR EN cruces_pendientes:", str(e))
        return jsonify({"error": str(e)}), 500


#-----------------------------------------VARIFICAR TARJETAS---------------------------
def validar_tarjetas(data, label=""):
    if not data:
        return

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                jugador_id = item.get("id") or item.get("jugador_id") or item.get("numero_carnet")
                if not jugador_id:
                    raise Exception(f"Tarjeta sin jugador seleccionado ({label})")

    if isinstance(data, dict):
        for jugador_id in data.keys():
            if not jugador_id or jugador_id in ("", "0", 0):
                raise Exception(f"Tarjeta sin jugador seleccionado ({label})")


@views.route('/api/guardar_inferiores', methods=['POST'])
def guardar_inferiores():

    data = request.get_json()
    print("DATA RECIBIDA =>", data)

    try:
        partido_id = int(data["partido_id"])
        goles_local = int(data.get("goles_local", 0))
        goles_visitante = int(data.get("goles_visitante", 0))

        goleadores_local = data.get("goleadores_local", [])
        goleadores_visitante = data.get("goleadores_visitante", [])

        amarillas_local = data.get("amarillas_local", [])
        rojas_local = data.get("rojas_local", [])
        amarillas_visitante = data.get("amarillas_visitante", [])
        rojas_visitante = data.get("rojas_visitante", [])

        # ==================================================
        # HELPERS
        # ==================================================
        def validar_tarjetas(data, label=""):
            if not data:
                return

            if isinstance(data, list):
                for item in data:
                    if not item or item in ("", "0", 0):
                        raise Exception(f"Tarjeta sin jugador seleccionado ({label})")

            if isinstance(data, dict):
                for jugador_id in data.keys():
                    if not jugador_id or jugador_id in ("", "0", 0):
                        raise Exception(f"Tarjeta sin jugador seleccionado ({label})")

        def normalizar_tarjetas(data):
            resultado = {}

            if isinstance(data, dict):
                for k, v in data.items():
                    resultado[str(k)] = int(v)
                return resultado

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, int):
                        resultado[str(item)] = resultado.get(str(item), 0) + 1
                return resultado

            return {}

        # ==================================================
        # VALIDACIONES
        # ==================================================
        validar_tarjetas(amarillas_local, "amarillas local")
        validar_tarjetas(rojas_local, "rojas local")
        validar_tarjetas(amarillas_visitante, "amarillas visitante")
        validar_tarjetas(rojas_visitante, "rojas visitante")

        amarillas_local = normalizar_tarjetas(amarillas_local)
        rojas_local = normalizar_tarjetas(rojas_local)
        amarillas_visitante = normalizar_tarjetas(amarillas_visitante)
        rojas_visitante = normalizar_tarjetas(rojas_visitante)

        # ==================================================
        # VALIDAR GOLES
        # ==================================================
        total_gl = sum(int(j.get("goles", 0)) for j in goleadores_local)
        total_gv = sum(int(j.get("goles", 0)) for j in goleadores_visitante)

        if total_gl != goles_local:
            return jsonify({"success": False, "message": "Los goles del local no coinciden"}), 400

        if total_gv != goles_visitante:
            return jsonify({"success": False, "message": "Los goles del visitante no coinciden"}), 400

        # ==================================================
        # UNIFICAR JUGADORES INVOLUCRADOS
        # ==================================================
        jugadores_local = set()
        jugadores_visitante = set()

        for j in goleadores_local:
            jid = j.get("id") or j.get("jugador_id") or j.get("numero_carnet")
            if jid:
                jugadores_local.add(int(jid))

        for j in goleadores_visitante:
            jid = j.get("id") or j.get("jugador_id") or j.get("numero_carnet")
            if jid:
                jugadores_visitante.add(int(jid))

        jugadores_local.update(map(int, amarillas_local.keys()))
        jugadores_local.update(map(int, rojas_local.keys()))
        jugadores_visitante.update(map(int, amarillas_visitante.keys()))
        jugadores_visitante.update(map(int, rojas_visitante.keys()))

        # ==================================================
        # GUARDAR JUGADORES LOCAL
        # ==================================================
        for jugador_id in jugadores_local:
            goles = next(
                (int(j.get("goles", 0)) for j in goleadores_local
                 if int(j.get("id") or j.get("jugador_id") or j.get("numero_carnet")) == jugador_id),
                0
            )

            estado = EstadoJugadorPartido(
                id_jugador=jugador_id,
                id_partido=partido_id,
                cant_goles=goles,
                tarjetas_amarillas=int(amarillas_local.get(str(jugador_id), 0)),
                tarjetas_rojas=int(rojas_local.get(str(jugador_id), 0))
            )
            db.session.add(estado)

        # ==================================================
        # GUARDAR JUGADORES VISITANTE
        # ==================================================
        for jugador_id in jugadores_visitante:
            goles = next(
                (int(j.get("goles", 0)) for j in goleadores_visitante
                 if int(j.get("id") or j.get("jugador_id") or j.get("numero_carnet")) == jugador_id),
                0
            )

            estado = EstadoJugadorPartido(
                id_jugador=jugador_id,
                id_partido=partido_id,
                cant_goles=goles,
                tarjetas_amarillas=int(amarillas_visitante.get(str(jugador_id), 0)),
                tarjetas_rojas=int(rojas_visitante.get(str(jugador_id), 0))
            )
            db.session.add(estado)

        # ==================================================
        # MARCAR PARTIDO COMO JUGADO
        # ==================================================
        partido = Partido.query.get_or_404(partido_id)
        partido.goles_local = goles_local
        partido.goles_visitante = goles_visitante
        partido.jugado = True

        db.session.commit()

        return jsonify({"success": True, "message": "Partido guardado correctamente"})

    except IntegrityError as e:
        db.session.rollback()
        if "estado_jugador_partido_pkey" in str(e.orig):
            return jsonify({"success": False, "message": "Este partido ya fue cargado"}), 400

        return jsonify({"success": False, "message": "Error de integridad en la base de datos"}), 500

    except Exception as e:
        db.session.rollback()
        print("ERROR REAL:", e)
        return jsonify({"success": False, "message": "Error interno del servidor"}), 500
        

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

            # RUTA REAL EN DISCO
            upload_folder = os.path.join(
                current_app.root_path,
                "static",
                "uploads",
                "noticias"
            )

            # Crear carpeta si no existe
            os.makedirs(upload_folder, exist_ok=True)

            filename = secure_filename(file.filename)
            new_filename = f"{int(datetime.datetime.utcnow().timestamp())}_{filename}"

            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)

            # URL PÚBLICA
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


@views.route('/cargar_resultados_admin')
@login_required
def cargar_resultados_admin():
    if current_user.rol != 'administrador':
        flash('Acceso denegado. Solo administradores pueden acceder a esta sección.', 'danger')
        return redirect(url_for('views.index'))
    return render_template('plantillasAdmin/cargar_resultados.html', usuario=current_user)