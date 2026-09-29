"""
Configuración de liga de ElTablón.

Cada liga vive en su propia carpeta (`app/ligas/<slug>/`) con dos archivos:
  - `__init__.py`: define `LIGA` (marca, colores, categorías, cuentas iniciales).
  - `formato.py`: reglas del torneo que son propias de esa liga (torneos, fases,
    cruces de playoff). Todo lo específico de una liga va acá, nunca en views.py.

La liga activa se elige con la variable de entorno `LIGA` (por defecto `lif`).
Como se despliega una instancia por liga, se carga una sola vez al importar.
"""
import importlib
import os
from dataclasses import dataclass, field, replace

PRODUCTO = "ElTablón"


@dataclass(frozen=True)
class Categoria:
    slug: str            # clave interna en minúsculas, sin tildes (ej. 'septima')
    etiqueta: str        # nombre corto para menús (ej. 'Séptima')
    etiqueta_larga: str  # nombre completo (ej. 'Séptima División')
    bloque: str          # grupo al que pertenece (ej. 'mayores' o 'inferiores')

    @property
    def parametro_url(self):
        """Valor que usan las rutas de fixture/tabla (ej. 'Septima')."""
        return self.slug.capitalize()


@dataclass(frozen=True)
class Liga:
    slug: str
    nombre: str                      # 'Liga Interprovincial de Fútbol'
    nombre_corto: str                # 'LIF'
    hero_lineas: tuple               # título del inicio en varias líneas
    descripcion: str
    logo: str                        # ruta dentro de static/
    url_publica: str
    email_remitente: str
    categorias: tuple = field(default_factory=tuple)
    tema: str = "clasico"
    resaltar_letra: int = -1         # índice de la letra de la sigla que va en color de acento (-1: ninguna)
    # Colores de marca opcionales para temas claros (el tema deriva el resto de la
    # paleta). Sin valor, cada tema usa su paleta propia.
    color_marca: str = ""            # ej. '#0B4A34'
    color_marca_2: str = ""          # color de contraste, ej. '#FF5A36'
    # cuentas iniciales / demo
    email_admin_inicial: str = "admin@liga.com"
    email_demo: str = "demo@liga.com"
    email_periodista_demo: str = "periodista.demo@liga.com"
    # paleta (hex); base.html y las capturas para redes la leen de acá
    acento: str = "#00e5ff"
    acento_dim: str = "#00b8d4"
    fondo: str = "#0a0e14"
    panel: str = "#111720"
    panel_2: str = "#161d28"
    texto: str = "#e8edf5"
    texto_dim: str = "#7a8a9e"

    @property
    def slugs_categorias(self):
        return [c.slug for c in self.categorias]

    @property
    def bloques(self):
        """{'mayores': ['primera', 'reserva'], 'inferiores': [...]} en orden."""
        resultado = {}
        for c in self.categorias:
            resultado.setdefault(c.bloque, []).append(c.slug)
        return resultado

    @property
    def bloques_categorias(self):
        """Igual que `bloques`, pero con objetos Categoria (para armar menús)."""
        resultado = {}
        for c in self.categorias:
            resultado.setdefault(c.bloque, []).append(c)
        return resultado

    def categorias_de(self, bloque):
        return [c for c in self.categorias if c.bloque == bloque]

    def categoria(self, slug):
        return next((c for c in self.categorias if c.slug == slug), None)

    def rgb(self, nombre_color):
        """Color de la paleta como tupla (r, g, b), para Pillow."""
        hex_ = getattr(self, nombre_color).lstrip("#")
        return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4))


def _cargar():
    slug = os.environ.get("LIGA", "lif").strip().lower()
    try:
        paquete = importlib.import_module(f"app.ligas.{slug}")
        formato = importlib.import_module(f"app.ligas.{slug}.formato")
    except ModuleNotFoundError as e:
        raise RuntimeError(
            f"La liga {slug!r} no existe: falta la carpeta app/ligas/{slug}/ "
            f"con __init__.py (LIGA) y formato.py"
        ) from e

    liga = paquete.LIGA
    # Estos valores cambian según el despliegue, no según la liga.
    url = os.environ.get("LIGA_URL_PUBLICA")
    if url:
        liga = replace(liga, url_publica=url.strip().rstrip("/"))
    return liga, formato


LIGA, FORMATO = _cargar()
