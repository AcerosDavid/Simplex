"""
Funciones auxiliares generales.
"""
from typing import List, Optional
import re


def nombre_variable_indice(prefijo: str, indice: int) -> str:
    """Genera nombres estilo 'x1', 's2', 'a3'."""
    return f"{prefijo}{indice}"


def extraer_numero(nombre: str) -> Optional[int]:
    """Extrae el número al final de un nombre de variable."""
    match = re.search(r'(\d+)$', nombre)
    return int(match.group(1)) if match else None


def ordenar_variables(nombres: List[str]) -> List[str]:
    """Ordena variables por prefijo y número."""
    def clave(n: str):
        partes = re.split(r'(\d+)', n)
        return [int(p) if p.isdigit() else p.lower() for p in partes]
    return sorted(nombres, key=clave)
