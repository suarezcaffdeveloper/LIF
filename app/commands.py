from flask.cli import with_appcontext
import click
import random
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

from app.database.db import db, DEMO_BIND_KEY, set_demo_mode
from app.models.models import Usuario
from app.ligas import LIGA, FORMATO


@click.command("create-admin")
@with_appcontext
def create_admin():
    email = LIGA.email_admin_inicial
    password = "admin123"  # luego la cambiás
    nombre = "Administrador"

    if Usuario.query.filter_by(email=email).first():
        click.echo("❌ El usuario admin ya existe")
        return

    admin = Usuario(
        nombre_completo=nombre,
        email=email,
        contraseña=generate_password_hash(password),
        rol="admin",
        fecha_registro=datetime.utcnow()
    )

    db.session.add(admin)
    db.session.commit()

    click.echo("✅ Usuario admin creado")


@click.command("reset-demo-db")
@click.option(
    "--seed/--no-seed",
    default=True,
    help="Poblar la base demo con datos de ejemplo después de recrearla (por defecto sí).",
)
@with_appcontext
def reset_demo_db(seed):
    """Elimina, recrea y (opcionalmente) puebla la base de datos demo (demo_db).

    Esta base es la que ven los usuarios con rol 'demo' (ver DemoRoutingSession
    en app/database/db.py): nunca toca la base de datos real.
    """
    click.echo("⏳ Eliminando y recreando el esquema de la base demo...")
    # Los modelos no declaran __bind_key__ (viven en la metadata por defecto),
    # así que creamos/eliminamos ese mismo esquema pero apuntando explícitamente
    # al engine del bind 'demo', en vez de usar db.create_all(bind_key=...)
    # (eso último sólo aplicaría a modelos con __bind_key__ == 'demo').
    demo_engine = db.engines[DEMO_BIND_KEY]
    db.metadata.drop_all(bind=demo_engine)
    db.metadata.create_all(bind=demo_engine)
    click.echo("✅ Esquema demo recreado")

    if not seed:
        return

    # Activamos el modo demo para que TODO lo que se agregue con `db.session`
    # a partir de acá (usando los mismos modelos de siempre) se escriba en la
    # base demo y no en la real.
    set_demo_mode(True)
    try:
        _seed_demo_data()
        db.session.commit()
        click.echo("✅ Datos de ejemplo cargados en la base demo")
        click.echo(f"   Login demo (panel admin) -> {LIGA.email_demo} / demo123")
        click.echo(f"   Login demo (periodista)  -> {LIGA.email_periodista_demo} / demo123")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error al poblar la base demo: {e}")
        raise
    finally:
        set_demo_mode(False)
        db.session.remove()


@click.command("seed-liga-demo")
@click.option("--yes", is_flag=True, help="No pedir confirmación.")
@with_appcontext
def seed_liga_demo(yes):
    """Borra y vuelve a crear la base PRINCIPAL con datos ficticios.

    Solo corre en una liga de demostración (LIGA=demo): con cualquier liga real
    se niega, para no borrar nunca datos verdaderos.
    """
    if not LIGA.demo:
        raise click.ClickException(
            f"Este comando solo corre en una liga de demostración (LIGA=demo); la liga activa es {LIGA.slug!r}."
        )
    destino = db.engine.url.render_as_string(hide_password=True)
    if not yes:
        click.confirm(f"Se BORRARÁN todas las tablas de {destino}. ¿Continuar?", abort=True)

    db.metadata.drop_all(bind=db.engine)
    db.metadata.create_all(bind=db.engine)
    resumen = _seed_demo_data()
    db.session.commit()
    click.echo(f"✅ Base {destino} poblada: {resumen}")


# Nombres para los jugadores ficticios.
_NOMBRES = ["Matías", "Lucas", "Tomás", "Franco", "Joaquín", "Nicolás", "Diego", "Martín", "Agustín", "Bruno"]
_APELLIDOS = ["Ferreyra", "Benítez", "Aguirre", "Ibarra", "Medina", "Rojas", "Sosa", "Paz", "Ledesma", "Acosta", "Vega", "Molina"]


def _rondas(n):
    """Todos contra todos (método del círculo): lista de fechas, cada una con pares (local, visitante)."""
    equipos = list(range(n))
    for _ in range(n - 1):
        yield [(equipos[i], equipos[n - 1 - i]) for i in range(n // 2)]
        equipos = [equipos[0]] + [equipos[-1]] + equipos[1:-1]


def _seed_demo_data():
    """Datos ficticios completos: 12 clubes en todas las categorías de la liga, cuatro
    fechas jugadas con goles y tarjetas, una fecha próxima con días relativos a hoy
    (la cuenta regresiva siempre tiene un partido por delante), noticias y videos.

    Escribe en la base activa de la sesión (la real o la del modo demo) y devuelve
    un resumen de lo creado. Es determinista: siempre genera lo mismo salvo las fechas.
    """
    from app.ligas.demo.clubes import CLUBES, url_escudo
    from app.models.models import (
        Temporada, Torneo, Fase, Club, Equipo, Jugador, JugadorEquipo,
        Partido, EstadoJugadorPartido, Noticia, Video,
    )

    azar = random.Random(2026)
    hoy = date.today()

    # Cuenta demo=administrador: rol 'administrador' (pasa los chequeos de
    # permisos de las rutas de admin, ej. adminview) y es_demo=True (queda
    # aislada en la base demo, ver _es_cuenta_demo en app/__init__.py).
    demo_user = Usuario(
        nombre_completo="Administrador Demo",
        email=LIGA.email_demo,
        rol="administrador",
        es_demo=True,
        fecha_registro=datetime.utcnow(),
    )
    demo_user.set_password("demo123")
    db.session.add(demo_user)

    periodista_demo = Usuario(
        nombre_completo="Periodista Demo",
        email=LIGA.email_periodista_demo,
        rol="periodista",
        es_demo=True,
        fecha_registro=datetime.utcnow(),
    )
    periodista_demo.set_password("demo123")
    db.session.add(periodista_demo)
    db.session.flush()

    # Temporada con los torneos y fases que define el formato de la liga.
    temporada = Temporada(nombre=str(hoy.year), activa=True)
    db.session.add(temporada)
    db.session.flush()
    torneo_activo, fase_regular = None, None
    for nombre_torneo in FORMATO.TORNEOS:
        torneo = Torneo(nombre=nombre_torneo, temporada=temporada, activo=(nombre_torneo == FORMATO.TORNEO_INICIAL))
        db.session.add(torneo)
        db.session.flush()
        for orden, (nombre_fase, ida_vuelta) in enumerate(FORMATO.FASES, start=1):
            fase = Fase(nombre=nombre_fase, orden=orden, torneo=torneo, ida_vuelta=ida_vuelta)
            db.session.add(fase)
            if torneo.activo and orden == 1:
                torneo_activo, fase_regular = torneo, fase
    db.session.flush()

    # Clubes y jugadores (los mismos jugadores sirven en todas las categorías del club).
    clubes, jugadores = [], []
    carnet = 1
    for nombre, localidad, _color in CLUBES:
        club = Club(nombre=nombre, localidad=localidad, escudo_url=url_escudo(nombre))
        db.session.add(club)
        clubes.append(club)
    db.session.flush()
    for club in clubes:
        plantel = []
        for k in range(9):
            jugador = Jugador(
                numero_carnet=carnet,
                nombre=_NOMBRES[(carnet + k) % len(_NOMBRES)],
                apellido=_APELLIDOS[(carnet * 3 + k) % len(_APELLIDOS)],
                club=club,
            )
            db.session.add(jugador)
            plantel.append(jugador)
            carnet += 1
        jugadores.append(plantel)
    db.session.flush()

    # Equipos por categoría, con su plantel.
    partidos_creados = 0
    for categoria in LIGA.categorias:
        equipos = []
        for club, plantel in zip(clubes, jugadores):
            equipo = Equipo(club=club, categoria=categoria.parametro_url)
            db.session.add(equipo)
            equipos.append(equipo)
        db.session.flush()
        for equipo, plantel in zip(equipos, jugadores):
            for jugador in plantel[:8]:
                db.session.add(JugadorEquipo(numero_carnet=jugador.numero_carnet, equipo_id=equipo.id))
        db.session.flush()

        # Cuatro fechas jugadas (una por semana hacia atrás) y una próxima.
        for nro, cruces in enumerate(_rondas(len(clubes)), start=1):
            if nro > 5:
                break
            jugada = nro <= 4
            for pos, (local, visitante) in enumerate(cruces):
                if jugada:
                    fecha = hoy - timedelta(days=7 * (5 - nro) + 1)
                    goles_l = azar.choice([0, 0, 1, 1, 1, 2, 2, 3])
                    goles_v = azar.choice([0, 0, 1, 1, 2, 2, 3])
                else:
                    fecha = hoy + timedelta(days=2 + pos // 3)
                    goles_l = goles_v = 0
                partido = Partido(
                    fecha_partido=fecha,
                    hora_partido=time(11 + (pos % 4) * 2, 30 if pos % 2 else 0),
                    jornada=nro,
                    categoria=categoria.parametro_url,
                    torneo=torneo_activo,
                    fase=fase_regular,
                    equipo_local=equipos[local],
                    equipo_visitante=equipos[visitante],
                    goles_local=goles_l,
                    goles_visitante=goles_v,
                    jugado=jugada,
                )
                db.session.add(partido)
                db.session.flush()
                partidos_creados += 1

                if not jugada:
                    continue
                # Goles y tarjetas: se acumulan por jugador para respetar la clave (jugador, partido).
                estadisticas = {}
                for indice_club, goles in ((local, goles_l), (visitante, goles_v)):
                    for _ in range(goles):
                        autor = jugadores[indice_club][azar.choice([0, 0, 0, 1, 1, 2, 3])]
                        estadisticas.setdefault(autor.numero_carnet, [0, 0, 0])[0] += 1
                    if azar.random() < .35:
                        estadisticas.setdefault(jugadores[indice_club][azar.randrange(4, 9)].numero_carnet, [0, 0, 0])[1] += 1
                    if azar.random() < .05:
                        estadisticas.setdefault(jugadores[indice_club][azar.randrange(4, 9)].numero_carnet, [0, 0, 0])[2] += 1
                for id_jugador, (g, a, r) in estadisticas.items():
                    db.session.add(EstadoJugadorPartido(
                        id_jugador=id_jugador, id_partido=partido.id,
                        cant_goles=g, tarjetas_amarillas=a, tarjetas_rojas=r,
                    ))
        db.session.flush()

    # Noticias y videos de ejemplo (los videos son películas abiertas de Blender, de uso libre).
    noticias = [
        ("El puntero ganó el clásico y sigue arriba", "Primera", "puntero-gano-el-clasico",
         "<p>Con un gol sobre el final, el líder venció 2 a 1 y estiró a tres puntos su ventaja en la cima de la tabla.</p>"
         "<p>El próximo fin de semana visita a uno de los cuatro equipos que lo siguen.</p>"),
        ("La Sexta ya tiene a sus cuatro semifinalistas", "Inferiores", "sexta-ya-tiene-semifinalistas",
         "Se definieron los cuatro clasificados y los cruces arrancan el fin de semana."),
        ("Nuevo horario para la Reserva desde la próxima fecha", "Institucional", "nuevo-horario-reserva",
         "Desde la próxima fecha, los partidos de Reserva se juegan una hora antes que los de Primera."),
    ]
    for pos, (titulo, categoria, slug_noticia, contenido) in enumerate(noticias):
        db.session.add(Noticia(
            titulo=titulo, contenido=contenido, categoria=categoria, slug=slug_noticia,
            id_autor=periodista_demo.id_usuario,
            fecha_publicacion=datetime.utcnow() - timedelta(days=pos * 2 + 1),
        ))
    videos = [
        ("Resumen de la fecha 4", "https://www.youtube.com/watch?v=aqz-KE-bpKQ"),
        ("Los mejores goles del mes", "https://www.youtube.com/watch?v=eRsGyueVLvQ"),
        ("Entrevista al capitán del puntero", "https://www.youtube.com/watch?v=R6MlUcmOul8"),
    ]
    for pos, (titulo, url) in enumerate(videos):
        db.session.add(Video(
            titulo_video=titulo, url=url, descripcion="Video de muestra para el entorno demo.",
            id_autor=periodista_demo.id_usuario, jornada_jugada=4,
            fecha_subida=datetime.utcnow() - timedelta(days=pos * 3 + 1),
        ))
    db.session.flush()

    return f"{len(clubes)} clubes, {len(LIGA.categorias)} categorías, {partidos_creados} partidos"
