"""
Ejemplos precargados de problemas para el método Simplex.
"""
from algorithms.parser import parsear_problema_completo
from models.problema import Problema


def ejemplo_1_basico() -> Problema:
    """Ejemplo 1: Simplex básico con maximización."""
    return parsear_problema_completo(
        linea_objetivo="Max Z = 3x1 + 5x2",
        lineas_restricciones=[
            "2x1 + 3x2 <= 12",
            "4x1 + 2x2 <= 16",
        ],
        nombre="Ejemplo 1 — Simplex Básico",
    )


def ejemplo_2_dos_fases() -> Problema:
    """Ejemplo 2: Problema que requiere Dos Fases (restricción >=)."""
    return parsear_problema_completo(
        linea_objetivo="Max Z = 2x1 + 3x2",
        lineas_restricciones=[
            "x1 + x2 >= 4",
            "x1 + 3x2 <= 12",
            "x1 <= 6",
        ],
        nombre="Ejemplo 2 — Dos Fases",
    )


def ejemplo_3_igualdad() -> Problema:
    """Ejemplo 3: Problema con restricción de igualdad."""
    return parsear_problema_completo(
        linea_objetivo="Max Z = 5x1 + 4x2",
        lineas_restricciones=[
            "x1 + x2 = 5",
            "10x1 + 6x2 <= 45",
        ],
        nombre="Ejemplo 3 — Restricción de Igualdad",
    )


def ejemplo_4_minimizacion() -> Problema:
    """Ejemplo 4: Problema de minimización."""
    return parsear_problema_completo(
        linea_objetivo="Min Z = 2x1 + 3x2",
        lineas_restricciones=[
            "x1 + x2 >= 4",
            "2x1 + x2 >= 6",
        ],
        nombre="Ejemplo 4 — Minimización",
    )


def ejemplo_5_dualidad() -> Problema:
    """Ejemplo 5: Problema diseñado para demostrar dualidad."""
    return parsear_problema_completo(
        linea_objetivo="Max Z = 3x1 + 5x2",
        lineas_restricciones=[
            "2x1 + x2 <= 10",
            "x1 + 3x2 <= 15",
        ],
        nombre="Ejemplo 5 — Dualidad",
    )


def ejemplo_6_revisado() -> Problema:
    """Ejemplo 6: Problema clásico para demostrar el Simplex Revisado."""
    return parsear_problema_completo(
        linea_objetivo="Max Z = 5x1 + 4x2 + 3x3",
        lineas_restricciones=[
            "6x1 + 4x2 + 2x3 <= 240",
            "3x1 + 2x2 + 5x3 <= 270",
            "5x1 + 6x2 + 5x3 <= 420",
        ],
        nombre="Ejemplo 6 — Simplex Revisado",
    )


EJEMPLOS = {
    "Ejemplo 1 — Simplex Básico": ejemplo_1_basico,
    "Ejemplo 2 — Dos Fases": ejemplo_2_dos_fases,
    "Ejemplo 3 — Igualdad": ejemplo_3_igualdad,
    "Ejemplo 4 — Minimización": ejemplo_4_minimizacion,
    "Ejemplo 5 — Dualidad": ejemplo_5_dualidad,
    "Ejemplo 6 — Simplex Revisado": ejemplo_6_revisado,
}


def cargar_ejemplo(nombre: str) -> Problema:
    """Carga un ejemplo por nombre."""
    if nombre not in EJEMPLOS:
        raise KeyError(f"Ejemplo '{nombre}' no encontrado. Disponibles: {list(EJEMPLOS.keys())}")
    return EJEMPLOS[nombre]()
