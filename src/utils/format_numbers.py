"""
Utilidades para formato de números en la interfaz.
"""
from fractions import Fraction
from typing import Union
import math


def format_number(
    valor: float,
    decimales: int = 4,
    modo: str = "decimal",
    epsilon: float = 1e-10,
) -> str:
    """
    Formatea un número para mostrar en la interfaz.

    Args:
        valor: Número a formatear.
        decimales: Cantidad de decimales a mostrar.
        modo: "decimal", "fraction" o "both".
        epsilon: Tolerancia para redondear a entero cercano.

    Returns:
        Cadena con el número formateado.
    """
    if math.isnan(valor):
        return "—"
    if math.isinf(valor):
        return "∞" if valor > 0 else "-∞"

    # Redondear si está muy cerca de un entero
    redondeado = round(valor)
    if abs(valor - redondeado) < epsilon:
        valor = float(redondeado)

    if modo == "decimal":
        return f"{valor:.{decimales}f}"

    # Intentar representar como fracción
    try:
        frac = Fraction(valor).limit_denominator(1000)
        frac_str = str(frac) if frac.denominator != 1 else str(frac.numerator)
    except (ValueError, OverflowError):
        frac_str = None

    if modo == "fraction":
        return frac_str if frac_str else f"{valor:.{decimales}f}"

    if modo == "both":
        dec_str = f"{valor:.{decimales}f}"
        if frac_str and frac.denominator != 1:
            return f"{dec_str} ({frac_str})"
        return dec_str

    return f"{valor:.{decimales}f}"


def limpiar_cero(valor: float, epsilon: float = 1e-10) -> float:
    """Retorna 0.0 si el valor está dentro de la tolerancia."""
    return 0.0 if abs(valor) < epsilon else valor


def es_entero(valor: float, epsilon: float = 1e-10) -> bool:
    """Retorna True si el valor es prácticamente un entero."""
    return abs(valor - round(valor)) < epsilon
