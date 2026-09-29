"""Clubes ficticios de la liga de demostración (nombre, localidad, color del escudo).

Los nombres son inventados a propósito: la demo nunca muestra clubes ni escudos reales.
"""
import unicodedata

CLUBES = [
    ("Unión del Valle", "Villa del Valle", "#12805A"),
    ("Atlético Norte", "Puerto Norte", "#D99A0B"),
    ("Deportivo Sur", "Colonia Sur", "#D64545"),
    ("Sportivo Central", "Centro", "#0E8F8F"),
    ("Rápido del Este", "Costa Este", "#6B54D6"),
    ("Juventud Arroyo", "Arroyo Claro", "#E2731F"),
    ("Club Faro", "Punta Faro", "#2A7BD6"),
    ("Sociedad Fomento", "Barrio Fomento", "#C23A93"),
    ("Barrio Oeste", "Oeste Chico", "#5E9E1E"),
    ("Social Ribera", "La Ribera", "#B8A400"),
    ("Puerto Unido", "Puerto Viejo", "#3F5BD6"),
    ("Independencia FC", "San Ignacio", "#D42E5B"),
]


def slug(nombre):
    """'Unión del Valle' -> 'union-del-valle' (nombre de archivo del escudo)."""
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return "-".join(sin_tildes.lower().split())


def monograma(nombre):
    """Dos iniciales de las palabras significativas: 'Unión del Valle' -> 'UV'."""
    palabras = [p for p in nombre.split() if p.lower() not in {"de", "del", "la", "el", "los", "las"}]
    return "".join(p[0] for p in palabras[:2]).upper()


def url_escudo(nombre):
    return f"/static/escudos/demo/{slug(nombre)}.png"
