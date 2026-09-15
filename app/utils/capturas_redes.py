"""
Generación de imágenes listas para publicar en redes sociales (Instagram/Facebook)
a partir de datos reales del sistema: tabla de posiciones, resultados de la fecha
y próxima fecha. Se generan con Pillow (sin capturar pantallas ni depender de un
navegador headless) reusando la paleta/tipografía del sitio, y se suben a
Cloudinary con el mismo patrón que ya usa el proyecto para escudos/noticias.
"""
import io
import os
from functools import lru_cache

import requests
from flask import current_app
from PIL import Image, ImageDraw, ImageFont, ImageOps
from sqlalchemy import func, or_

import cloudinary
import cloudinary.uploader

from ..database.db import db
from ..models.models import CapturaJornada, Fase, Partido, Temporada, Torneo

# ---------------------------------------------------------------------------
# Constantes visuales (misma paleta que app/templates/base.html)
# ---------------------------------------------------------------------------
SIZE = 1080
BG = (10, 14, 20)          # --oscuro
PANEL = (17, 23, 32)       # --panel
PANEL_2 = (22, 29, 40)     # --panel-2
VERDE = (0, 229, 255)      # --verde
VERDE_DIM = (0, 184, 212)  # --verde-dim
TEXTO = (232, 237, 245)    # --texto
TEXTO_DIM = (122, 138, 158)  # --texto-dim

MARGEN_X = 85
ANCHO_CONTENIDO = SIZE - 2 * MARGEN_X

FASES_PLAYOFF = ["Cuartos", "Semifinal", "Final", "Finalísima"]
BLOQUES_CATEGORIAS = {
    "mayores": ["primera", "reserva"],
    "inferiores": ["quinta", "sexta", "septima"],
}

_UTILS_DIR = os.path.dirname(__file__)
_FONTS_DIR = os.path.join(_UTILS_DIR, "..", "static", "fonts")
_LOGO_PATH = os.path.join(_UTILS_DIR, "..", "static", "escudos", "logolif_transparente.png")
_ESCUDO_DEFAULT_PATH = os.path.join(_UTILS_DIR, "..", "static", "escudos", "predeterminada.png")


@lru_cache(maxsize=32)
def _font(nombre, size):
    return ImageFont.truetype(os.path.join(_FONTS_DIR, f"{nombre}.ttf"), size)


def _fit_text(draw, text, nombre_fuente, max_size, max_width, min_size=16):
    """Devuelve (font, texto) reduciendo el tamaño o truncando con '…' para
    que el texto entre en max_width."""
    size = max_size
    while size > min_size:
        font = _font(nombre_fuente, size)
        if draw.textlength(text, font=font) <= max_width:
            return font, text
        size -= 2

    font = _font(nombre_fuente, min_size)
    truncado = text
    while len(truncado) > 1 and draw.textlength(truncado + "…", font=font) > max_width:
        truncado = truncado[:-1]
    return font, (truncado + "…" if truncado != text else text)


@lru_cache(maxsize=256)
def _cargar_escudo(escudo_url, size):
    try:
        if not escudo_url:
            raise ValueError("sin escudo_url")
        resp = requests.get(escudo_url, timeout=6)
        resp.raise_for_status()
        imagen = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        imagen = Image.open(_ESCUDO_DEFAULT_PATH).convert("RGBA")

    imagen = ImageOps.fit(imagen, (size, size), Image.LANCZOS)
    mascara = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, size, size), fill=255)
    resultado = Image.new("RGBA", (size, size))
    resultado.paste(imagen, (0, 0), mascara)
    return resultado


def _temporada_activa():
    return Temporada.query.filter_by(activa=True).first()


def _torneo_activo(temporada):
    return Torneo.query.filter_by(activo=True, temporada_id=temporada.id).first()


def _dibujar_header(img, draw, categoria, jornada, kicker, titulo):
    logo = Image.open(_LOGO_PATH).convert("RGBA")
    logo.thumbnail((110, 110))
    img.paste(logo, (MARGEN_X, 50), logo)

    texto_x = MARGEN_X + 130
    draw.text((texto_x, 58), kicker, font=_font("BarlowCondensed-SemiBold", 28), fill=VERDE)
    draw.text((texto_x, 90), titulo, font=_font("BarlowCondensed-Bold", 54), fill=TEXTO)
    subtitulo = f"{categoria.capitalize()}  ·  Fecha {jornada}"
    draw.text((texto_x, 156), subtitulo, font=_font("Barlow-SemiBold", 28), fill=TEXTO_DIM)

    linea_y = 216
    draw.rectangle([MARGEN_X, linea_y, SIZE - MARGEN_X, linea_y + 3], fill=VERDE)
    return linea_y + 40


def _dibujar_pie(draw):
    draw.text(
        (SIZE // 2, SIZE - 34),
        "LIGA INTERPROVINCIAL",
        font=_font("BarlowCondensed-SemiBold", 22),
        fill=TEXTO_DIM,
        anchor="mm",
    )


# ---------------------------------------------------------------------------
# Tabla de posiciones
# ---------------------------------------------------------------------------
def generar_imagen_tabla_posiciones(categoria, jornada, temporada_nombre):
    # Import diferido: recalcular_tabla_posiciones vive en views.py, que a su
    # vez importa este módulo (ver generar_capturas_jornada más abajo).
    from ..routes.views import recalcular_tabla_posiciones

    tabla = recalcular_tabla_posiciones(categoria)
    if not tabla:
        return None

    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    y = _dibujar_header(
        img, draw, categoria, jornada,
        kicker=f"LIF · TEMPORADA {temporada_nombre}",
        titulo="TABLA DE POSICIONES",
    )

    columnas = [
        ("pj", "PJ", 60), ("g", "G", 55), ("e", "E", 55), ("p", "P", 55),
        ("gf", "GF", 60), ("gc", "GC", 60), ("dif", "DIF", 65), ("pts", "PTS", 80),
    ]
    ancho_stats = sum(c[2] for c in columnas)
    ancho_pos = 45
    ancho_equipo = ANCHO_CONTENIDO - ancho_pos - ancho_stats

    x_pos = MARGEN_X
    x_equipo = x_pos + ancho_pos
    x_stats = []
    cursor = x_equipo + ancho_equipo
    for _, _, ancho in columnas:
        x_stats.append(cursor)
        cursor += ancho

    header_h = 46
    font_header = _font("Barlow-SemiBold", 20)
    draw.text((x_equipo, y + header_h / 2), "EQUIPO", font=font_header, fill=TEXTO_DIM, anchor="lm")
    for (clave, etiqueta, ancho), x in zip(columnas, x_stats):
        draw.text((x + ancho / 2, y + header_h / 2), etiqueta, font=font_header, fill=TEXTO_DIM, anchor="mm")
    y += header_h

    filas = len(tabla)
    disponible = SIZE - y - 55
    alto_fila = max(34, min(70, disponible // filas))
    alto_total = alto_fila * filas
    y += max(0, (disponible - alto_total) // 2)
    fuente_size = max(18, min(28, int(alto_fila * 0.42)))
    font_pos = _font("BarlowCondensed-SemiBold", fuente_size)
    font_stat = _font("Barlow-Regular", fuente_size - 2)
    font_pts = _font("BarlowCondensed-Bold", fuente_size + 2)

    for i, fila in enumerate(tabla):
        top = y + i * alto_fila
        color_fondo = PANEL if i % 2 == 0 else PANEL_2
        draw.rectangle([MARGEN_X, top, SIZE - MARGEN_X, top + alto_fila], fill=color_fondo)
        draw.rectangle([MARGEN_X, top, MARGEN_X + 4, top + alto_fila], fill=VERDE if i < 8 else TEXTO_DIM)

        cy = top + alto_fila / 2
        draw.text((x_pos + ancho_pos / 2, cy), str(i + 1), font=font_pos, fill=TEXTO_DIM, anchor="mm")

        escudo_size = min(alto_fila - 10, 46)
        escudo = _cargar_escudo(fila.get("escudo_url"), escudo_size)
        img.paste(escudo, (x_equipo, int(cy - escudo_size / 2)), escudo)

        nombre_x = x_equipo + escudo_size + 14
        max_ancho_nombre = ancho_equipo - escudo_size - 20
        font_nombre, nombre = _fit_text(
            draw, fila["nombre_equipo"], "BarlowCondensed-SemiBold",
            fuente_size + 4, max_ancho_nombre
        )
        draw.text((nombre_x, cy), nombre, font=font_nombre, fill=TEXTO, anchor="lm")

        valores = [
            fila["partidos_jugados"], fila["partidos_ganados"], fila["partidos_empatados"],
            fila["partidos_perdidos"], fila["goles_a_favor"], fila["goles_en_contra"],
            fila["diferencia_gol"], fila["cantidad_puntos"],
        ]
        for (clave, _, ancho), x, valor in zip(columnas, x_stats, valores):
            fuente = font_pts if clave == "pts" else font_stat
            color = VERDE if clave == "pts" else TEXTO
            draw.text((x + ancho / 2, cy), str(valor), font=fuente, fill=color, anchor="mm")

    _dibujar_pie(draw)
    return img


# ---------------------------------------------------------------------------
# Resultados de la fecha / próxima fecha
# ---------------------------------------------------------------------------
def _partidos_de_jornada(categoria, torneo, jornada, jugado=None):
    """Partidos de una categoría/jornada en el torneo dado. `jugado=None` trae
    todos (jugados y pendientes) — es lo que necesita "próxima fecha", ya que
    algunas categorías pueden llevar cargados de antemano algunos resultados
    de la ronda siguiente mientras otras todavía no; la ronda sigue siendo
    "la próxima fecha" aunque ya tenga uno o dos resultados cargados."""
    query = (
        Partido.query
        .outerjoin(Partido.fase)
        .filter(
            Partido.torneo_id == torneo.id,
            func.lower(Partido.categoria) == categoria.lower(),
            Partido.jornada == jornada,
            or_(Partido.fase_id.is_(None), ~Fase.nombre.in_(FASES_PLAYOFF)),
        )
    )
    if jugado is not None:
        query = query.filter(Partido.jugado == jugado)
    return query.order_by(Partido.fecha_partido, Partido.hora_partido).all()


def _dibujar_partidos(categoria, jornada_mostrada, temporada_nombre, partidos, kicker, mostrar_marcador):
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    y = _dibujar_header(
        img, draw, categoria, jornada_mostrada,
        kicker=f"LIF · TEMPORADA {temporada_nombre}",
        titulo=kicker,
    )

    n = len(partidos)
    disponible = SIZE - y - 55
    alto_fila = max(90, min(150, disponible // n))
    alto_total = alto_fila * n
    y0 = y + max(0, (disponible - alto_total) // 2)

    font_score = _font("BarlowCondensed-Bold", 46)
    font_fecha = _font("Barlow-SemiBold", 24)

    for i, partido in enumerate(partidos):
        top = y0 + i * alto_fila
        pad = 12
        card_top = top + pad
        card_bottom = top + alto_fila - pad
        card_h = card_bottom - card_top
        draw.rounded_rectangle(
            [MARGEN_X, card_top, SIZE - MARGEN_X, card_bottom],
            radius=16, fill=PANEL,
        )

        cy = (card_top + card_bottom) / 2
        escudo_size = int(min(64, card_h - 24))

        escudo_local = _cargar_escudo(partido.equipo_local.club.escudo_url if partido.equipo_local.club else None, escudo_size)
        escudo_visit = _cargar_escudo(partido.equipo_visitante.club.escudo_url if partido.equipo_visitante.club else None, escudo_size)

        lx = MARGEN_X + 24
        img.paste(escudo_local, (lx, int(cy - escudo_size / 2)), escudo_local)
        rx = SIZE - MARGEN_X - 24 - escudo_size
        img.paste(escudo_visit, (rx, int(cy - escudo_size / 2)), escudo_visit)

        max_ancho_nombre = (ANCHO_CONTENIDO / 2) - escudo_size - 60
        font_local, nombre_local = _fit_text(
            draw, partido.equipo_local.club.nombre if partido.equipo_local.club else "—",
            "BarlowCondensed-SemiBold", 30, max_ancho_nombre
        )
        draw.text((lx + escudo_size + 16, cy), nombre_local, font=font_local, fill=TEXTO, anchor="lm")

        font_visit, nombre_visit = _fit_text(
            draw, partido.equipo_visitante.club.nombre if partido.equipo_visitante.club else "—",
            "BarlowCondensed-SemiBold", 30, max_ancho_nombre
        )
        draw.text((rx - 16, cy), nombre_visit, font=font_visit, fill=TEXTO, anchor="rm")

        cx = SIZE // 2
        if mostrar_marcador and partido.jugado:
            marcador = f"{partido.goles_local} - {partido.goles_visitante}"
            draw.text((cx, cy), marcador, font=font_score, fill=VERDE, anchor="mm")
        elif partido.fecha_partido or partido.hora_partido:
            draw.text((cx, cy - 12), "VS", font=font_score, fill=TEXTO_DIM, anchor="mm")
            fecha_str = partido.fecha_partido.strftime("%d/%m") if partido.fecha_partido else ""
            hora_str = partido.hora_partido.strftime("%H:%M") if partido.hora_partido else ""
            draw.text((cx, cy + 24), " ".join(filter(None, [fecha_str, hora_str])), font=font_fecha, fill=TEXTO_DIM, anchor="mm")
        else:
            draw.text((cx, cy), "VS", font=font_score, fill=TEXTO_DIM, anchor="mm")

    _dibujar_pie(draw)
    return img


def generar_imagen_resultados_fecha(categoria, jornada, temporada_nombre, torneo):
    partidos = _partidos_de_jornada(categoria, torneo, jornada, jugado=True)
    if not partidos:
        return None
    return _dibujar_partidos(categoria, jornada, temporada_nombre, partidos, "RESULTADOS DE LA FECHA", mostrar_marcador=True)


def generar_imagen_proxima_fecha(categoria, jornada, temporada_nombre, torneo):
    jornada_siguiente = jornada + 1
    partidos = _partidos_de_jornada(categoria, torneo, jornada_siguiente)
    if not partidos:
        return None
    return _dibujar_partidos(categoria, jornada_siguiente, temporada_nombre, partidos, "PRÓXIMA FECHA", mostrar_marcador=False)


# ---------------------------------------------------------------------------
# Orquestador: genera + sube a Cloudinary + persiste metadata
# ---------------------------------------------------------------------------
def _guardar_captura(temporada, bloque, categoria, jornada, tipo, imagen):
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    carpeta = f"capturas_redes/{temporada.nombre}/Jornada{jornada}{bloque.capitalize()}"
    public_id = f"{tipo}_{categoria.lower()}"

    resultado = cloudinary.uploader.upload(
        buffer,
        folder=carpeta,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )

    captura = CapturaJornada.query.filter_by(
        temporada_id=temporada.id, categoria=categoria.lower(), jornada=jornada, tipo=tipo
    ).first()
    if not captura:
        captura = CapturaJornada(
            temporada_id=temporada.id, bloque=bloque, categoria=categoria.lower(),
            jornada=jornada, tipo=tipo,
        )
        db.session.add(captura)

    captura.cloudinary_url = resultado.get("secure_url")
    captura.cloudinary_public_id = resultado.get("public_id")
    db.session.commit()
    return captura


def generar_capturas_jornada(bloque, jornada):
    """Genera y sube las capturas (tabla de posiciones, resultados y próxima
    fecha) de todas las categorías de un bloque ('mayores'/'inferiores') para
    la jornada indicada. Nunca lanza excepción: un fallo puntual (ej. un
    escudo caído) se loguea y se sigue con el resto."""
    bloque = bloque.lower().strip()
    categorias = BLOQUES_CATEGORIAS.get(bloque)
    if not categorias:
        current_app.logger.warning("generar_capturas_jornada: bloque inválido %r", bloque)
        return []

    temporada = _temporada_activa()
    if not temporada:
        current_app.logger.warning("generar_capturas_jornada: no hay temporada activa")
        return []

    torneo = _torneo_activo(temporada)
    if not torneo:
        current_app.logger.warning("generar_capturas_jornada: no hay torneo activo")
        return []

    generadas = []
    for categoria in categorias:
        generadores = [
            ("tabla_posiciones", lambda c=categoria: generar_imagen_tabla_posiciones(c, jornada, temporada.nombre)),
            ("resultados", lambda c=categoria: generar_imagen_resultados_fecha(c, jornada, temporada.nombre, torneo)),
            ("proxima_fecha", lambda c=categoria: generar_imagen_proxima_fecha(c, jornada, temporada.nombre, torneo)),
        ]
        for tipo, generador in generadores:
            try:
                imagen = generador()
                if imagen is None:
                    continue
                captura = _guardar_captura(temporada, bloque, categoria, jornada, tipo, imagen)
                generadas.append(captura)
                current_app.logger.info(
                    "Captura generada: %s J%s %s -> %s", categoria, jornada, tipo, captura.cloudinary_url
                )
            except Exception:
                current_app.logger.exception(
                    "No se pudo generar la captura %s de %s (jornada %s)", tipo, categoria, jornada
                )

    return generadas
