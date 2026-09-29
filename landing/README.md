# Landing de ElTablón

Sitio estático (HTML, CSS y JS): no necesita servidor ni instalación. Es la página principal de ElTablón; la demo en vivo es una instancia aparte de la app.

## Ver en local

```
python -m http.server 5070 --directory landing
```

Y abrir http://127.0.0.1:5070. Ojo: Chrome bloquea el puerto 5060, no lo uses.

## Antes de publicar: completar los datos

Todo lo que hay que cambiar está en `js/config.js`. **Hoy tiene valores de ejemplo** y la consola del navegador lo avisa mientras `EJEMPLO` sea `true`.

| Dato | Para qué se usa |
|---|---|
| `WHATSAPP` y `WHATSAPP_MENSAJE` | Todos los botones "WhatsApp" y "Consultá" |
| `EMAIL` | El botón "Enviar un email" y el respaldo del formulario |
| `FORM_ENDPOINT` | Servicio que recibe el formulario (por ejemplo Formspree). Vacío: abre el correo del visitante con el mensaje escrito |
| `DEMO_URL` y `DEMO_EN_VIVO` | Con `DEMO_EN_VIVO: true` la sección "Elegí cómo se ve tu liga" incrusta la demo real; en `false` muestra capturas |

Al terminar, poné `EJEMPLO: false`.

## Publicar en Vercel (o cualquier hosting estático)

1. Crear un proyecto nuevo apuntando a la carpeta `landing/` como raíz.
2. Sin comando de build. `vercel.json` ya activa las URL limpias y el caché de las imágenes.
3. Conectar el dominio.

## Publicar la demo en vivo

La demo es la misma app con la liga ficticia. En un servicio aparte (por ejemplo Render), con su propia base de datos:

| Variable | Valor |
|---|---|
| `LIGA` | `demo` |
| `DEMO_TEMAS` | `1` (habilita `?tema=`, `?marca=` y el selector de diseño) |
| `DATABASE_URL` | Base de datos **exclusiva de la demo**, nunca la de una liga real |
| `DEMO_DATABASE_URL` | Otra base para la sesión de demo (o vacía para usar SQLite local) |
| `SECRET_KEY` | Una clave larga y propia |
| `LIGA_URL_PUBLICA` | Dirección pública de la demo |

Después, una sola vez y luego cada día (tarea programada), para que las fechas de los partidos sigan siendo "de hoy":

```
flask seed-liga-demo --yes
flask reset-demo-db
```

`seed-liga-demo` se niega a correr si `LIGA` no es `demo`, para no borrar datos de una liga real. En la demo no se envían mails ni se suben archivos.

## Imágenes

Están en `assets/img/` y salen de la demo real: capturas de los diseños (escritorio y celular), variantes de color, paneles de administrador y periodista, y las imágenes de Instagram que genera el sistema. Si cambia un diseño, hay que volver a capturarlas (ver la carpeta `app/themes/README.md`, sección "Modo escaparate", para elegir diseño y color por URL).

### Sumar o actualizar un diseño en la landing

Con un solo comando (desde la raíz del proyecto) se generan las siete imágenes de un diseño con la liga demo, sin tocar ninguna base real:

```
venv\Scripts\python.exe landing\herramientas\capturar_diseno.py cuaderno
```

Después hay que agregar el diseño en `index.html` (una imagen más en el notebook y en el celular del hero, y un botón en la sección "Elegí cómo se ve tu liga") y su nombre en la lista `nombres` de `js/landing.js`. Hoy la landing muestra Cancha, Reflectores y Cuaderno; Marcador y Clásico quedaron afuera a propósito.

## Lo que la landing promete (y lo que no)

Solo dice lo que el sistema hace hoy. En particular: **prepara** las imágenes para Instagram pero no las publica, y no menciona integraciones que no están conectadas.
