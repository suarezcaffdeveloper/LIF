import contextvars

from flask import g, has_app_context
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session as _FSASession

# Bind key usado en SQLALCHEMY_BINDS para la base de datos demo (ver app/__init__.py)
DEMO_BIND_KEY = "demo"

# Rol que activa el modo demo al iniciar sesión (ver before_request en app/__init__.py)
DEMO_ROLE = "demo"

# Fallback para contextos sin request activo (p. ej. el comando CLI de seed),
# donde no existe `flask.g` para guardar el flag por-request.
_demo_mode_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "demo_mode", default=False
)


def is_demo_mode() -> bool:
    """Indica si la sesión actual debe leer/escribir en la base de datos demo."""
    if has_app_context() and "use_demo_db" in g:
        return bool(g.use_demo_db)
    return _demo_mode_ctx.get()


def set_demo_mode(active: bool) -> None:
    """Activa o desactiva el modo demo para el contexto actual (request o CLI)."""
    if has_app_context():
        g.use_demo_db = active
    _demo_mode_ctx.set(active)


class DemoRoutingSession(_FSASession):
    """
    Sesión de SQLAlchemy que, cuando el modo demo está activo, desvía todas las
    lecturas y escrituras al bind 'demo' (base de datos de pruebas) en lugar del
    bind por defecto. No requiere ningún cambio en las rutas ni en los modelos:
    el mismo `db.session`/`Modelo.query` de siempre queda apuntando a otra base
    de datos física de forma transparente.
    """

    def get_bind(self, mapper=None, clause=None, bind=None, **kwargs):
        if bind is None and is_demo_mode():
            engines = self._db.engines
            if DEMO_BIND_KEY in engines:
                return engines[DEMO_BIND_KEY]
        return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kwargs)


db = SQLAlchemy(session_options={"class_": DemoRoutingSession})
