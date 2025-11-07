from ..database.db import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)

    jugadores = db.relationship('Jugador', backref='equipo', lazy=True)


class Jugador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('nombre', 'apellido', 'equipo_id', 'categoria', name='jugador_unico'),
    )


class Partido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_partido = db.Column(db.Date, nullable=False)
    jornada = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(20), nullable=False)

    equipo_local_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
    equipo_visitante_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)

    goles_local = db.Column(db.Integer, default=0)
    goles_visitante = db.Column(db.Integer, default=0)
    jugado = db.Column(db.Boolean, default=False)

    equipo_local = db.relationship("Equipo", foreign_keys=[equipo_local_id], backref='partidos_local')
    equipo_visitante = db.relationship("Equipo", foreign_keys=[equipo_visitante_id], backref='partidos_visitante')


class EstadoJugadorPartido(db.Model):
    __tablename__ = 'estado_jugador_partido'

    id_jugador = db.Column(db.Integer, db.ForeignKey('jugador.id'), primary_key=True)
    id_partido = db.Column(db.Integer, db.ForeignKey('partido.id'), primary_key=True)

    cant_goles = db.Column(db.Integer, default=0)
    tarjetas_amarillas = db.Column(db.Integer, default=0)
    tarjetas_rojas = db.Column(db.Integer, default=0)

    jugador = db.relationship('Jugador', backref='estadisticas')
    partido = db.relationship('Partido', backref='estadisticas_jugadores')


class Usuario(db.Model):
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    contraseña = db.Column(db.String, nullable=False)
    rol = db.Column(db.String, nullable=False)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))

    noticias = db.relationship('Noticia', backref='autor', lazy=True)
    videos = db.relationship('Video', backref='autor', lazy=True)
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return str(self.id_usuario)
    
    def set_password(self, password):
        """Guarda el hash de la contraseña."""
        self.contraseña = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta."""
        return check_password_hash(self.contraseña, password)
    
    

class Noticia(db.Model):
    id_noticia = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String, nullable=False)
    contenido = db.Column(db.String, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, nullable=False)
    id_autor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    categoria = db.Column(db.String, nullable=False)
    imagen_url = db.Column(db.String)


class Video(db.Model):
    id_video = db.Column(db.Integer, primary_key=True)
    titulo_video = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)
    descripcion = db.Column(db.String)
    fecha_subida = db.Column(db.DateTime, nullable=False)
    id_autor = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    jornada_jugada = db.Column(db.Integer)
    
class TablaPosiciones(db.Model):
    __tablename__ = 'tabla_posiciones'
    __table_args__ = {'extend_existing': True}

    id_equipo = db.Column(db.Integer)
    nombre_equipo = db.Column(db.String)
    categoria = db.Column(db.String(50), nullable=True)
    partidos_jugados = db.Column(db.Integer)
    partidos_ganados = db.Column(db.Integer)
    partidos_empatados = db.Column(db.Integer)
    partidos_perdidos = db.Column(db.Integer)
    goles_a_favor = db.Column(db.Integer)
    goles_en_contra = db.Column(db.Integer)
    cantidad_puntos = db.Column(db.Integer)
    diferencia_gol = db.Column(db.Integer)
    id_posicion = db.Column(db.Integer, primary_key=True)

