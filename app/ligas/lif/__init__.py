from app.ligas import Categoria, Liga

LIGA = Liga(
    slug="lif",
    nombre="Liga Interprovincial de Fútbol",
    nombre_corto="LIF",
    hero_lineas=("Liga", "Interprovincial", "de Fútbol"),
    descripcion="Seguí toda la acción, los resultados, goleadores y posiciones de la liga en tiempo real.",
    resaltar_letra=1,
    logo="escudos/logolif_transparente.png",
    url_publica="https://lif-1.onrender.com",
    email_remitente="Liga Interprovincial <infoligainterprovincial@gmail.com>",
    categorias=(
        Categoria("primera", "Primera", "Primera División", "mayores"),
        Categoria("reserva", "Reserva", "Reserva", "mayores"),
        Categoria("quinta", "Quinta", "Quinta División", "inferiores"),
        Categoria("sexta", "Sexta", "Sexta División", "inferiores"),
        Categoria("septima", "Séptima", "Séptima División", "inferiores"),
    ),
)
