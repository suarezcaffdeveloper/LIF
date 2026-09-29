# Frame spec — LIF, video de venta

## Concept angle

Un sistema de software se vende mostrando el momento en que deja de ser
trabajo manual: un administrador carga un resultado y la liga entera lo ve
al instante. Todo lo demás — el tour público, los 3 roles — es evidencia de
esa promesa, no la promesa en sí.

## Palette

Modo oscuro real del producto, no un preset genérico. Un solo acento
(celeste), sin gradientes ni degradé cian-a-violeta.

- `--bg`: `#0A0C0F` (casi negro, con un ligerísimo tinte frío)
- `--surface`: `#14181D` (paneles, cards)
- `--fg`: `#EDEFF2` (blanco roto, nunca #fff puro)
- `--muted`: `#8B94A0` (texto secundario, metadatos)
- `--accent`: `#4CC3EA` (celeste — CTA, subrayados, estado activo, la
  cápsula de rol en cada escena)

Nota de intencionalidad: celeste-sobre-oscuro es una "AI design tell" por
default (house-style), pero acá es una elección deliberada — es literalmente
la paleta real de la interfaz de LIF (gris + blanco + celeste, modo oscuro).
No se decoran las capturas: se las deja leer como son.

## Typography

Cruce sans condensada + mono (no dos sans), con tensión real: autoridad de
cartelera de estadio vs. precisión de un panel de software.

- **Titulares / cartelones / CTA**: `Oswald`, 700, mayúsculas, tracking
  -0.02em — el registro "marcador de estadio".
- **Subtítulos cinéticos (texto sobre las capturas)**: `Oswald`, 400/500,
  frases cortas, una idea por golpe.
- **Etiquetas de rol / datos / metadatos** (ADMIN · PERIODISTA · marcas de
  tiempo, chips): `IBM Plex Mono`, 400/700, `tabular-nums` — el registro
  "panel técnico".

Tamaños para visualización completa (YouTube/embed, no feed): titulares
60–90px, subtítulos cinéticos 28–36px, chips/etiquetas 16–18px. Peso de
cuerpo 350 en vez de 400 (blanco sobre negro lee más pesado).

## Focal element / anchors / background

- **Focal**: la captura de pantalla real de LIF, siempre a pantalla
  completa o dentro de un marco de navegador minimalista (una línea
  `--muted` de 1px, sin barra de navegador realista pesada).
- **Anclas de borde**: chip de rol (ADMIN/PERIODISTA/PÚBLICO) en una
  esquina fija en mono; subtítulo cinético anclado al tercio inferior.
- **Detalle de apoyo**: una línea celeste hairline que aparece bajo el
  subtítulo activo (subraya, no decora).
- **Fondo** (solo en frames sin captura — hook, cartelones, cierre): `--bg`
  liso + 2–3 decorativos ambientales de bajo perfil (glow celeste muy tenue
  respirando, una línea hairline `--muted`), nunca un patrón cargado —
  coherente con "minimalista".

## Motion identity (compartida entre escenas)

- Transiciones **conectivas** (tour público, frames 3–7): whip-pan CSS
  suave (0.3–0.4s) o crossfade con blur — nunca corte seco.
- Transición **al frame centro** (admin, frame 10): la única de la pieza
  que se gana un shader — `domain-warp` o `whip-pan` (GPU), marcando que
  ahí está el clímax.
- Subtítulos: entran con `spring-pop-entrance` recortado (sin rebote
  exagerado, minimalista), salen con blur-out rápido — nunca fade simple ni
  slam agresivo.
- Un único movimiento ambiental por escena (glow respirando o línea
  hairline con pulso lento) — no acumular decorativos.
