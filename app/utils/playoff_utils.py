def obtener_ganador_partido(partido):
    """
    Determina el ganador real del partido.
    Considera goles y penales.

    Returns:
        Equipo ganador o None
    """

    # Partido no jugado
    if not partido.jugado:
        return None

    # ✅ Ganador en tiempo reglamentario
    if partido.goles_local > partido.goles_visitante:
        return partido.equipo_local

    if partido.goles_visitante > partido.goles_local:
        return partido.equipo_visitante

    # ✅ Empate → usar penales
    if (
        partido.penales_local is not None and
        partido.penales_visitante is not None
    ):
        if partido.penales_local > partido.penales_visitante:
            return partido.equipo_local

        if partido.penales_visitante > partido.penales_local:
            return partido.equipo_visitante

    # ⚠️ empate sin definir
    return None