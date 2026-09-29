from app.ligas import Categoria, Liga

# Liga ficticia para mostrar ElTablón: mismos rubros y categorías que una liga real,
# pero con clubes inventados. Con demo=True no envía mails ni sube archivos.
LIGA = Liga(
    slug="demo",
    nombre="Liga Regional de Fútbol",
    nombre_corto="LRF",
    hero_lineas=("Liga", "Regional", "de Fútbol"),
    descripcion="Seguí toda la acción, los resultados, goleadores y posiciones de la liga en tiempo real.",
    logo="escudos/demo/logo.png",
    url_publica="https://demo.eltablon.com",
    email_remitente="Liga Regional <demo@eltablon.com>",
    categorias=(
        Categoria("primera", "Primera", "Primera División", "mayores"),
        Categoria("reserva", "Reserva", "Reserva", "mayores"),
        Categoria("quinta", "Quinta", "Quinta División", "inferiores"),
        Categoria("sexta", "Sexta", "Sexta División", "inferiores"),
        Categoria("septima", "Séptima", "Séptima División", "inferiores"),
    ),
    email_admin_inicial="admin@demo.eltablon.com",
    email_demo="demo@eltablon.com",
    email_periodista_demo="periodista@eltablon.com",
    acento="#2dd4bf",
    acento_dim="#14b8a6",
    demo=True,
)
