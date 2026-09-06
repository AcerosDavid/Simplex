"""
Modelo que representa una restricción del problema de PL.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict


class TipoRestriccion(Enum):
    """Tipo de restricción."""
    LEQ = "<="   # Menor o igual
    GEQ = ">="   # Mayor o igual
    EQ  = "="    # Igual


@dataclass
class Restriccion:
    """
    Representa una restricción lineal.

    Attributes:
        nombre: Etiqueta de la restricción (p.ej. 'R1').
        coeficientes: Mapa {nombre_variable: coeficiente}.
        tipo: Tipo de restricción (<= / >= / =).
        rhs: Lado derecho (Right-Hand Side).
        indice: Posición dentro del sistema (base 0).
    """
    nombre: str
    coeficientes: Dict[str, float] = field(default_factory=dict)
    tipo: TipoRestriccion = TipoRestriccion.LEQ
    rhs: float = 0.0
    indice: int = 0

    def obtener_coef(self, nombre_var: str) -> float:
        """Retorna el coeficiente de una variable (0 si no aparece)."""
        return self.coeficientes.get(nombre_var, 0.0)

    def __repr__(self) -> str:
        terminos = " + ".join(
            f"{v}*{k}" for k, v in self.coeficientes.items()
        )
        return f"Restriccion({self.nombre}: {terminos} {self.tipo.value} {self.rhs})"
