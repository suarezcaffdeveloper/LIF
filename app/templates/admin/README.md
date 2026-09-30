# Panel de administración de ElTablón

Un solo diseño para todas las ligas, independiente del tema público. Claro y oscuro son el mismo diseño con los colores invertidos: cada persona elige desde la barra superior (Automático, Claro u Oscuro) y la elección queda en una cookie del navegador (`admin_tema`, un año).

## Piezas

| Archivo | Para qué |
|---|---|
| `app/templates/admin/base_admin.html` | Marco: barra lateral por rol, barra superior con el conmutador, banner de modo demo, íconos y avisos |
| `app/static/admin/admin.css` | Tokens de color, tipografía y componentes compartidos (prefijo `ad-`) |
| `app/static/admin/admin.js` | Conmutador de tema, cajón del menú en celular y la API de avisos |
| `app/static/admin/estadisticas.css` | Estilos de las dos pantallas de estadísticas (solo dentro de `.est`) |
| `app/__init__.py` | Context processor `tema_admin`: lee la cookie y la escribe en `<html data-tema>` sin parpadeo |

El menú lateral está en `base_admin.html`. El administrador ve todo; el periodista solo Noticias y Videos.

## Armar una pantalla nueva

```jinja
{% extends "admin/base_admin.html" %}
{% block title %}Cargar algo{% endblock %}
{% block page_title %}Cargar algo{% endblock %}
{% block page_sub %}Una línea que explica qué se hace acá.{% endblock %}

{% block content %}
<div class="ad-card ad-card-form">
  <form class="ad-form" method="POST" action="{{ url_for('views.mi_ruta') }}">
    <div class="ad-field">
      <label for="nombre">Nombre</label>
      <input type="text" id="nombre" name="nombre" required>
    </div>
    <div class="ad-form-acciones">
      <button type="submit" class="ad-btn ad-btn-primario">Guardar</button>
    </div>
  </form>
</div>
{% endblock %}
```

Bloques disponibles: `title`, `page_title`, `page_sub`, `page_actions` (botones a la derecha del título), `extra_head` (CSS propio de la pantalla) y `scripts`.

La ruta tiene que usar `@admin_required` (o `@login_required` con `role_required` si también entran periodistas). Para sumarla al menú, agregá una línea `item(...)` en `base_admin.html` con un ícono del sprite.

## Componentes

- **Estructura:** `ad-card`, `ad-card-head`, `ad-grid` (`c-3`, `c-4`, `c-6`, `c-8`), `ad-cols-2`, `ad-cols-3`, `ad-stack`, `ad-row`.
- **Formularios:** `ad-form` da estilo a los `input`, `select` y `textarea` de adentro; `ad-field` agrupa etiqueta y campo; `ad-hint` es la ayuda; `ad-check` y `ad-switch` para casillas e interruptores; `ad-form-acciones` para los botones al pie.
- **Botones:** `ad-btn`, `ad-btn-primario` (amarillo), `ad-btn-peligro`, `ad-btn-fantasma`, `ad-btn-sm`, `ad-btn-block`.
- **Datos:** `ad-tabla-wrap` + `ad-tabla`, `ad-badge` (`-ok`, `-warn`, `-danger`, `-info`), `ad-tabs`, `ad-chip`.
- **Estados:** `ad-vacio` (nada para mostrar), `ad-spinner`, `ad-modal-fondo` + `ad-modal`.
- **Inicio:** `ad-estado` + `ad-dato`, `ad-accesos` + `ad-acceso`.

## Colores

Usá siempre las variables, nunca colores fijos, para que el modo claro y el oscuro funcionen solos: `--bg`, `--surface`, `--surface-2`, `--surface-3`, `--line`, `--text`, `--muted`, `--acento` (amarillo banderín, con `--acento-ink` para el texto encima), `--ok`, `--danger`, `--warn`, `--info` y sus versiones `-bg`. Si necesitás un componente nuevo y de uso general, agregalo a `admin.css`; si es solo de esa pantalla, va en su `extra_head`.

## Avisos

Un solo mecanismo. Desde Python, `flash("texto", "success" | "danger" | "warning" | "info")` y aparece al cargar la página. Desde JavaScript:

```js
ElTablonAdmin.aviso('success', 'Guardado');           // ok, danger, warn, info
ElTablonAdmin.confirmar({ titulo: '¿Borrar?', texto: '...', peligro: true }).then(si => { ... });
```

`mostrarFlash(mensaje, tipo)` y `showFlash(mensaje, tipo)` siguen existiendo como atajos para el JavaScript viejo. No definas funciones con ese nombre en la pantalla: pisarían a las del panel. SweetAlert2 (estadísticas y playoff) toma sus colores de las mismas variables.

## Reglas para no romper nada

Varias pantallas (estadísticas, fixtures, playoff, asignar jugador) generan HTML desde JavaScript y leen `id`, `name`, clases y `data-*` concretos. Al retocarlas:

1. No renombres ni quites ningún `id`, `name`, `data-*` ni las clases que el script consulta (`.list-row`, `.tarjeta-player`, `.tarjeta-tipo`, `.cruce-card`, `.jornada-card`, `.card-in`, etc.). Cambiá solo su aspecto en el CSS.
2. No pongas colores fijos en el JavaScript que arma HTML; usá clases.
3. Comprobá siempre en claro, en oscuro y a 390 px de ancho.

## Conocido y pendiente

- Cinco rutas siguen apuntando a plantillas que no existen (`cargar_parametros`, `ver_partidos_playoff` y `ver_partidos_playoff_inferiores`, `chequeo_resultado` y `chequeo_resultado_inferiores`). Son anteriores al rediseño.
- Algunos textos que arma el JavaScript conservan emojis (listas vacías, tipos de tarjeta).
- `cargar_equipos` y algunas pantallas de estadísticas tienen las categorías escritas a mano para una liga; hoy no salen de la configuración.
