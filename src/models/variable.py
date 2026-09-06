"""
Modelo que representa una variable de decisión o auxiliar.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TipoVariable(Enum):
    """Clasificación de variables dentro del modelo."""
    DECISION = "decision"       # x1, x2, ...
    HOLGURA = "holgura"         # s1, s2, ...  (slack)
    EXCESO = "exceso"           # e1, e2, ...  (surplus)
    ARTIFICIAL = "artificial"   # a1, a2, ...
    LIBRE = "libre"             # sin restricción de signo


@dataclass
class Variable:
    """
    Representa una variable del problema de PL.

    Attributes:
        nombre: Identificador de la variable (p.ej. 'x1', 's2', 'a1').
        tipo: Clasificación de la variable.
        coef_objetivo: Coeficiente en la función objetivo (0 para auxiliares).
        indice: Posición en el vector de variables (base 0).
        no_negativa: True si la variable debe ser >= 0.
    """
    nombre: str
    tipo: TipoVariable = TipoVariable.DECISION
    coef_objetivo: float = 0.0
    indice: int = 0
    no_negativa: bool = True

    def __repr__(self) -> str:
        return f"Variable({self.nombre}, tipo={self.tipo.value}, c={self.coef_objetivo})"

    def es_basica_inicial(self) -> bool:
        """Retorna True si la variable puede ser base inicial (holgura / artificial)."""
        return self.tipo in (TipoVariable.HOLGURA, TipoVariable.ARTIFICIAL)
