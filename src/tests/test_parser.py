"""
Pruebas unitarias para el módulo parser.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from algorithms.parser import (
    parsear_funcion_objetivo,
    parsear_restriccion,
    parsear_problema_completo,
    ParseError,
)
from models.problema import TipoOptimizacion
from models.restriccion import TipoRestriccion


class TestParsearFuncionObjetivo:

    def test_maximizar(self):
        tipo, coefs = parsear_funcion_objetivo("Max Z = 3x1 + 5x2")
        assert tipo == TipoOptimizacion.MAXIMIZAR
        assert coefs == {"x1": 3.0, "x2": 5.0}

    def test_minimizar(self):
        tipo, coefs = parsear_funcion_objetivo("Min Z = 2x1 - x2")
        assert tipo == TipoOptimizacion.MINIMIZAR
        assert coefs["x1"] == 2.0
        assert coefs["x2"] == -1.0

    def test_sin_z(self):
        tipo, coefs = parsear_funcion_objetivo("max 4x1 + 2x2 + x3")
        assert tipo == TipoOptimizacion.MAXIMIZAR
        assert coefs["x3"] == 1.0

    def test_coef_decimal(self):
        tipo, coefs = parsear_funcion_objetivo("Max Z = 1.5x1 + 2.5x2")
        assert coefs["x1"] == 1.5

    def test_formato_invalido(self):
        with pytest.raises(ParseError):
            parsear_funcion_objetivo("3x1 + 5x2")  # Sin Max/Min


class TestParsearRestriccion:

    def test_leq(self):
        rest = parsear_restriccion("2x1 + 3x2 <= 10")
        assert rest.tipo == TipoRestriccion.LEQ
        assert rest.rhs == 10.0
        assert rest.coeficientes["x1"] == 2.0

    def test_geq(self):
        rest = parsear_restriccion("x1 + x2 >= 4", indice=1)
        assert rest.tipo == TipoRestriccion.GEQ
        assert rest.rhs == 4.0
        assert rest.nombre == "R2"

    def test_eq(self):
        rest = parsear_restriccion("x1 + x2 = 5")
        assert rest.tipo == TipoRestriccion.EQ

    def test_formato_invalido(self):
        with pytest.raises(ParseError):
            parsear_restriccion("2x1 + 3x2 10")  # Sin signo


class TestParsearProblemaCompleto:

    def test_ejemplo_basico(self):
        problema = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        assert problema.num_variables == 2
        assert problema.num_restricciones == 2
        assert problema.tipo == TipoOptimizacion.MAXIMIZAR

    def test_tres_variables(self):
        problema = parsear_problema_completo(
            "Max Z = x1 + 2x2 + 3x3",
            ["x1 + x2 + x3 <= 10"],
        )
        assert problema.num_variables == 3

    def test_variable_sin_coef_en_objetivo(self):
        """Variable en restricción pero no en objetivo → coef = 0."""
        problema = parsear_problema_completo(
            "Max Z = 3x1",
            ["x1 + x2 <= 10"],
        )
        assert problema.coef_objetivo.get("x2", 0.0) == 0.0
