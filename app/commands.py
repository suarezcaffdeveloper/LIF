from flask.cli import with_appcontext
import click
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash

from app.database.db import db, DEMO_BIND_KEY, DEMO_ROLE, set_demo_mode
from app.models.models import Usuario


@click.command("create-admin")
@with_appcontext
def create_admin():
    email = "admin@liga.com"
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
        click.echo("   Login demo -> email: demo@liga.com / password: demo123")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error al poblar la base demo: {e}")
        raise
    finally:
        set_demo_mode(False)
        db.session.remove()


def _seed_demo_data():
    from app.models.models import (
        Temporada, Torneo, Fase, Club, Equipo, Jugador, JugadorEquipo,
        Partido, EstadoJugadorPartido, Noticia, Video,
    )

    demo_user = Usuario(
        nombre_completo="Usuario Demo",
        email="demo@liga.com",
        rol=DEMO_ROLE,
        fecha_registro=datetime.utcnow(),
    )
    demo_user.set_password("demo123")
    db.session.add(demo_user)

    periodista_demo = Usuario(
        nombre_completo="Periodista Demo",
        email="periodista.demo@liga.com",
        rol="periodista",
        fecha_registro=datetime.utcnow(),
    )
    periodista_demo.set_password("demo123")
    db.session.add(periodista_demo)
    db.session.flush()

    temporada = Temporada(nombre="2026-demo", activa=True)
    db.session.add(temporada)
    db.session.flush()

    torneo = Torneo(nombre="Apertura Demo", temporada=temporada, activo=True)
    db.session.add(torneo)
    db.session.flush()

    fase = Fase(nombre="Regular", orden=1, torneo=torneo, ida_vuelta=False)
    db.session.add(fase)
    db.session.flush()

    clubes_info = [
        ("Atlético Demo", "Ciudad Norte"),
        ("Deportivo Muestra", "Ciudad Sur"),
        ("Club Prototipo", "Ciudad Este"),
        ("Unión Ejemplo", "Ciudad Oeste"),
    ]
    clubes = []
    for nombre, localidad in clubes_info:
        club = Club(nombre=nombre, localidad=localidad)
        db.session.add(club)
        clubes.append(club)
    db.session.flush()

    equipos = []
    for club in clubes:
        equipo = Equipo(club=club, categoria="Primera")
        db.session.add(equipo)
        equipos.append(equipo)
    db.session.flush()

    nombres = ["Juan", "Carlos", "Diego", "Martín", "Lucas", "Nicolás"]
    apellidos = ["Gómez", "Pérez", "Fernández", "López", "Díaz", "Romero"]

    carnet = 1
    jugadores_por_equipo = {}
    for i, equipo in enumerate(equipos):
        jugadores_equipo = []
        for j in range(6):
            jugador = Jugador(
                numero_carnet=carnet,
                nombre=nombres[(i + j) % len(nombres)],
                apellido=apellidos[(i * 3 + j) % len(apellidos)],
                club=equipo.club,
            )
            db.session.add(jugador)
            db.session.flush()
            db.session.add(JugadorEquipo(numero_carnet=jugador.numero_carnet, equipo_id=equipo.id))
            jugadores_equipo.append(jugador)
            carnet += 1
        jugadores_por_equipo[equipo.id] = jugadores_equipo
    db.session.flush()

    resultados = [
        (0, 1, 2, 1),
        (2, 3, 0, 0),
        (1, 3, 1, 1),
        (0, 2, 3, 2),
        (1, 2, 2, 2),
        (0, 3, 1, 0),
    ]
    for jornada, (local_i, visitante_i, gl, gv) in enumerate(resultados, start=1):
        partido = Partido(
            fecha_partido=date(2026, 3, jornada),
            hora_partido=time(16, 0),
            jornada=jornada,
            categoria="Primera",
            torneo=torneo,
            fase=fase,
            equipo_local=equipos[local_i],
            equipo_visitante=equipos[visitante_i],
            goles_local=gl,
            goles_visitante=gv,
            jugado=True,
        )
        db.session.add(partido)
        db.session.flush()

        if gl:
            goleador = jugadores_por_equipo[equipos[local_i].id][0]
            db.session.add(EstadoJugadorPartido(
                id_jugador=goleador.numero_carnet, id_partido=partido.id, cant_goles=gl
            ))
        if gv:
            goleador = jugadores_por_equipo[equipos[visitante_i].id][0]
            db.session.add(EstadoJugadorPartido(
                id_jugador=goleador.numero_carnet, id_partido=partido.id, cant_goles=gv
            ))
    db.session.flush()

    db.session.add(Noticia(
        titulo="Bienvenido al modo demo",
        contenido=(
            "Este contenido fue generado por 'flask reset-demo-db' para mostrar "
            "el panel de noticias con datos de prueba, sin tocar la base real."
        ),
        id_autor=periodista_demo.id_usuario,
        categoria="General",
        slug="bienvenido-al-modo-demo",
    ))

    db.session.add(Video(
        titulo_video="Resumen de ejemplo",
        url="https://www.youtube.com/watch?v=demo00001",
        descripcion="Video de muestra para el entorno demo.",
        id_autor=periodista_demo.id_usuario,
        jornada_jugada=1,
    ))
