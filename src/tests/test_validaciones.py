"""
Pruebas unitarias para las validaciones del problema.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from algorithms.parser import parsear_problema_completo
from algorithms.validaciones import validar_problema
from models.problema import Problema, TipoOptimizacion
from models.variable import Variable, TipoVariable


class TestValidaciones:

    def test_problema_valido(self):
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        es_valido, errores = validar_problema(p)
        assert es_valido
        assert errores == []

    def test_sin_variables(self):
        p = Problema(nombre="Vacío", tipo=TipoOptimizacion.MAXIMIZAR)
        es_valido, errores = validar_problema(p)
        assert not es_valido
        assert any("variables" in e.lower() for e in errores)

    def test_sin_restricciones(self):
        p = parsear_problema_completo("Max Z = 3x1 + 5x2", [])
        es_valido, errores = validar_problema(p)
        assert not es_valido
        assert any("restricciones" in e.lower() for e in errores)

    def test_variable_duplicada(self):
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12"],
        )
        # Duplicar manualmente
        v_dup = Variable("x1", TipoVariable.DECISION, 3.0, 0)
        p.variables.append(v_dup)
        es_valido, errores = validar_problema(p)
        assert not es_valido
        assert any("duplicada" in e.lower() for e in errores)
