"""
Modelo principal del problema de Programación Lineal.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

from models.variable import Variable, TipoVariable
from models.restriccion import Restriccion, TipoRestriccion


class TipoOptimizacion(Enum):
    """Dirección de optimización."""
    MAXIMIZAR = "Max"
    MINIMIZAR = "Min"


@dataclass
class Problema:
    """
    Encapsula un problema de Programación Lineal.

    Attributes:
        nombre: Nombre descriptivo del problema.
        tipo: Maximizar o Minimizar.
        variables: Lista ordenada de variables de decisión.
        restricciones: Lista de restricciones.
        coef_objetivo: Mapa {nombre_variable: coeficiente en Z}.
    """
    nombre: str = "Problema sin nombre"
    tipo: TipoOptimizacion = TipoOptimizacion.MAXIMIZAR
    variables: List[Variable] = field(default_factory=list)
    restricciones: List[Restriccion] = field(default_factory=list)
    coef_objetivo: Dict[str, float] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    #  Propiedades derivadas                                               #
    # ------------------------------------------------------------------ #

    @property
    def num_variables(self) -> int:
        return len(self.variables)

    @property
    def num_restricciones(self) -> int:
        return len(self.restricciones)

    @property
    def nombres_variables(self) -> List[str]:
        return [v.nombre for v in self.variables]

    def obtener_variable(self, nombre: str) -> Optional[Variable]:
        """Busca una variable por nombre."""
        for v in self.variables:
            if v.nombre == nombre:
                return v
        return None

    def coef_var_objetivo(self, nombre: str) -> float:
        """Retorna el coeficiente de una variable en la función objetivo."""
        return self.coef_objetivo.get(nombre, 0.0)

    def funcion_objetivo_str(self) -> str:
        """Representación textual de la función objetivo."""
        terminos = []
        for nombre, coef in self.coef_objetivo.items():
            if coef == 0:
                continue
            if coef == 1:
                terminos.append(nombre)
            elif coef == -1:
                terminos.append(f"-{nombre}")
            else:
                terminos.append(f"{coef}{nombre}")
        expr = " + ".join(terminos).replace("+ -", "- ")
        return f"{self.tipo.value} Z = {expr}"

    def __repr__(self) -> str:
        return (
            f"Problema('{self.nombre}', {self.tipo.value}, "
            f"{self.num_variables} vars, {self.num_restricciones} rest.)"
        )
