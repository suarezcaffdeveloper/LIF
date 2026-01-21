from ..database.db import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint, UniqueConstraint, Index
import datetime

class Club(db.Model):
    __tablename__ = 'club'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False, unique=True)
    localidad = db.Column(db.String(120), nullable=True)
    escudo_url = db.Column(db.String(300), nullable=True)

    equipos = db.relationship('Equipo', back_populates='club', lazy='select', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Club {self.nombre}>"

class Equipo(db.Model):
    __tablename__ = 'equipo'
    __table_args__ = (
        UniqueConstraint('club_id', 'categoria', name='uq_equipo_club_categoria'),
    )

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)

    club = db.relationship('Club', back_populates='equipos', lazy='joined')
    jugadores = db.relationship(
        'JugadorEquipo',
        back_populates='equipo',
        cascade='all, delete-orphan'
    )

    partidos_local = db.relationship(
        'Partido',
        foreign_keys='Partido.equipo_local_id',
        back_populates='equipo_local'
    )
    partidos_visitante = db.relationship(
        'Partido',
        foreign_keys='Partido.equipo_visitante_id',
        back_populates='equipo_visitante'
    )

    def __repr__(self):
        return f"<Equipo {self.club.nombre} - {self.categoria}>"

class Temporada(db.Model):
    __tablename__ = 'temporada'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20), nullable=False, unique=True)  # ej: "2025"
    activa = db.Column(db.Boolean, default=False)

    torneos = db.relationship(
        'Torneo',
        back_populates='temporada',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Temporada {self.nombre}>"

class Torneo(db.Model):
    __tablename__ = 'torneo'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)  # Apertura / Clausura

    temporada_id = db.Column(db.Integer, db.ForeignKey('temporada.id'), nullable=False)
    temporada = db.relationship('Temporada', back_populates='torneos')

    partidos = db.relationship('Partido', back_populates='torneo')
    fases = db.relationship('Fase', back_populates='torneo')

    def __repr__(self):
        return f"<Torneo {self.nombre} - {self.temporada.nombre}>"
    
class Fase(db.Model):
    __tablename__ = 'fase'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)  # si no definiste, poner default
    torneo_id = db.Column(db.Integer, db.ForeignKey('torneo.id'), nullable=False)
    ida_vuelta = db.Column(db.Boolean, default=False, nullable=False)

    torneo = db.relationship('Torneo', back_populates='fases')
    partidos = db.relationship('Partido', back_populates='fase')

class Jugador(db.Model):
    __tablename__ = 'jugador'

    numero_carnet = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)

    creado_en = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    club = db.relationship('Club', backref='jugadores', lazy='joined')
    equipos = db.relationship('JugadorEquipo', back_populates='jugador', lazy='select', cascade='all, delete-orphan')

    estadisticas = db.relationship('EstadoJugadorPartido', back_populates='jugador', lazy='select', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('nombre', 'apellido', 'club_id', name='uq_jugador_nombre_apellido_club'),
    )

    def __repr__(self):
        return f"<Jugador {self.nombre} {self.apellido} ({self.numero_carnet})>"

class JugadorEquipo(db.Model):
    __tablename__ = 'jugador_equipo'
    numero_carnet = db.Column(db.Integer, db.ForeignKey('jugador.numero_carnet'), primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), primary_key=True)
    #fecha_alta = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    #fecha_baja = db.Column(db.DateTime, nullable=True)

    jugador = db.relationship('Jugador', back_populates='equipos', lazy='joined')
    equipo = db.relationship('Equipo', back_populates='jugadores', lazy='joined')

    def __repr__(self):
        return f"<JugadorEquipo J:{self.numero_carnet} E:{self.equipo_id}>"

class Partido(db.Model):
    __tablename__ = 'partido'

    id = db.Column(db.Integer, primary_key=True)
    fecha_partido = db.Column(db.Date, nullable=True)
    hora_partido = db.Column(db.Time, nullable=True)
    jornada = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(20), nullable=False)

    torneo_id = db.Column(db.Integer, db.ForeignKey('torneo.id'), nullable=True)
    fase_id = db.Column(db.Integer, db.ForeignKey('fase.id'), nullable=True)

    equipo_local_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
    equipo_visitante_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)

    goles_local = db.Column(db.Integer, default=0, nullable=False)
    goles_visitante = db.Column(db.Integer, default=0, nullable=False)
    jugado = db.Column(db.Boolean, default=False, nullable=False)

    equipo_local = db.relationship(
        'Equipo',
        foreign_keys=[equipo_local_id],
        back_populates='partidos_local'
    )
    equipo_visitante = db.relationship(
        'Equipo',
        foreign_keys=[equipo_visitante_id],
        back_populates='partidos_visitante'
    )

    torneo = db.relationship('Torneo', back_populates='partidos')
    fase = db.relationship('Fase', back_populates='partidos')

    estadisticas_jugadores = db.relationship(
        'EstadoJugadorPartido',
        back_populates='partido',
        lazy='select',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Partido {self.id} J{self.jornada}>"



class EstadoJugadorPartido(db.Model):
    __tablename__ = 'estado_jugador_partido'
    id_jugador = db.Column(db.Integer, db.ForeignKey('jugador.numero_carnet'), primary_key=True)
    id_partido = db.Column(db.Integer, db.ForeignKey('partido.id'), primary_key=True)

    cant_goles = db.Column(db.Integer, default=0, nullable=False)
    tarjetas_amarillas = db.Column(db.Integer, default=0, nullable=False)
    tarjetas_rojas = db.Column(db.Integer, default=0, nullable=False)

    jugador = db.relationship('Jugador', back_populates='estadisticas', lazy='joined')
    partido = db.relationship('Partido', back_populates='estadisticas_jugadores', lazy='joined')

    def __repr__(self):
        return f"<EstadoJugadorPartido J:{self.id_jugador} P:{self.id_partido} goles:{self.cant_goles}>"

#datos para entrar como admin = email(admin123@gmail.com) contraseña (admin123)

class Usuario(db.Model):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    contraseña = db.Column(db.String(300), nullable=False)
    rol = db.Column(db.String(30), nullable=False, default='usuario')
    telefono = db.Column(db.String(50), nullable=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    noticias = db.relationship('Noticia', back_populates='autor', lazy='select', cascade='all, delete-orphan')
    videos = db.relationship('Video', back_populates='autor', lazy='select', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.contraseña = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.contraseña:
            return False  
        if not password:
            return False
        return check_password_hash(self.contraseña, password)


    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return str(self.id_usuario)

    def __repr__(self):
        return f"<Usuario {self.nombre_completo} ({self.rol})>"

class Noticia(db.Model):
    __tablename__ = 'noticia'

    id_noticia = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(300), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    id_autor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    categoria = db.Column(db.String(100), nullable=True)
    imagen_url = db.Column(db.String(400), nullable=True)
    slug = db.Column(db.String(200), nullable=True, unique=True)

    autor = db.relationship('Usuario', back_populates='noticias', lazy='joined')

    def __repr__(self):
        return f"<Noticia {self.titulo}>"

class Video(db.Model):
    __tablename__ = 'video'

    id_video = db.Column(db.Integer, primary_key=True)
    titulo_video = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_subida = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    id_autor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    jornada_jugada = db.Column(db.Integer, nullable=True)

    autor = db.relationship('Usuario', back_populates='videos', lazy='joined')

    def __repr__(self):
        return f"<Video {self.titulo_video}>"


# ---------------------------
# Tabla/Vista: TABLA DE POSICIONES
# Recomiendo implementarla en la BD como VIEW en lugar de tabla física.
# Mantengo un stub para que puedas mapearla en SQLAlchemy si usas introspección.
# ---------------------------
class TablaPosiciones(db.Model):
    __tablename__ = 'tabla_posiciones'
    __table_args__ = {'extend_existing': True}

    # clave primaria REAL de la vista
    id_equipo = db.Column(db.Integer, primary_key=True)

    nombre_equipo = db.Column(db.String)
    categoria = db.Column(db.String(50))

    partidos_jugados = db.Column(db.Integer)
    partidos_ganados = db.Column(db.Integer)
    partidos_empatados = db.Column(db.Integer)
    partidos_perdidos = db.Column(db.Integer)

    goles_a_favor = db.Column(db.Integer)
    goles_en_contra = db.Column(db.Integer)

    cantidad_puntos = db.Column(db.Integer)
    diferencia_gol = db.Column(db.Integer)

    def __repr__(self):
        return f"<TablaPosiciones Equipo:{self.nombre_equipo} Pts:{self.cantidad_puntos}>"


# ---------------------------
# INDEXES UTILES
# ---------------------------
Index('ix_equipo_club_categoria', Equipo.club_id, Equipo.categoria)
