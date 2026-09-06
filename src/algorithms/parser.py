"""
Parser de expresiones de Programación Lineal en texto natural.

Soporta expresiones como:
    "Max Z = 3x1 + 5x2"
    "2x1 + 3x2 <= 10"
    "x1 - 2x2 + 4x3 >= 8"
    "x1 + x2 = 5"
"""
import re
from typing import List, Tuple, Dict, Optional

from models.problema import Problema, TipoOptimizacion
from models.variable import Variable, TipoVariable
from models.restriccion import Restriccion, TipoRestriccion


class ParseError(Exception):
    """Error durante el análisis de texto."""
    pass


# Patrones regex
_PATRON_TERMINO = re.compile(
    r'([+-]?\s*\d*\.?\d*)\s*\*?\s*([a-zA-Z][a-zA-Z0-9]*)'
)
_PATRON_RESTRICCION = re.compile(
    r'^(.+?)\s*(<=|>=|=)\s*([+-]?\d+\.?\d*)$'
)
_PATRON_OBJETIVO = re.compile(
    r'^(max|min|maximize|minimize)\s*(?:z\s*=\s*)?(.+)$',
    re.IGNORECASE
)


def parsear_funcion_objetivo(texto: str) -> Tuple[TipoOptimizacion, Dict[str, float]]:
    """
    Analiza la función objetivo.

    Args:
        texto: Cadena como "Max Z = 3x1 + 5x2" o "min 2x1 - x2"

    Returns:
        (tipo_optimizacion, dict {variable: coeficiente})

    Raises:
        ParseError: Si el formato no es reconocible.
    """
    texto = texto.strip()
    match = _PATRON_OBJETIVO.match(texto)
    if not match:
        raise ParseError(
            f"No se puede interpretar la función objetivo: '{texto}'\n"
            "Formato esperado: 'Max Z = 3x1 + 5x2' o 'Min 2x1 + x2'"
        )

    tipo_str = match.group(1).lower()
    expresion = match.group(2).strip()

    tipo = (
        TipoOptimizacion.MAXIMIZAR
        if tipo_str.startswith("max")
        else TipoOptimizacion.MINIMIZAR
    )
    coeficientes = _parsear_expresion_lineal(expresion)
    return tipo, coeficientes


def parsear_restriccion(texto: str, indice: int = 0) -> Restriccion:
    """
    Analiza una restricción en texto.

    Args:
        texto: Cadena como "2x1 + 3x2 <= 10"
        indice: Posición de la restricción (base 0).

    Returns:
        Objeto Restriccion.

    Raises:
        ParseError: Si el formato no es válido.
    """
    texto = texto.strip()
    match = _PATRON_RESTRICCION.match(texto)
    if not match:
        raise ParseError(
            f"No se puede interpretar la restricción: '{texto}'\n"
            "Formato esperado: '2x1 + 3x2 <= 10'"
        )

    lado_izq = match.group(1).strip()
    signo_str = match.group(2).strip()
    rhs_str = match.group(3).strip()

    coeficientes = _parsear_expresion_lineal(lado_izq)

    tipo_map = {"<=": TipoRestriccion.LEQ, ">=": TipoRestriccion.GEQ, "=": TipoRestriccion.EQ}
    tipo = tipo_map[signo_str]

    try:
        rhs = float(rhs_str)
    except ValueError:
        raise ParseError(f"El lado derecho '{rhs_str}' no es un número válido.")

    return Restriccion(
        nombre=f"R{indice + 1}",
        coeficientes=coeficientes,
        tipo=tipo,
        rhs=rhs,
        indice=indice,
    )


def parsear_problema_completo(
    linea_objetivo: str,
    lineas_restricciones: List[str],
    nombre: str = "Problema",
) -> Problema:
    """
    Construye un Problema completo a partir de texto.

    Args:
        linea_objetivo: "Max Z = 3x1 + 5x2"
        lineas_restricciones: ["2x1 + 3x2 <= 10", "4x1 + x2 <= 15"]
        nombre: Nombre del problema.

    Returns:
        Objeto Problema validado.
    """
    tipo, coef_obj = parsear_funcion_objetivo(linea_objetivo)

    restricciones: List[Restriccion] = []
    for i, linea in enumerate(lineas_restricciones):
        linea = linea.strip()
        if not linea:
            continue
        rest = parsear_restriccion(linea, i)
        restricciones.append(rest)

    # Reunir todos los nombres de variables (objetivo + restricciones)
    todos_nombres: List[str] = []
    for nombre_var in coef_obj:
        if nombre_var not in todos_nombres:
            todos_nombres.append(nombre_var)
    for rest in restricciones:
        for nombre_var in rest.coeficientes:
            if nombre_var not in todos_nombres:
                todos_nombres.append(nombre_var)

    # Ordenar naturalmente: x1, x2, x3, ...
    todos_nombres = _ordenar_variables(todos_nombres)

    variables = [
        Variable(
            nombre=n,
            tipo=TipoVariable.DECISION,
            coef_objetivo=coef_obj.get(n, 0.0),
            indice=i,
            no_negativa=True,
        )
        for i, n in enumerate(todos_nombres)
    ]

    return Problema(
        nombre=nombre,
        tipo=tipo,
        variables=variables,
        restricciones=restricciones,
        coef_objetivo={n: coef_obj.get(n, 0.0) for n in todos_nombres},
    )


# ------------------------------------------------------------------ #
#  Helpers internos                                                    #
# ------------------------------------------------------------------ #

def _parsear_expresion_lineal(expresion: str) -> Dict[str, float]:
    """
    Convierte una expresión lineal en un diccionario {variable: coeficiente}.

    Soporta: "3x1 + 5x2", "2x1 - x2 + 4x3", "-x1 + 2.5x2"
    """
    # Normalizar espacios y asegurar signo inicial
    expresion = expresion.strip()
    if not expresion.startswith(('+', '-')):
        expresion = '+' + expresion

    # Insertar separadores antes de cada signo que precede a un término
    # (excepto signos dentro de números como 1e-5)
    normalizada = re.sub(r'\s*([+-])\s*', r' \1', expresion)
    tokens = normalizada.split()

    coefs: Dict[str, float] = {}

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # ¿El token es sólo un signo? fusionar con el siguiente
        if token in ('+', '-') and i + 1 < len(tokens):
            token = token + tokens[i + 1]
            i += 2
        else:
            i += 1

        match = _PATRON_TERMINO.match(token.replace(' ', ''))
        if not match:
            continue

        coef_str = match.group(1).replace(' ', '').replace('+-', '-').replace('--', '+')
        var_nombre = match.group(2)

        if coef_str in ('', '+'):
            coef = 1.0
        elif coef_str == '-':
            coef = -1.0
        else:
            try:
                coef = float(coef_str)
            except ValueError:
                raise ParseError(f"Coeficiente inválido: '{coef_str}' en '{token}'")

        if var_nombre in coefs:
            coefs[var_nombre] += coef
        else:
            coefs[var_nombre] = coef

    if not coefs:
        raise ParseError(f"No se encontraron términos válidos en: '{expresion}'")

    return coefs


def _ordenar_variables(nombres: List[str]) -> List[str]:
    """
    Ordena variables numéricamente cuando corresponda.
    x1, x2, x10 en lugar de x1, x10, x2.
    """
    import re as _re

    def clave(nombre: str):
        partes = _re.split(r'(\d+)', nombre)
        return [int(p) if p.isdigit() else p.lower() for p in partes]

    return sorted(nombres, key=clave)
