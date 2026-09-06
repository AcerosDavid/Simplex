"""
Configuración global de la aplicación.
"""
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class AppConfig:
    """Configuración principal de la aplicación."""

    # Ventana
    app_title: str = "Simplex — Programación Lineal"
    window_width: int = 1400
    window_height: int = 860
    min_width: int = 1100
    min_height: int = 700

    # Tema
    theme: str = "light"  # "dark" | "light"
    color_scheme: str = "green"

    # Precisión numérica
    decimal_places: int = 4
    epsilon: float = 1e-10          # Tolerancia para ceros
    big_m_value: float = 1e6        # Valor de M para Gran M

    # Límites de entrada
    max_variables: int = 10
    max_restrictions: int = 20
    min_variables: int = 2
    min_restrictions: int = 1

    # Base de datos
    db_path: str = "historial.db"

    # Colores de la tabla Simplex
    color_pivot_cell: str = "#FF6B35"
    color_entering_col: str = "#4ECDC4"
    color_leaving_row: str = "#FFE66D"
    color_optimal: str = "#95E77E"

    # Mostrar números como
    number_display: str = "decimal"  # "decimal" | "fraction" | "both"


# Instancia global
APP_CONFIG = AppConfig()
