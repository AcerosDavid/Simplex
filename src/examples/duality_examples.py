"""
Ejemplos específicos para demostración de dualidad.
"""
from algorithms.parser import parsear_problema_completo
from models.problema import Problema


def ejemplo_dual_1() -> Problema:
    """Primal estándar para demostración de dualidad."""
    return parsear_problema_completo(
        linea_objetivo="Max Z = 3x1 + 5x2",
        lineas_restricciones=[
            "2x1 + x2 <= 10",
            "x1 + 3x2 <= 15",
        ],
        nombre="Dual — Ejemplo 1",
    )


def ejemplo_dual_2() -> Problema:
    """Primal de minimización para conversión a dual de maximización."""
    return parsear_problema_completo(
        linea_objetivo="Min Z = 2x1 + 3x2 + x3",
        lineas_restricciones=[
            "x1 + x2 + x3 >= 6",
            "2x1 + x2 >= 8",
        ],
        nombre="Dual — Ejemplo 2 (Min)",
    )
