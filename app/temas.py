"""
Sistema de temas de ElTablón.

Un tema es una carpeta `app/themes/<slug>/` con:
  - `templates/`: las páginas públicas que quiera redefinir (index.html,
    tabla_posiciones.html, etc.). Lo que no defina se toma del tema `clasico`.
  - `static/`: CSS, JS e imágenes propios, servidos en `/tema/...`.
  - `theme.json`: nombre, descripción y modo (claro u oscuro).

Los templates de admin, periodista y emails viven en `app/templates/` y no
cambian con el tema. Ver `app/themes/README.md` para el contrato de datos.

Cada instancia usa un solo tema, elegido al arrancar: el de la liga
(`LIGA.tema`) o el de la variable de entorno `TEMA`.

Modo escaparate (`DEMO_TEMAS=1`): pensado para la demo pública. Cada visita puede
elegir el tema con `?tema=` y el color de marca con `?marca=%23RRGGBB`; la elección
queda en la sesión y se propaga en los enlaces. Para eso cada tema tiene su propio
entorno Jinja (las plantillas compiladas se guardan en caché por entorno).
"""
import json
import os
import re

from flask import Blueprint, Flask, g, has_request_context, request, send_from_directory, session
from jinja2 import ChoiceLoader, FileSystemLoader

TEMA_BASE = "clasico"
_COLOR = re.compile(r"#?([0-9a-fA-F]{6})")


class AppConTemas(Flask):
    """Flask que, en modo escaparate, usa un entorno Jinja distinto según el tema
    elegido en la visita. Sin escaparate se comporta exactamente como Flask."""

    entornos_por_tema = None  # {slug: Environment}; None = un solo tema para todos

    @property
    def jinja_env(self):
        entornos = self.entornos_por_tema
        if entornos and has_request_context():
            entorno = entornos.get(getattr(g, "tema_slug", None))
            if entorno is not None:
                return entorno
        return Flask.jinja_env.__get__(self, type(self))


def _dir_tema(app, slug):
    return os.path.join(app.root_path, "themes", slug)


def temas_disponibles(app):
    """Slugs de los temas instalados (carpetas con `templates/`), en orden alfabético."""
    base = os.path.join(app.root_path, "themes")
    return sorted(
        d for d in os.listdir(base)
        if not d.startswith("_") and os.path.isdir(os.path.join(base, d, "templates"))
    )


def _leer_meta(app, slug):
    meta = {"slug": slug, "nombre": slug.capitalize(), "descripcion": "", "modo": "oscuro"}
    ruta = os.path.join(_dir_tema(app, slug), "theme.json")
    if os.path.isfile(ruta):
        with open(ruta, encoding="utf-8") as f:
            meta.update(json.load(f))
    return meta


def _loaders_de(app, slug):
    """Carpetas de plantillas del tema `slug`, con el tema base como respaldo."""
    carpetas = [os.path.join(_dir_tema(app, slug), "templates")]
    if slug != TEMA_BASE:
        carpetas.append(os.path.join(_dir_tema(app, TEMA_BASE), "templates"))
    return [FileSystemLoader(c) for c in carpetas]


def cargar_tema(app, slug, escaparate=False):
    """Configura los templates y estáticos del tema `slug` y devuelve su
    metadato (dict con `slug`, `nombre`, `descripcion`, `modo`...).

    Con `escaparate=True` deja además habilitada la elección de tema y color por visita."""
    slug = (slug or TEMA_BASE).strip().lower()
    if slug not in temas_disponibles(app):
        raise RuntimeError(
            f"El tema {slug!r} no existe en app/themes/. Disponibles: {', '.join(temas_disponibles(app))}"
        )

    # Orden de búsqueda: tema activo -> tema base -> app/templates (admin, emails).
    app.loader_plantillas = app.jinja_loader
    app.jinja_loader = ChoiceLoader(_loaders_de(app, slug) + [app.loader_plantillas])

    meta = _leer_meta(app, slug)
    if escaparate:
        _habilitar_escaparate(app, slug)
    else:
        static = os.path.join(_dir_tema(app, slug), "static")
        if os.path.isdir(static):
            app.register_blueprint(
                Blueprint("tema", __name__, static_folder=static, static_url_path="/tema")
            )
    return meta


def tema_actual(app):
    """Metadato del tema con el que se está respondiendo (el de la visita en modo escaparate)."""
    if app.config.get("ESCAPARATE") and has_request_context():
        return app.config["TEMAS_META"].get(getattr(g, "tema_slug", None), app.config["TEMA"])
    return app.config["TEMA"]


def _habilitar_escaparate(app, slug_defecto):
    # Solo los temas visibles se pueden elegir (`"visible": false` en theme.json los oculta:
    # siguen instalados como respaldo, pero no se ofrecen en el selector ni por ?tema=).
    metas = {s: _leer_meta(app, s) for s in temas_disponibles(app)}
    metas = {s: m for s, m in metas.items() if m.get("visible", True)}
    if slug_defecto not in metas:
        slug_defecto = next(iter(metas))
    app.config["ESCAPARATE"] = True
    app.config["TEMAS_META"] = metas
    app.config["TEMA"] = metas[slug_defecto]

    # Las cookies de sesión tienen que viajar dentro de un iframe (la landing incrusta la demo).
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

    base = app.jinja_env  # entorno por defecto (ya con filtros y globales propios)
    entornos = {}
    for slug in metas:
        entorno = app.create_jinja_environment()
        entorno.loader = ChoiceLoader(_loaders_de(app, slug) + [app.loader_plantillas])
        entorno.filters.update(base.filters)
        entorno.tests.update(base.tests)
        for nombre, valor in base.globals.items():
            entorno.globals.setdefault(nombre, valor)
        entornos[slug] = entorno
    app.entornos_por_tema = entornos

    @app.before_request
    def _elegir_tema():
        # ?tema= y ?marca= se guardan en la sesión; ?embed=1 oculta el selector (para iframes).
        tema = (request.args.get("tema") or "").lower()
        if tema in metas:
            session["tema"] = tema
        if "marca" in request.args:
            valor = request.args.get("marca", "")
            coincide = _COLOR.fullmatch(valor)
            if coincide:
                session["marca"] = "#" + coincide.group(1).lower()
            else:
                session.pop("marca", None)  # vacío o "auto": vuelve al color propio del tema
        if request.args.get("embed"):
            session["embed"] = 1

        g.tema_slug = session.get("tema") if session.get("tema") in metas else slug_defecto
        g.tema_explicito = session.get("tema")
        g.marca = session.get("marca")
        g.embed = bool(session.get("embed"))

    @app.url_defaults
    def _propagar_eleccion(endpoint, values):
        # Si las cookies no llegan (iframe de otro sitio), la elección viaja en los enlaces.
        if not has_request_context() or endpoint.endswith("static"):
            return
        if getattr(g, "tema_explicito", None):
            values.setdefault("tema", g.tema_explicito)
        if getattr(g, "marca", None):
            values.setdefault("marca", g.marca)
        if getattr(g, "embed", False):
            values.setdefault("embed", 1)

    # Los estáticos salen del tema de la visita: /tema/css/cancha.css, /tema/js/reflectores.js...
    bp = Blueprint("tema", __name__)

    def servir(filename):
        slug = getattr(g, "tema_slug", slug_defecto)
        return send_from_directory(os.path.join(_dir_tema(app, slug), "static"), filename)

    bp.add_url_rule("/tema/<path:filename>", endpoint="static", view_func=servir)
    app.register_blueprint(bp)


def contexto_escaparate(app):
    """Datos para el selector de diseño y color; None si no hay modo escaparate."""
    if not app.config.get("ESCAPARATE") or not has_request_context():
        return None
    return {
        "temas": [
            {"slug": s, "nombre": m["nombre"], "descripcion": m.get("descripcion", "")}
            for s, m in app.config["TEMAS_META"].items()
        ],
        "actual": getattr(g, "tema_slug", None),
        "marca": getattr(g, "marca", None),
        "embed": getattr(g, "embed", False),
    }
