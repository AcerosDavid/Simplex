"""
Validaciones para el problema de Programación Lineal antes de resolver.
"""
from typing import List, Tuple, Optional
from models.problema import Problema
from models.restriccion import TipoRestriccion


class ErrorValidacion(Exception):
    """Excepción personalizada para errores de validación."""
    pass


def validar_problema(problema: Problema) -> Tuple[bool, List[str]]:
    """
    Valida un Problema antes de resolver.

    Returns:
        (es_valido, lista_de_errores)
    """
    errores: List[str] = []

    # 1. Debe tener variables
    if not problema.variables:
        errores.append("⚠ El problema no tiene variables de decisión definidas.")

    # 2. Debe tener restricciones
    if not problema.restricciones:
        errores.append("⚠ El problema no tiene restricciones definidas.")

    # 3. La función objetivo debe tener al menos un coeficiente no nulo
    if not any(c != 0 for c in problema.coef_objetivo.values()):
        errores.append("⚠ La función objetivo no tiene coeficientes no nulos.")

    # 4. Variables de la función objetivo deben existir en el problema
    nombres = problema.nombres_variables
    for nombre_var in problema.coef_objetivo:
        if nombre_var not in nombres:
            errores.append(
                f"⚠ La variable '{nombre_var}' en la función objetivo "
                f"no está declarada en las variables del problema."
            )

    # 5. Validar cada restricción
    for i, rest in enumerate(problema.restricciones):
        etiqueta = rest.nombre or f"Restricción {i + 1}"

        # 5a. Debe tener coeficientes
        if not rest.coeficientes:
            errores.append(f"⚠ {etiqueta}: no tiene coeficientes.")
            continue

        # 5b. Coeficientes deben ser numéricos finitos
        for var, coef in rest.coeficientes.items():
            try:
                val = float(coef)
                if not _es_finito(val):
                    errores.append(
                        f"⚠ {etiqueta}: el coeficiente de '{var}' no es finito."
                    )
            except (TypeError, ValueError):
                errores.append(
                    f"⚠ {etiqueta}: el coeficiente de '{var}' no es un número válido."
                )

        # 5c. RHS debe ser numérico finito
        try:
            rhs = float(rest.rhs)
            if not _es_finito(rhs):
                errores.append(f"⚠ {etiqueta}: el RHS no es un valor finito.")
        except (TypeError, ValueError):
            errores.append(f"⚠ {etiqueta}: el RHS no es un número válido.")

        # 5d. Las variables de la restricción deben estar declaradas
        for var in rest.coeficientes:
            if var not in nombres:
                errores.append(
                    f"⚠ {etiqueta}: la variable '{var}' no está declarada."
                )

    # 6. Variables duplicadas
    nombres_vistos = set()
    for v in problema.variables:
        if v.nombre in nombres_vistos:
            errores.append(f"⚠ La variable '{v.nombre}' está duplicada.")
        nombres_vistos.add(v.nombre)

    es_valido = len(errores) == 0
    return es_valido, errores


def _es_finito(valor: float) -> bool:
    """Verifica que el valor sea finito (no NaN ni Inf)."""
    import math
    return math.isfinite(valor)
