"""
Modelos para representar el resultado del algoritmo Simplex y sus iteraciones.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import numpy as np


class EstadoSolucion(Enum):
    """Estado final del problema tras aplicar el Simplex."""
    OPTIMA = "optima"
    INFACTIBLE = "infactible"
    ILIMITADO = "ilimitado"
    MULTIPLES = "multiples"
    DEGENERADO = "degenerado"
    SIN_RESOLVER = "sin_resolver"


@dataclass
class OperacionFila:
    """Registra una operación elemental de fila realizada durante el pivoteo."""
    descripcion: str          # Texto legible: "R2 = R2 - 2 * R1"
    fila_resultado: List[float] = field(default_factory=list)


@dataclass
class Iteracion:
    """
    Captura completa de una iteración del algoritmo Simplex.

    Attributes:
        numero: Número de iteración (0 = tabla inicial).
        variables_base: Lista de nombres de variables en la base.
        coefs_base: Coeficientes cj de las variables en la base.
        tabla: Tableau completo (filas × columnas incluyendo RHS).
        nombres_columnas: Nombres de columnas (variables + RHS).
        cj: Vector de coeficientes de la función objetivo para cada columna.
        zj: Vector Zj calculado.
        cj_zj: Vector Cj - Zj.
        variable_entrante: Nombre de la variable que entra a la base.
        variable_saliente: Nombre de la variable que sale de la base.
        col_pivote: Índice de columna del elemento pivote.
        fila_pivote: Índice de fila del elemento pivote.
        elemento_pivote: Valor del elemento pivote.
        razones: Lista de razones en la prueba de razón mínima.
        operaciones: Operaciones de fila realizadas.
        explicacion: Texto explicativo paso a paso de la iteración.
        fase: 1 o 2 (para método de Dos Fases); None en otros casos.
    """
    numero: int = 0
    variables_base: List[str] = field(default_factory=list)
    coefs_base: List[float] = field(default_factory=list)
    tabla: List[List[float]] = field(default_factory=list)
    nombres_columnas: List[str] = field(default_factory=list)
    cj: List[float] = field(default_factory=list)
    zj: List[float] = field(default_factory=list)
    cj_zj: List[float] = field(default_factory=list)
    variable_entrante: Optional[str] = None
    variable_saliente: Optional[str] = None
    col_pivote: Optional[int] = None
    fila_pivote: Optional[int] = None
    elemento_pivote: Optional[float] = None
    razones: List[Optional[float]] = field(default_factory=list)
    operaciones: List[OperacionFila] = field(default_factory=list)
    explicacion: str = ""
    fase: Optional[int] = None


@dataclass
class Resultado:
    """
    Resultado completo de la resolución de un problema de PL.

    Attributes:
        estado: Estado final de la solución.
        iteraciones: Historial completo de iteraciones.
        valores_variables: Mapa {nombre: valor} de la solución óptima.
        valor_objetivo: Valor óptimo de Z.
        variables_base_final: Variables en la base en la solución óptima.
        mensaje: Descripción textual del resultado.
        metodo: Nombre del método utilizado.
        num_iteraciones: Total de iteraciones realizadas.
    """
    estado: EstadoSolucion = EstadoSolucion.SIN_RESOLVER
    iteraciones: List[Iteracion] = field(default_factory=list)
    valores_variables: Dict[str, float] = field(default_factory=dict)
    valor_objetivo: Optional[float] = None
    variables_base_final: List[str] = field(default_factory=list)
    mensaje: str = ""
    metodo: str = "Simplex"
    num_iteraciones: int = 0

    def es_optima(self) -> bool:
        return self.estado == EstadoSolucion.OPTIMA

    def resumen(self) -> str:
        lines = [f"Estado: {self.estado.value}"]
        if self.valor_objetivo is not None:
            lines.append(f"Z* = {self.valor_objetivo:.4f}")
        for nombre, valor in self.valores_variables.items():
            lines.append(f"  {nombre} = {valor:.4f}")
        return "\n".join(lines)
