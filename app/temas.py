"""
Sistema de temas de ElTablón.

Un tema es una carpeta `app/themes/<slug>/` con:
  - `templates/`: las páginas públicas que quiera redefinir (index.html,
    tabla_posiciones.html, etc.). Lo que no defina se toma del tema `clasico`.
  - `static/`: CSS, JS e imágenes propios, servidos en `/tema/...`.
  - `theme.json`: nombre, descripción y modo (claro u oscuro).

Los templates de admin, periodista y emails viven en `app/templates/` y no
cambian con el tema. Ver `app/themes/README.md` para el contrato de datos.

El tema activo es el de la liga (`LIGA.tema`) o el que indique la variable de
entorno `TEMA`. Se despliega una instancia por liga, así que se elige al
arrancar.
"""
import json
import os

from flask import Blueprint
from jinja2 import ChoiceLoader, FileSystemLoader

TEMA_BASE = "clasico"


def _dir_tema(app, slug):
    return os.path.join(app.root_path, "themes", slug)


def cargar_tema(app, slug):
    """Configura los templates y estáticos del tema `slug` y devuelve su
    metadato (dict con `slug`, `nombre`, `descripcion` y `modo`)."""
    slug = (slug or TEMA_BASE).strip().lower()
    carpeta = _dir_tema(app, slug)
    if not os.path.isdir(os.path.join(carpeta, "templates")):
        disponibles = sorted(
            d for d in os.listdir(os.path.join(app.root_path, "themes"))
            if os.path.isdir(os.path.join(app.root_path, "themes", d, "templates"))
        )
        raise RuntimeError(
            f"El tema {slug!r} no existe en app/themes/. Disponibles: {', '.join(disponibles)}"
        )

    # Orden de búsqueda: tema activo -> tema base -> app/templates (admin, emails).
    carpetas = [os.path.join(carpeta, "templates")]
    if slug != TEMA_BASE:
        carpetas.append(os.path.join(_dir_tema(app, TEMA_BASE), "templates"))
    app.jinja_loader = ChoiceLoader(
        [FileSystemLoader(c) for c in carpetas] + [app.jinja_loader]
    )

    static = os.path.join(carpeta, "static")
    if os.path.isdir(static):
        app.register_blueprint(
            Blueprint("tema", __name__, static_folder=static, static_url_path="/tema")
        )

    meta = {"slug": slug, "nombre": slug.capitalize(), "descripcion": "", "modo": "oscuro"}
    ruta_meta = os.path.join(carpeta, "theme.json")
    if os.path.isfile(ruta_meta):
        with open(ruta_meta, encoding="utf-8") as f:
            meta.update(json.load(f))
    return meta
