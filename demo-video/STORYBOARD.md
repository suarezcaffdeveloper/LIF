---
format: 1920x1080
duration: 71.5s
message: "Con LIF, tu liga publica posiciones, goleadores, fixture y noticias en minutos — sin depender de un programador."
arc: Hook → Valor → Evidencia (tour público) → Roles (periodista + admin) → Funcionalidades admin (fixture, jugadores, estadísticas) → CTA
audience: dirigentes y administradores de ligas de fútbol evaluando sumarse
mode: collaborative
---

## Frame 1 — Hook

- status: animated
- duration: 6s
- transition_in: cut
- scene: Tipografía pura, sin captura — la frase de apertura arma y remata
- src: compositions/frames/01-hook.html
- role: hook
- blueprint: kinetic-type-beats
- clip: (ninguno — solo texto animado)
- onscreen_text: "Actualizar tu liga / no debería tardar días."

Fondo `--bg` liso, dos beats de tipografía a pantalla completa (kinetic-type-beats):
beat A "Actualizar tu liga" entra, se sostiene un instante; beat B "no debería
tardar días." lo reemplaza en el mismo centro con un spring-pop recortado. No
hay producto todavía — es la promesa, en el lenguaje del dolor del usuario, no
en vocabulario de features.

## Frame 2 — La promesa

- status: animated
- duration: 8.2s
- transition_in: blur-crossfade (0.5s, desde el frame 1)
- scene: Home pública de LIF, Ken Burns lento sobre la captura real
- src: compositions/frames/02-home.html
- role: product_intro
- blueprint: cursor-ui-demo
- clip: assets/02-home.mp4 (real — subido por el usuario como videos/PanelPrincipal.mp4)
- onscreen_text: "Con LIF, lo hacés en minutos."

Primer contacto con el producto real. Captura a pantalla completa (object-fit
cover) con un push lento (scale 1→1.035) y un scrim inferior para que el chip
"PÚBLICO" y el subtítulo lean bien. Entra desde el Frame 1 con una blur
crossfade calma (0.5s) — la promesa tipográfica se disuelve en el producto
real. El mensaje central de la pieza aterriza acá, en el segundo beat — todo
lo que sigue es evidencia de esta frase.

## Frame 3 — Posiciones

- status: animated
- duration: 3.9s
- transition_in: push-slide (0.5s, desde el frame 2)
- scene: Tabla de posiciones — captura real
- src: compositions/frames/03-posiciones.html
- role: feature_showcase
- blueprint: device-surface-showcase
- clip: assets/03-tabla-posiciones.mp4 (real — subido por el usuario como videos/TablaPosiciones.mp4)
- onscreen_text: "Posiciones actualizadas, por categoría."

Entra con un push slide horizontal (0.5s, todo el frame se desplaza 1920px)
— se nota literalmente que "cambia de panel". Mismo tratamiento visual que
los frames 4–6: captura a pantalla completa, Ken Burns lento, chip
"PÚBLICO", subtítulo anclado al tercio inferior con línea celeste.

## Frame 4 — Goleadores

- status: animated
- duration: 5s
- transition_in: whip-pan CSS (0.3s, desde el frame 3)
- scene: Goleadores y tarjetas por categoría — captura real
- src: compositions/frames/04-goleadores.html
- role: feature_showcase
- blueprint: device-surface-showcase
- clip: assets/04-goleadores.mp4 (real — subido por el usuario como videos/TablaGoleadores.mp4)
- onscreen_text: "Goleadores y tarjetas, siempre al día."

Entra con un whip-pan (pan lateral + motion blur, 0.3s) en vez de push
slide — más nervioso, corta distinto al frame anterior.

## Frame 5 — Fixture

- status: animated
- duration: 5s
- transition_in: focus-pull (0.5s, desde el frame 4)
- scene: Fixture general de la temporada — captura real
- src: compositions/frames/05-fixture.html
- role: feature_showcase
- blueprint: device-surface-showcase
- clip: assets/05-fixture.mp4 (real — subido por el usuario como videos/FixtureGeneral.mp4)
- onscreen_text: "Todo el fixture de la temporada."

Entra con un focus pull (el frame anterior se desenfoca y se va, éste llega
nítido) — cuarta transición distinta hasta ahora.

## Frame 6 — Noticias y videos

- status: animated
- duration: 8s
- transition_in: elastic-push (0.7s, desde el frame 5)
- scene: Noticias y videos de la liga — captura real
- src: compositions/frames/06-noticias-videos.html
- role: feature_showcase
- blueprint: device-surface-showcase
- clip: assets/06-noticias-videos.mp4 (real — subido por el usuario como videos/VideosYNoticias.mp4)
- onscreen_text: "Noticias y videos, en un mismo lugar."

Cierra el bloque de evidencia pública (tour del rol usuario/público). Entra
con un push con rebote elástico (overshoot en el entrante) — quinta
transición distinta, más juguetona que las anteriores, marca el final del
tour antes del quiebre de tema hacia los roles con panel.

## Frame 7 — "Gestioná la información con estos roles"

- status: animated
- duration: 3.5s
- transition_in: squeeze (0.5s, desde el frame 6)
- scene: Cartelón tipográfico, sin captura
- src: compositions/frames/07-roles.html
- role: product_intro
- blueprint: titlecard-reveal
- clip: (ninguno — solo texto animado)
- onscreen_text: "Gestioná la información con estos roles."

Respiro entre el tour público y los paneles con rol. Ya no se cuentan "3
tipos de usuario" ni se muestra el login — el público ya vio todo lo que ve
el rol usuario en los frames 2–6, así que repetirlo sería redundante. Esta
escena solo abre paso a los dos roles con panel que siguen (periodista y
administrador). Entra con un squeeze (el tour se comprime, el cartel se
expande desde el lado opuesto) — sexta transición distinta.

## Frame 8 — Periodista

- status: animated
- duration: 7.1s
- transition_in: crossfade (0.5s, desde el frame 7)
- scene: Panel de periodista cargando una noticia — captura real, pantallazo de la funcionalidad
- src: compositions/frames/08-periodista.html
- role: feature_showcase
- blueprint: cursor-ui-demo
- clip: assets/08-periodista.mp4 (real — subido por el usuario como videos/VistaPeriodista.mp4)
- onscreen_text: "El periodista carga sus propias noticias —"

Chip de rol "PERIODISTA" arriba del video (mono, celeste), subtítulo debajo
del video. No es el flujo completo, es un pantallazo — alcanza para mostrar
que el rol existe y qué puede hacer. El subtítulo queda abierto ("—") para
resolverse en el frame siguiente. Séptima transición distinta (crossfade
simple, calma, del cartel al primer panel con rol).

## Frame 9 — Administrador

- status: animated
- duration: 4.8s
- transition_in: zoom-through (0.4s, desde el frame 8)
- scene: Panel de administrador — captura real, pantallazo de varias acciones
- src: compositions/frames/09-admin.html
- role: feature_showcase
- blueprint: cursor-ui-demo
- clip: assets/09-admin.mp4 (real — subido por el usuario como videos/PanelPeriodista.mp4)
- onscreen_text: "— y el administrador, todo lo demás."

Mismo tratamiento que el resto de los paneles con rol: chip "ADMINISTRADOR"
arriba del video, subtítulo debajo, Ken Burns lento. Continúa la frase que
dejó abierta el Frame 8 ("El periodista carga sus propias noticias —"). Entra
con un zoom through (el periodista queda atrás y se desenfoca, el admin
entra de frente) — octava transición distinta, la más marcada de la pieza,
reservada para el último rol antes del cierre.

## Frame 10 — Fixture / sorteo

- status: animated
- duration: 9.2s
- transition_in: circle-iris (0.5s, desde el frame 9)
- scene: Panel de admin — carga de fixture, captura real
- src: compositions/frames/10-fixture-sorteo.html
- role: feature_showcase
- blueprint: cursor-ui-demo
- clip: assets/10-fixture-sorteo.mp4 (real — subido por el usuario como videos/SorteoFixture.mp4)
- onscreen_text: "Cargá el fixture a mano, o generalo solo por sorteo."

Primera de tres funcionalidades puntuales del admin, después del panel
general. Mismo chip "ADMINISTRADOR" arriba, subtítulo debajo. Entra con un
circle iris (un círculo se abre desde el centro) — como "entrando en detalle"
del panel general que se vio en el Frame 9. Novena transición distinta.

## Frame 11 — Jugadores

- status: animated
- duration: 3.8s
- transition_in: vertical-push (0.5s, desde el frame 10)
- scene: Panel de admin — carga de jugadores, captura real
- src: compositions/frames/11-jugadores.html
- role: feature_showcase
- blueprint: cursor-ui-demo
- clip: assets/11-jugadores.mp4 (real — subido por el usuario como videos/CargaJugadores.mp4)
- onscreen_text: "Jugadores uno por uno, o toda la planilla desde Excel."

Segunda funcionalidad. Entra con un push vertical (eje distinto a los push
horizontales ya usados en el tour público) — décima transición distinta.

## Frame 12 — Estadísticas

- status: animated
- duration: 5.4s
- transition_in: color-dip (0.5s, desde el frame 11)
- scene: Panel de admin — carga de estadísticas, captura real
- src: compositions/frames/12-estadisticas.html
- role: feature_showcase
- blueprint: cursor-ui-demo
- clip: assets/12-estadisticas.mp4 (real — subido por el usuario como videos/CargaEstadisticas.mp4)
- onscreen_text: "Y las estadísticas de cada partido, cargadas en minutos."

Tercera y última funcionalidad puntual antes del cierre. Entra con un color
dip (corte limpio a color de fondo y sube el nuevo video) — se cambió desde
un diamond iris porque ese clip-path dejaba las 4 esquinas del video
recortadas durante toda la escena, no solo en la transición.

## Frame 13 — Cierre

- status: animated
- duration: 8s
- transition_in: blur-crossfade (0.6s, desde el frame 12 — wind-down calmo, mismo lenguaje que 1→2)
- scene: Cartelón de cierre con CTA, sin captura
- src: compositions/frames/13-cierre.html
- role: cta
- blueprint: titlecard-reveal
- clip: (ninguno — solo texto animado)
- onscreen_text: "Así de simple es llevar tu liga a otro nivel. / Escribinos para sumar tu liga."

Cadena de 3 cards tipográficas (statement → CTA → wordmark), sin isotipo (no
hay archivo de logo): remata en el nombre "LIF" a modo de lockup tipográfico
sobre `--bg`, con el motivo de cancha del Frame 1 reapareciendo. El texto de
contacto real (mail/WhatsApp/Instagram) sigue pendiente de confirmar con el
usuario antes del render final.
