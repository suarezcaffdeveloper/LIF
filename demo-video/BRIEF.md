---
workflow: general-video
flow: automation
storyboard: yes
message: "LIF le da a tu liga un sistema profesional para publicar posiciones, goleadores, fixture y noticias en minutos, sin depender de un programador."
destination: youtube
aspect: 1920x1080
language: es
audience: "dirigentes y administradores de ligas de fútbol evaluando sumarse a un sistema de gestión"
length: 90s
---

## Intent

Video de venta para LIF, un sistema de gestión para ligas de fútbol. El
objetivo es mandárselo a otras ligas que piden ver el sistema antes de
sumarse. Tiene que ser un video **único y genérico**, reutilizable para
cualquier liga interesada — no debe nombrar ni atarse a una liga cliente en
particular.

Tiene que mostrar los 3 tipos de usuario del sistema:

1. Usuario público (solo ve información: posiciones, goleadores, fixture,
   noticias y videos).
2. Periodista (panel acotado: carga noticias y videos).
3. Administrador (panel completo: carga estadísticas, fixture, jugadores,
   clubes y resultados; lo que carga se refleja al instante en la web
   pública).

Tono: minimalista, profesional, oscuro — igual al modo oscuro real del
producto. Texto animado en pantalla con movimiento suave (subtítulos
cinéticos), sin locución. Transiciones suaves y con movimiento entre
escenas, nunca cortes secos.

## Assets

- videos/ — carpeta en la raíz del repo (fuera de este proyecto) donde el
  usuario va guardando, a medida que las graba, las capturas de pantalla en
  bruto. Un archivo por escena, nombrado según lo que muestra. El mapeo
  exacto nombre de archivo → escena se define en el storyboard antes de
  armar la composición.

## Customizations

- Subtítulos/texto en pantalla con movimiento suave y minimalista (kinetic
  captions), no un narrador leyendo el texto.
- Transiciones suaves con movimiento entre escenas (crossfade/slide con
  motion, evitar cortes secos).
- Paleta oscura con grises, blancos y celeste — acorde al modo oscuro real
  del producto (no un preset genérico de marca).
- Sin logo: el usuario no tiene un archivo de logo todavía. Apertura y
  cierre solo con tipografía sobre la paleta oscura.
- Música de fondo de bajo perfil, sin voz en off.
- Cierre con texto de contacto/CTA — pendiente de que el usuario confirme el
  texto exacto (email/WhatsApp/Instagram) antes del render final.

## Notes

- No debe nombrar una liga cliente específica: solo muestra el sistema LIF
  en general, para que sirva como el mismo video para cualquier liga.
- Estructura actual (13 escenas, ~71.5s): hook tipográfico → home pública →
  tabla de posiciones → goleadores → fixture general → noticias/videos →
  cartel "Gestioná la información con estos roles" → panel de periodista
  (pantallazo de carga de una noticia) → panel de administrador, vista
  general (pantallazo de varias acciones) → carga de fixture (manual o
  automática por sorteo) → carga de jugadores (manual o masiva por Excel) →
  carga de estadísticas → cierre con CTA. El plantel de un club se descartó
  a pedido del usuario — no se muestra en el video. Ninguno de los paneles
  con rol muestra el flujo completo: son pantallazos de lo que cada uno
  puede hacer, no una demo end-to-end.
- Las tres funcionalidades de admin (fixture, jugadores, estadísticas) van
  después del panel general de administrador y antes del cierre — mismo
  chip "ADMINISTRADOR" arriba del video que el resto de las escenas de ese
  rol. El subtítulo de fixture menciona las dos formas de cargarlo (manual
  o sorteo automático); el de jugadores menciona carga manual e importación
  masiva por Excel.
- Ya no hay cartel "3 tipos de usuario" ni pantalla de login: el público ya
  vio todo lo que ve el rol usuario en el tour (frames 2–6), así que
  volver a anunciar que ese rol existe sería redundante. El quiebre de tema
  hacia los roles con panel arranca directo en "Gestioná la información con
  estos roles" y va derecho a periodista y administrador.
- En los frames de periodista y administrador: el rol (PERIODISTA /
  ADMINISTRADOR) se indica arriba del video en un chip mono celeste, y el
  subtítulo va debajo del video — mismo lenguaje visual que el resto del
  tour (donde el chip dice PÚBLICO).
- Sin voz en off: solo texto animado + música de fondo. El video debe leerse
  bien con el sonido apagado (WhatsApp/Instagram).
- Canal de distribución real: el usuario comparte el video por email,
  WhatsApp o Instagram según a quién le esté respondiendo. Se decidió subir
  el render final a YouTube como no listado y pasar ese link, porque
  funciona igual en cualquiera de esos canales, sin límites de tamaño de
  archivo ni pérdida de calidad al reenviarlo — y el contenido (capturas de
  pantalla de una web) es naturalmente horizontal (16:9), por eso el aspect
  ratio elegido es 1920x1080 en vez de un formato vertical o cuadrado.
- Las capturas de pantalla todavía no existen: el usuario las va a grabar
  después de definir el storyboard. El storyboard debe dejar claro, escena
  por escena, qué pantalla del sistema grabar y qué nombre de archivo
  ponerle dentro de videos/.
