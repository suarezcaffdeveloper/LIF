# Temas de ElTablón

Un tema es solo HTML, CSS y JS sobre un contrato de datos fijo. Crear uno no requiere tocar Python.

## Estructura

```
app/themes/<slug>/
  theme.json      nombre, descripcion, modo ("claro" u "oscuro"), portada (true si el inicio
                  muestra fixture, tabla y goleadores; ver "portada" más abajo)
  templates/      páginas que el tema redefine (las que falten se toman de "clasico")
  static/         CSS, JS e imágenes, servidos en /tema/...
```

Orden de búsqueda de un template: tema activo → `clasico` → `app/templates/` (admin, periodista y emails, que no cambian con el tema).

Para usar un tema: variable de entorno `TEMA=<slug>`, o `tema="<slug>"` en la `Liga` (`app/ligas/<liga>/__init__.py`). Un estático del tema se referencia con `url_for('tema.static', filename='css/tema.css')`.

## Variables disponibles en todas las páginas

| Variable | Contenido |
|---|---|
| `liga` | Marca y configuración de la liga (ver abajo) |
| `producto` | Nombre de la plataforma ("ElTablón") |
| `anio` | Año actual |
| `tema` | Metadato del tema activo: `slug`, `nombre`, `descripcion`, `modo` |
| `demo_mode` | `True` si la sesión está en la base demo |
| `current_user` | Usuario de Flask-Login (`is_authenticated`, `rol`, ...) |

`liga`: `nombre`, `nombre_corto`, `hero_lineas` (3 textos), `descripcion`, `logo` (ruta en `static/`), `url_publica`, colores (`acento`, `acento_dim`, `fondo`, `panel`, `panel_2`, `texto`, `texto_dim`), `categorias` (objetos con `slug`, `etiqueta`, `etiqueta_larga`, `bloque`, `parametro_url`), `bloques_categorias` (`{bloque: [categorias]}`) y `resaltar_letra`.

Los colores de la liga son la base de la marca. Un tema debería usarlos (`{{ liga.acento }}`) en vez de fijar colores propios, salvo que su identidad lo exija.

## Páginas y sus datos

| Template | Ruta | Variables |
|---|---|---|
| `base.html` | (herencia) | bloques `title`, `extra_styles`, `content` |
| `index.html` | `/` | `clubes`, `noticias` (3 últimas), `videos` (3 últimos) |
| `club_plantel.html` | `/club/<id>` | `club`, `planteles` (`{slug: {label, jugadores}}`), `categorias` (lista de slugs) |
| `fixture_general.html` | `/fixture/<bloque>[/<categoria>]` | `fechas_partidos`, `titulo`, `mostrar_resultados` |
| `tabla_posiciones.html` | `/tabla_posiciones/<categoria>` | `tabla`, `categoria`, `stats`, `rachas`, `cruces` |
| `goleadores.html` | `/goleadores/<categoria>` | `categoria`, `goles`, `amarillas`, `rojas`, `stats` |
| `noticias.html` | `/noticias` | `noticias` |
| `noticia_detalle.html` | `/noticia/<id>` | `noticia` |
| `videos.html` | `/videos` | `videos` |
| `login.html` | `/login` | (solo las globales) |
| `register.html` | `/register` | (solo las globales) |

Para el detalle de los campos de `club`, `noticia`, `video` y `partido`, ver `app/models/models.py`.

## Portada (resumen para el inicio)

Si el `theme.json` tiene `"portada": true`, `index.html` recibe además `portada` con `categorias` y `proximo`:

- `portada.categorias`: una entrada por categoría de la liga, con `categoria` (objeto Categoria), `jornada` (la última con resultados o, si no hay, la primera), `partidos` (fase regular de esa jornada), `tabla` (lista de dicts, igual que en la página de posiciones) y `goleadores` (hasta 6 filas con `nombre`, `apellido`, `club_nombre` y `total`).
- `portada.proximo`: el partido pendiente más cercano de toda la liga, o `None`.
- Variable global `clasificados`: cuántos equipos de la tabla pasan a la fase final (definido en el `formato.py` de la liga).

Los temas que no lo piden reciben `portada = None` y no pagan las consultas extra.

## Temas incluidos

| Tema | Modo | Idea |
|---|---|---|
| `clasico` | oscuro | Diseño original. Es el tema base: lo que otro tema no define se toma de acá. |
| `cancha` | claro | Editorial y pensado para celular. Sigla gigante con césped en movimiento, nav flotante que se oscurece al scrollear, barra de navegación inferior en el celular. |
| `reflectores` | oscuro | Estadio nocturno. Reflectores que oscilan, cancha que se dibuja al cargar, nav de vidrio que se esconde al bajar, sliders que se arrastran y contadores animados. |
| `marcador` | oscuro | Tablero de estadio. Inicio con el marcador electrónico (cuenta regresiva en dígitos LED de matriz de puntos), barra lateral de íconos en escritorio y pestañas fijas en celular, goleadores como gráfico de barras y puntos como barra LED. |
| `cuaderno` | claro | Cuaderno del técnico. Papel cuadriculado y tinta con tiza roja, pizarra táctica en el inicio con fichas de escudos que se arrastran y una flecha que las sigue, listas con renglones y margen, goleadores en columnas rayadas, tipografía serif y anotaciones a mano. |
| `nocturno` | oscuro | Neón nocturno premium. Tipografía enorme con mucho aire, acento neón que respira en elementos clave, nav y dock de cristal esmerilado, secciones que aparecen con fade-up al scrollear y estados de goles con brillo. |
| `tribuna` | claro | Estadio de día. Héroe con los hinchas haciendo la ola y banderines, partidos como entradas con código de barras, cinta de resultados, tipografía de camiseta y acento ultramar. |

`tribuna` toma su ultramar de `color_marca` y el amarillo de la ola de `color_marca_2` (defaults: ultramar y amarillo).

`nocturno` toma su neón de `color_marca` (lima por defecto).

`cuaderno` toma su color de tiza de `color_marca` (rojo por defecto).

`marcador` toma su color LED de `color_marca` (ámbar por defecto).

`reflectores` toma su acento de `color_marca` (azul por defecto). Además de lo que usa `cancha`, el inicio le pide a `portada` los `totales` (`partidos` jugados y `goles`) para los contadores.

`cancha` deriva su paleta de dos colores opcionales de la liga: `color_marca` (verde por defecto) y `color_marca_2` (naranja por defecto). Se definen en `app/ligas/<liga>/__init__.py`.

### Ocultar un tema

Con `"visible": false` en su `theme.json`, un tema no aparece en el selector de la demo ni se puede elegir con `?tema=`. Sigue instalado: los otros temas toman de `clasico` las páginas que no definen. Hoy `clasico` está oculto.

## Modo escaparate (demo pública)

Con `DEMO_TEMAS=1` cada visita elige el diseño y el color de marca, y la elección queda en la sesión y en los enlaces:

- `?tema=cancha` (o `reflectores`, `clasico`) cambia el diseño.
- `?marca=%23e2731f` reemplaza el color de marca (`color_marca` y `acento` de la liga) solo para esa visita; `?marca=auto` la quita.
- `?embed=1` oculta el selector flotante, para incrustar la demo en un iframe.
- El selector flotante (`app/templates/_selector_tema.html`) lo incluye cada `base.html` con `{% include "_selector_tema.html" ignore missing %}`. Un tema nuevo tiene que sumar esa línea para aparecer con la misma barra.

Detalles de implementación (`app/temas.py`): cada tema tiene su propio entorno Jinja (así no se mezclan las plantillas compiladas), `/tema/...` sirve el estático del tema de la visita, y el nombre de los archivos estáticos de cada tema no debe repetirse (`cancha.css`, `reflectores.css`). Sin `DEMO_TEMAS` nada de esto está activo.

Los enlaces de un tema deben armarse con `url_for(...)`, no con rutas escritas a mano, para que lleven la elección de la visita.

## Reglas para un tema nuevo

- Empezar con `base.html` e `index.html`. El resto puede heredar de `clasico`.
- Si el tema define su propio `base.html`, las páginas de `clasico` que hereden de él tienen que encajar con sus bloques (`title`, `extra_styles`, `content`), o el tema debe redefinir esas páginas.
- No fijar nombres, logos ni textos de una liga: usar `liga.*`.
- Que se vea bien en celular (ancho de 360 px) y respete `prefers-reduced-motion`.
