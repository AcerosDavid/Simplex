"""
Conversión de un Problema de PL a Forma Estándar.

Reglas:
  - Restricción <=  → agregar variable de holgura (s_i >= 0)
  - Restricción >=  → agregar variable de exceso (e_i >= 0) y artificial (a_i >= 0)
  - Restricción  =  → agregar variable artificial (a_i >= 0)
  - Minimización    → convertir internamente a maximización (Max -Z)
                      O trabajar directamente con Cj-Zj <= 0 como criterio de parada.
                      Aquí mantenemos la dirección original y ajustamos el criterio.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import copy

from models.problema import Problema, TipoOptimizacion
from models.variable import Variable, TipoVariable
from models.restriccion import Restriccion, TipoRestriccion


@dataclass
class ProblemaEstandar:
    """
    Problema de PL en forma estándar (todas restricciones =).

    Attributes:
        problema_original: Referencia al problema antes de la conversión.
        variables_decision: Variables originales de decisión.
        variables_auxiliares: Holguras, excesos y artificiales añadidas.
        todas_variables: Lista ordenada de TODAS las variables (decisión + aux).
        restricciones: Restricciones ya convertidas a igualdades.
        coef_objetivo: Coeficientes de la función objetivo (incluyendo aux = 0).
        base_inicial: Variables que forman la base inicial.
        tiene_artificiales: True si se añadieron variables artificiales.
        pasos_conversion: Lista de cadenas que describen cada transformación.
        tipo: Tipo de optimización original.
    """
    problema_original: Problema = field(default=None)
    variables_decision: List[Variable] = field(default_factory=list)
    variables_auxiliares: List[Variable] = field(default_factory=list)
    todas_variables: List[Variable] = field(default_factory=list)
    restricciones: List[Restriccion] = field(default_factory=list)
    coef_objetivo: Dict[str, float] = field(default_factory=dict)
    base_inicial: List[str] = field(default_factory=list)
    tiene_artificiales: bool = False
    pasos_conversion: List[str] = field(default_factory=list)
    tipo: TipoOptimizacion = TipoOptimizacion.MAXIMIZAR

    @property
    def nombres_variables(self) -> List[str]:
        return [v.nombre for v in self.todas_variables]

    @property
    def num_variables(self) -> int:
        return len(self.todas_variables)

    @property
    def num_restricciones(self) -> int:
        return len(self.restricciones)


def convertir_a_forma_estandar(problema: Problema) -> ProblemaEstandar:
    """
    Convierte un Problema a su Forma Estándar.

    Args:
        problema: Problema de PL original.

    Returns:
        ProblemaEstandar con toda la información de la conversión.
    """
    pe = ProblemaEstandar()
    pe.problema_original = problema
    pe.tipo = problema.tipo

    # Copiar variables de decisión
    pe.variables_decision = [copy.deepcopy(v) for v in problema.variables]
    pe.coef_objetivo = dict(problema.coef_objetivo)

    pasos: List[str] = []
    pasos.append(f"Problema original: {problema.funcion_objetivo_str()}")
    pasos.append("─" * 50)
    pasos.append("Conversión a Forma Estándar:")
    pasos.append("")

    contadores = {"s": 0, "e": 0, "a": 0}
    restricciones_estandar: List[Restriccion] = []
    base_inicial: List[str] = []
    variables_aux: List[Variable] = []

    for i, rest in enumerate(problema.restricciones):
        rest_nueva = copy.deepcopy(rest)
        etiqueta = rest.nombre or f"R{i + 1}"

        if rest.tipo == TipoRestriccion.LEQ:
            # Agregar variable de holgura
            contadores["s"] += 1
            nombre_s = f"s{contadores['s']}"
            var_s = Variable(
                nombre=nombre_s,
                tipo=TipoVariable.HOLGURA,
                coef_objetivo=0.0,
                indice=len(pe.variables_decision) + len(variables_aux),
                no_negativa=True,
            )
            variables_aux.append(var_s)
            rest_nueva.coeficientes[nombre_s] = 1.0
            rest_nueva.tipo = TipoRestriccion.EQ
            pe.coef_objetivo[nombre_s] = 0.0
            base_inicial.append(nombre_s)
            pasos.append(
                f"  {etiqueta}: {_rest_str(rest)} → {_rest_str(rest_nueva)}"
            )
            pasos.append(f"  → Se agrega variable de holgura {nombre_s} ≥ 0")

        elif rest.tipo == TipoRestriccion.GEQ:
            # Agregar variable de exceso (con signo negativo)
            contadores["e"] += 1
            nombre_e = f"e{contadores['e']}"
            var_e = Variable(
                nombre=nombre_e,
                tipo=TipoVariable.EXCESO,
                coef_objetivo=0.0,
                indice=len(pe.variables_decision) + len(variables_aux),
                no_negativa=True,
            )
            variables_aux.append(var_e)
            rest_nueva.coeficientes[nombre_e] = -1.0
            pe.coef_objetivo[nombre_e] = 0.0

            # Agregar variable artificial
            contadores["a"] += 1
            nombre_a = f"a{contadores['a']}"
            var_a = Variable(
                nombre=nombre_a,
                tipo=TipoVariable.ARTIFICIAL,
                coef_objetivo=0.0,  # Se ajusta en Gran M o Dos Fases
                indice=len(pe.variables_decision) + len(variables_aux),
                no_negativa=True,
            )
            variables_aux.append(var_a)
            rest_nueva.coeficientes[nombre_a] = 1.0
            rest_nueva.tipo = TipoRestriccion.EQ
            pe.coef_objetivo[nombre_a] = 0.0
            base_inicial.append(nombre_a)
            pe.tiene_artificiales = True
            pasos.append(
                f"  {etiqueta}: {_rest_str(rest)} → {_rest_str(rest_nueva)}"
            )
            pasos.append(f"  → Se agrega variable de exceso {nombre_e} ≥ 0")
            pasos.append(f"  → Se agrega variable artificial {nombre_a} ≥ 0")

        elif rest.tipo == TipoRestriccion.EQ:
            # Solo variable artificial
            contadores["a"] += 1
            nombre_a = f"a{contadores['a']}"
            var_a = Variable(
                nombre=nombre_a,
                tipo=TipoVariable.ARTIFICIAL,
                coef_objetivo=0.0,
                indice=len(pe.variables_decision) + len(variables_aux),
                no_negativa=True,
            )
            variables_aux.append(var_a)
            rest_nueva.coeficientes[nombre_a] = 1.0
            rest_nueva.tipo = TipoRestriccion.EQ
            pe.coef_objetivo[nombre_a] = 0.0
            base_inicial.append(nombre_a)
            pe.tiene_artificiales = True
            pasos.append(
                f"  {etiqueta}: {_rest_str(rest)} → {_rest_str(rest_nueva)}"
            )
            pasos.append(f"  → Se agrega variable artificial {nombre_a} ≥ 0")

        restricciones_estandar.append(rest_nueva)
        pasos.append("")

    pe.variables_auxiliares = variables_aux
    pe.todas_variables = pe.variables_decision + variables_aux
    pe.restricciones = restricciones_estandar
    pe.base_inicial = base_inicial
    pe.pasos_conversion = pasos

    return pe


# ------------------------------------------------------------------ #
#  Helper                                                              #
# ------------------------------------------------------------------ #

def _rest_str(rest: Restriccion) -> str:
    """Representación compacta de una restricción para los pasos."""
    terminos = []
    for var, coef in rest.coeficientes.items():
        if coef == 1.0:
            terminos.append(var)
        elif coef == -1.0:
            terminos.append(f"-{var}")
        else:
            terminos.append(f"{coef}{var}")
    lado_izq = " + ".join(terminos).replace("+ -", "- ")
    return f"{lado_izq} {rest.tipo.value} {rest.rhs}"
