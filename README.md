# ⚽ Sistema de Información Deportiva para la Liga Interprovincial de Fútbol (LIF)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.1.1-black?logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Deployed_on-Render-46E3B7?logo=render&logoColor=white" />
  <img src="https://img.shields.io/badge/Estado-Activo-brightgreen" />
</p>

---

## 📋 Descripción general

La **Liga Interprovincial de Fútbol (LIF)** es una plataforma web full-stack desarrollada con Python y Flask que centraliza toda la información deportiva de una liga de fútbol amateur con múltiples divisiones y categorías.

### ¿Qué problema resuelve?

Las ligas de fútbol amateur gestionan una gran cantidad de información —jugadores, equipos, fixtures, resultados, estadísticas— que habitualmente se dispersa entre planillas de Excel, grupos de WhatsApp y archivos físicos. Esta plataforma concentra toda esa información en un sistema web accesible, actualizado en tiempo real.

### ¿A quién está dirigido?

| Actor | Rol en el sistema |
|---|---|
| **Administrador de la liga** | Gestión completa del sistema |
| **Periodistas deportivos** | Publicación de noticias y videos |
| **Hinchas y seguidores** | Consulta de fixture, posiciones y estadísticas |
| **Técnicos y dirigentes** | Consulta de planteles y resultados |

### Beneficios principales

- ✅ Información actualizada al instante tras cargar resultados.
- ✅ Tabla de posiciones calculada automáticamente.
- ✅ Notificaciones por correo electrónico al registrarse o al completarse una jornada.
- ✅ Carga masiva de jugadores mediante archivos Excel.
- ✅ Panel de administración dedicado por rol.
- ✅ Integración con Cloudinary para imágenes y n8n para automatizaciones.
- ✅ Desplegado en producción sobre Render.

---

## 🚀 Características principales

### 👥 Gestión de usuarios y autenticación
- Registro de usuarios públicos con envío automático de email de bienvenida.
- Login/logout con Flask-Login y sesiones seguras.
- Contraseñas hasheadas con Werkzeug (`generate_password_hash`).
- Tres roles diferenciados: `administrador`, `periodista`, `usuario`.
- Redirección automática al panel correspondiente según rol tras el login.
- Decorador personalizado `@role_required` para protección de rutas por rol.

### 🏟️ Gestión de clubes
- Alta de clubes con nombre y localidad.
- Carga de escudo del club con subida directa a **Cloudinary**.
- Visualización del plantel completo de cada club, organizado por categorías.

### ⚽ Gestión de equipos
- Creación de equipos por club y categoría.
- Categorías soportadas: Primera, Reserva, Quinta, Sexta, Séptima.
- Validación de duplicados (un club no puede tener dos equipos en la misma categoría).
- API JSON para consultar categorías disponibles por club.

### 🎽 Gestión de jugadores
- Alta de jugadores con número de carnet, nombre, apellido, fecha de nacimiento y club.
- Validación de carnet único a nivel global.
- Validación de duplicado por nombre dentro del mismo club.
- Asignación de jugadores a equipos (categorías) mediante tabla intermedia `JugadorEquipo`.
- **Carga masiva** de jugadores mediante importación de archivos **Excel** (`.xlsx`) con `pandas` y `openpyxl`.

### 🗞️ Gestión de periodistas
- El administrador puede crear cuentas de periodista desde el panel.
- Contraseña generada automáticamente de forma segura (`secrets`).
- Las credenciales se envían al periodista por correo electrónico.

### 📅 Gestión de temporadas y torneos
- Creación de temporadas anuales con activación/desactivación.
- Al crear una temporada se generan automáticamente los torneos **Apertura** y **Clausura**.
- Creación automática de las fases: Regular, Cuartos, Semifinal, Final y Finalísima.
- Las fases de Cuartos en adelante se configuran como ida y vuelta automáticamente.
- Solo una temporada y un torneo pueden estar activos simultáneamente.
- El administrador puede cambiar el torneo activo en cualquier momento.

### 📋 Gestión de fixtures

#### Mayores (Primera y Reserva)
- Generación automática de fixture con algoritmo de rotación round-robin.
- Carga manual de partidos individuales con selección de equipos y jornada.
- Control de jornadas ocupadas para evitar superposición de partidos.
- Vista previa del fixture generado antes de confirmar.

#### Inferiores (Quinta, Sexta y Séptima)
- Sistema idéntico al de mayores pero con gestión independiente.
- Vista previa del fixture generado para inferiores.

#### Playoffs
- Creación de partidos de playoff (Cuartos, Semifinal, Final, Finalísima).
- API para obtener los clubes clasificados según la tabla de posiciones.
- Soporte para partidos de ida y vuelta con cálculo del ganador global.
- Definición por penales: se registran goles de penal por separado.

### 📊 Registro de resultados y estadísticas
- Carga de resultados con detalle por jugador: goles, tarjetas amarillas y tarjetas rojas.
- Rutas separadas para cargar estadísticas de mayores e inferiores.
- API REST interna para cargar resultados de Primera y Reserva de forma independiente.
- Al completar una jornada, se evalúa automáticamente si todos los partidos están jugados y se envía una notificación por email a todos los usuarios registrados.

### 🏆 Tabla de posiciones
- Cálculo **en tiempo real** desde la base de datos (no se almacena en tabla física).
- Puntos, partidos jugados, ganados, empatados, perdidos, goles a favor, en contra y diferencia de gol.
- Ordenamiento por puntos → diferencia de gol → goles a favor.
- **Racha de forma**: últimos 5 resultados por equipo (G/E/P).
- Estadísticas destacadas: equipo más goleador, menos goleado y mejor diferencia.
- Proyección de cruces de playoff basada en las posiciones actuales.
- Notificación automática a **n8n** (webhook) al actualizar la tabla.

### ⚽ Goleadores y estadísticas
- Tabla de goleadores, amonestados y expulsados por categoría.
- Filtrado solo para la temporada activa.
- Estadísticas de equipo: equipo con más goles, más amarillas y más rojas.

### 📰 Gestión de noticias
- Creación de noticias con título, contenido, categoría e imagen.
- Imagen de noticia subida a **Cloudinary**.
- Generación automática de **slug** con `python-slugify`.
- Vista de detalle de noticia accesible por ID.
- Acceso a la gestión desde el panel del periodista y del administrador.

### 🎥 Gestión de videos
- Carga de videos de YouTube con título, descripción y número de jornada.
- Extracción automática del ID de video de YouTube en cualquier formato de URL (watch, short, embed).
- Visualización integrada mediante filtro Jinja2 `youtube_id`.

### 📧 Correos electrónicos automáticos
- **Bienvenida**: se envía al registrar un nuevo usuario.
- **Credenciales de periodista**: se envían al crear una cuenta de periodista.
- **Jornada cargada**: se envía a todos los usuarios cuando una jornada queda completa.
- Plantillas HTML personalizadas para cada tipo de email.
- Configurado sobre Gmail SMTP con TLS.

### 🤖 Automatizaciones con n8n
- Al recalcular la tabla de posiciones se dispara un webhook a **n8n** con la división actualizada, timestamp e URL de la tabla.
- Permite encadenar acciones externas como publicaciones en redes sociales, alertas, etc.

### 📥 Carga masiva mediante Excel
- Importación de jugadores desde archivo `.xlsx`.
- Procesamiento con `pandas` para validación y carga masiva.
- Ruta dedicada `/importar_jugadores_excel`.

### 🛡️ Panel administrativo
- Panel exclusivo para el rol `administrador`.
- Acceso a todos los módulos de carga: clubes, equipos, jugadores, fixture, resultados, noticias, videos y temporadas.
- Panel exclusivo para `periodista` con acceso solo a noticias y videos.

---

## 🏗️ Arquitectura del proyecto

El proyecto sigue el patrón **MVC (Modelo–Vista–Controlador)** adaptado al ecosistema Flask, organizado como una **Application Factory** mediante `create_app()`.

### Árbol de directorios

```
LIF/
├── run.py                          # Punto de entrada para desarrollo local
├── requirements.txt                # Dependencias del proyecto
├── convertir_utf8.py               # Utilidad para conversión de encoding
│
├── app/
│   ├── __init__.py                 # Application Factory (create_app)
│   ├── commands.py                 # Comandos CLI (crear admin)
│   │
│   ├── database/
│   │   └── db.py                   # Instancia SQLAlchemy
│   │
│   ├── models/
│   │   └── models.py               # Todos los modelos ORM (SQLAlchemy)
│   │
│   ├── routes/
│   │   └── views.py                # Blueprint principal con todas las rutas
│   │
│   ├── utils/
│   │   ├── admin.py                # Script de carga de datos iniciales
│   │   ├── email_utils.py          # Funciones de envío de email
│   │   ├── notificar_n8n.py        # Integración con n8n (webhooks)
│   │   └── playoff_utils.py        # Lógica de determinación de ganador
│   │
│   ├── static/
│   │   ├── escudos/                # Escudos locales (legacy)
│   │   └── uploads/noticias/       # Uploads locales (legacy)
│   │
│   └── templates/
│       ├── base.html               # Template base con navegación
│       ├── index.html              # Página principal pública
│       ├── login.html / register.html
│       ├── adminview.html          # Panel administrador
│       ├── panelperiodista.html    # Panel periodista
│       ├── fixture_general.html    # Vista de fixture
│       ├── tabla_posiciones.html   # Tabla de posiciones
│       ├── goleadores.html         # Estadísticas de goleadores
│       ├── noticias.html           # Listado de noticias
│       ├── videos.html             # Listado de videos
│       ├── club_plantel.html       # Plantel por club
│       ├── emails/                 # Plantillas HTML para emails
│       └── plantillasAdmin/        # Templates del panel de administración
│
├── migrations/                     # Migraciones Alembic (Flask-Migrate)
└── instance/                       # Configuración de instancia (ignorado en Git)
```

### Responsabilidades de cada componente

| Componente | Responsabilidad |
|---|---|
| `app/__init__.py` | Inicialización de la app, configuración, registro de extensiones y blueprints |
| `app/models/models.py` | Definición de todas las entidades de la base de datos |
| `app/routes/views.py` | Todas las rutas HTTP, lógica de negocio y renderizado de templates |
| `app/utils/email_utils.py` | Envío de correos transaccionales |
| `app/utils/playoff_utils.py` | Lógica pura para determinar ganadores de cruces |
| `app/utils/notificar_n8n.py` | Envío de webhooks al servidor de automatización n8n |
| `app/commands.py` | Comandos Flask CLI para tareas de administración |
| `migrations/` | Historial de cambios del esquema de base de datos |

---

## 🛠️ Tecnologías utilizadas

### Backend
| Tecnología | Uso |
|---|---|
| **Python 3.11+** | Lenguaje principal |
| **Flask 3.1.1** | Framework web |
| **Flask-SQLAlchemy** | ORM para mapeo objeto-relacional |
| **Flask-Migrate** | Gestión de migraciones de base de datos (Alembic) |
| **Flask-Login** | Manejo de sesiones y autenticación |
| **Flask-Mail** | Envío de correos electrónicos |
| **Werkzeug** | Hashing de contraseñas, utilidades HTTP |
| **Gunicorn** | Servidor WSGI para producción |
| **python-slugify** | Generación de slugs para noticias |
| **python-dotenv** | Gestión de variables de entorno |

### Base de datos
| Tecnología | Uso |
|---|---|
| **PostgreSQL** | Base de datos relacional principal |
| **psycopg2-binary** | Driver de conexión PostgreSQL para Python |

### Frontend
| Tecnología | Uso |
|---|---|
| **HTML5 + Jinja2** | Templates del servidor |
| **CSS3** | Estilos de la interfaz |
| **JavaScript** | Interactividad del cliente (fetch API, DOM) |

### Servicios externos e integraciones
| Servicio | Uso |
|---|---|
| **Cloudinary** | Almacenamiento de imágenes en la nube (escudos, noticias) |
| **Gmail SMTP** | Servidor de correo para emails transaccionales |
| **n8n** | Automatizaciones mediante webhooks |
| **Render** | Plataforma de despliegue en la nube |
| **YouTube** | Embed de videos mediante extracción de ID |

### Herramientas de desarrollo
| Herramienta | Uso |
|---|---|
| **Git** | Control de versiones |
| **pandas + openpyxl** | Procesamiento de archivos Excel |
| **Alembic** | Motor de migraciones de base de datos |

---

## 🗄️ Modelo de datos

El sistema cuenta con **10 entidades principales** con las siguientes relaciones:

```
Club ──────────< Equipo >──────────── JugadorEquipo >──── Jugador
  |                 |                                         |
  |                 |                                         |
  └── Jugadores     |                                 EstadoJugadorPartido
                    |                                         |
              Partido <─── Fase <─── Torneo <─── Temporada   |
                 |                                            |
                 └────────────────────────────────────────────┘
                        (estadisticas_jugadores)

Usuario ──< Noticia
        └──< Video
```

### Descripción de entidades

| Entidad | Descripción | Campos clave |
|---|---|---|
| **Club** | Institución deportiva | nombre, localidad, escudo_url |
| **Equipo** | Club + categoría | club_id, categoria |
| **Jugador** | Persona registrada en la liga | numero_carnet (PK), nombre, apellido, club_id |
| **JugadorEquipo** | Relación entre jugador y equipo (categoría) | numero_carnet, equipo_id |
| **Temporada** | Año deportivo | nombre (ej: "2026"), activa |
| **Torneo** | Apertura o Clausura dentro de una temporada | nombre, temporada_id, activo |
| **Fase** | Instancia del torneo (Regular, Cuartos, etc.) | nombre, orden, ida_vuelta, torneo_id |
| **Partido** | Enfrentamiento entre dos equipos | equipos, goles, jornada, jugado, penales |
| **EstadoJugadorPartido** | Estadísticas individuales por partido | goles, tarjetas_amarillas, tarjetas_rojas |
| **Usuario** | Cuenta de acceso al sistema | email, contraseña (hash), rol |
| **Noticia** | Artículo publicado | titulo, contenido, slug, imagen_url, autor |
| **Video** | Enlace a video de YouTube | url, titulo, jornada_jugada, autor |

---

## ⚙️ Instalación local

### Requisitos previos
- Python 3.11 o superior
- PostgreSQL instalado y en ejecución
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/suarezcaffdeveloper/LIF.git
cd LIF
```

### 2. Crear y activar el entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto con el siguiente contenido (ver sección de variables de entorno):

```bash
cp .env.example .env
# Editar .env con tus valores reales
```

### 5. Crear la base de datos

```sql
-- En psql o pgAdmin
CREATE DATABASE lif_db;
```

### 6. Ejecutar las migraciones

```bash
flask db upgrade
```

### 7. Crear el usuario administrador

```bash
flask create-admin
```

Esto crea un usuario con email `admin@liga.com` y contraseña `admin123`. **Cambiarla inmediatamente en producción.**

### 8. Ejecutar el servidor de desarrollo

```bash
python run.py
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

---

## 🔐 Variables de entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@localhost:5432/lif_db` |
| `SECRET_KEY` | Clave secreta de Flask para firmar sesiones | `una-clave-muy-larga-y-aleatoria` |
| `MAIL_USERNAME` | Cuenta de Gmail para envío de emails | `infoliga@gmail.com` |
| `MAIL_PASSWORD` | Contraseña de aplicación de Gmail | `abcd efgh ijkl mnop` |
| `MAIL_DEFAULT_SENDER` | Nombre y email del remitente | `Liga Interprovincial <info@liga.com>` |
| `CLOUDINARY_CLOUD_NAME` | Nombre del cloud en Cloudinary | `mi-cloud-name` |
| `CLOUDINARY_API_KEY` | API Key de Cloudinary | `123456789012345` |
| `CLOUDINARY_API_SECRET` | API Secret de Cloudinary | `aBcDeFgHiJkLmNoPqRsTuVwXyZ` |

> ⚠️ Nunca subir el archivo `.env` al repositorio. Agregarlo al `.gitignore`.

---

## 📖 Flujo de uso

### 1. Configuración inicial (Administrador)
1. Ingresar al panel de administración en `/adminview`.
2. Crear los **clubes** participantes desde `/cargar_clubes`.
3. Crear los **equipos** de cada club por categoría desde `/cargar_equipos`.
4. Registrar los **jugadores** manualmente desde `/cargar_jugadores` o de forma masiva desde `/importar_jugadores_excel`.
5. Asignar jugadores a sus categorías desde `/asignar_jugador_categoria`.

### 2. Apertura de temporada
1. Ir a `/admin/temporadas` y crear una nueva temporada (ej: "2026").
2. El sistema crea automáticamente los torneos **Apertura** y **Clausura** con sus fases.
3. Activar el torneo que se jugará primero.

### 3. Generación del fixture
1. Ir a `/cargar_fixture_mayores` o `/cargar_fixture_inferiores`.
2. Seleccionar la categoría y usar la generación automática de fixture.
3. Revisar la vista previa y confirmar.

### 4. Carga de resultados
1. Ir a `/cargar_estadisticas_mayores` o `/cargar_estadisticas_inferiores`.
2. Seleccionar la jornada y el partido.
3. Ingresar goles, tarjetas amarillas y rojas por jugador.
4. Al completar todos los partidos de la jornada, se envía email automáticamente a los usuarios.

### 5. Consulta pública
Los visitantes pueden consultar sin registrarse:
- **Fixture**: `/fixture/mayores` o `/fixture/inferiores`
- **Tabla de posiciones**: `/tabla_posiciones/primera`, `/tabla_posiciones/reserva`, etc.
- **Goleadores**: `/goleadores/primera`
- **Noticias**: `/noticias`
- **Videos**: `/videos`
- **Plantel de club**: `/club/<id>`

### 6. Publicación de contenido (Periodista)
1. Ingresar al panel desde `/panel_periodista`.
2. Publicar noticias desde `/cargar_noticia` con imagen.
3. Cargar videos desde `/cargar_video` con URL de YouTube.

---

## 🔒 Seguridad

### Autenticación
- Contraseñas almacenadas como hash con **PBKDF2** (Werkzeug).
- Sesiones manejadas con **Flask-Login** y cookie firmada con `SECRET_KEY`.
- Protección de rutas privadas con el decorador `@login_required`.

### Control de acceso por rol
| Rol | Acceso |
|---|---|
| `usuario` | Consulta pública del sitio |
| `periodista` | Panel propio + publicación de noticias y videos |
| `administrador` | Acceso completo al sistema |

- Verificación de rol en rutas sensibles con el decorador personalizado `@role_required(*roles)`.
- El rol del usuario se fija en `"usuario"` en el backend al registrarse, sin importar lo que envíe el formulario.
- Los periodistas solo son creados por el administrador desde el panel.

### Otras protecciones
- Contraseñas de periodistas generadas automáticamente con `secrets.choice` (no predecibles).
- URLs de Cloudinary para imágenes (no se expone el sistema de archivos del servidor).
- Variables sensibles gestionadas con `.env` y nunca incluidas en el código fuente.

---

## 📸 Capturas sugeridas

Para mostrar el proyecto en GitHub, se recomienda capturar las siguientes pantallas:

| N° | Pantalla | URL |
|---|---|---|
| 1 | **Página de inicio** con clubes, últimas noticias y videos | `/` |
| 2 | **Fixture de mayores** organizado por jornadas con goleadores | `/fixture/mayores` |
| 3 | **Tabla de posiciones** con racha de forma y estadísticas | `/tabla_posiciones/primera` |
| 4 | **Goleadores** con tabla de goles, amarillas y rojas | `/goleadores/primera` |
| 5 | **Plantel de un club** organizado por categorías | `/club/<id>` |
| 6 | **Panel de administración** con menú de módulos | `/adminview` |
| 7 | **Carga de jugadores** con validaciones en tiempo real | `/cargar_jugadores` |
| 8 | **Administración de temporadas** con torneos y fases | `/admin/temporadas` |
| 9 | **Sección de noticias** con imagen y detalle | `/noticias` |
| 10 | **Panel del periodista** | `/panel_periodista` |

---

## 🧠 Aprendizajes del proyecto

Este proyecto demuestra dominio práctico de un stack Backend completo en Python:

### Desarrollo Backend con Python y Flask
- Diseño de aplicaciones con **Application Factory pattern** (`create_app()`).
- Registro de **Blueprints** para modularización de rutas.
- Manejo del ciclo request–response, redirecciones, mensajes flash y renderizado de templates.
- Desarrollo de una **API REST interna** con endpoints JSON para comunicación asincrónica (AJAX).
- Comandos CLI personalizados con **Click**.

### Base de datos y ORM
- Diseño de un esquema relacional normalizado con **10+ tablas** y relaciones complejas (one-to-many, many-to-many).
- Uso avanzado de **SQLAlchemy**: `joinedload`, `outerjoin`, constraints únicos, `func`, `or_`, `and_`.
- Gestión del ciclo de vida de las migraciones con **Flask-Migrate / Alembic**.
- Cálculos en memoria (tabla de posiciones, rachas) evitando redundancia de datos.

### Diseño de sistema y lógica de negocio
- Implementación de algoritmo de **generación automática de fixture** (round-robin).
- Lógica de **playoffs** con sistema de ida y vuelta y definición por penales.
- Sistema de **temporadas activas** con propagación de estado.

### Autenticación y autorización
- Autenticación con **Flask-Login** y hashing seguro de contraseñas.
- Control de acceso basado en roles con decorador personalizado.
- Generación segura de contraseñas con el módulo `secrets`.

### Integraciones externas
- Subida de imágenes a **Cloudinary** desde el backend.
- Envío de correos transaccionales con **Flask-Mail** y plantillas HTML.
- Webhooks a **n8n** para automatización de tareas externas.
- Procesamiento de archivos **Excel** con `pandas` y `openpyxl`.

### Despliegue
- Configuración de la aplicación para producción con **Gunicorn**.
- Despliegue sobre la plataforma **Render** con variables de entorno seguras.
- Manejo de la URL de PostgreSQL en formato legacy (`postgres://` → `postgresql://`).

---

## 🔭 Futuras mejoras

Mejoras coherentes identificadas a partir del análisis del proyecto actual:

| Mejora | Descripción |
|---|---|
| **API REST pública** | Exponer endpoints documentados para consumir datos desde apps móviles |
| **Panel de estadísticas avanzado** | Gráficos históricos por temporada, comparativa entre torneos |
| **Búsqueda de jugadores** | Buscador global por nombre/carnet con resultados en tiempo real |
| **Notificaciones push / Telegram** | Alertas de resultados vía bot de Telegram usando n8n |
| **Edición de resultados** | Corrección de resultados ya cargados con log de auditoría |
| **Autenticación 2FA** | Segundo factor de autenticación para el rol administrador |
| **Tests automatizados** | Suite de pruebas unitarias e de integración con `pytest` |
| **Paginación** | Paginación en noticias, videos y listados largos |
| **Exportación de datos** | Exportar tabla de posiciones y goleadores a PDF o Excel |
| **Gestión de sanciones** | Módulo para registrar suspensiones por acumulación de tarjetas |

---

## 👤 Autor

**Santiago Suárez**

Desarrollador Backend Python | Flask · PostgreSQL · SQLAlchemy

| Red | Enlace |
|---|---|
| 💼 LinkedIn | [Tu perfil de LinkedIn] |
| 🐙 GitHub | [github.com/suarezcaffdeveloper](https://github.com/suarezcaffdeveloper) |

---

<p align="center">
  Desarrollado con ❤️ y Python 🐍
</p>
