"""
Formato de torneo de la LIF: dos torneos por temporada (Apertura y Clausura),
fase regular y playoffs desde cuartos de final con ida y vuelta.

Otra liga con otro formato (por ejemplo octavos como primera fase eliminatoria)
define su propio `formato.py` en `app/ligas/<slug>/` con estos mismos nombres.
"""

TORNEOS = ("Apertura", "Clausura")
TORNEO_INICIAL = "Apertura"

# (nombre, ida_vuelta) en orden de juego. El orden define `Fase.orden`.
FASES = (
    ("Regular", False),
    ("Cuartos", True),
    ("Semifinal", True),
    ("Final", True),
    ("Finalísima", True),
)
FASES_PLAYOFF = ("Cuartos", "Semifinal", "Final", "Finalísima")


def torneo_opuesto(nombre):
    """Apertura <-> Clausura (se usa al generar el fixture del otro torneo)."""
    return TORNEOS[0] if nombre == TORNEOS[1] else TORNEOS[1]


def cruces_clasificados(tabla):
    """Cruces de la primera fase de playoff a partir de la tabla ordenada:
    1º vs 8º, 2º vs 7º, 3º vs 6º y 4º vs 5º. Lista vacía si hay menos de 8."""
    if len(tabla) < 8:
        return []
    return [
        (tabla[0], tabla[7]),
        (tabla[1], tabla[6]),
        (tabla[2], tabla[5]),
        (tabla[3], tabla[4]),
    ]
