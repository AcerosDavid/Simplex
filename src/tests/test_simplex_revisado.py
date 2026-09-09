"""
Pruebas unitarias para el algoritmo Simplex Revisado.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from algorithms.parser import parsear_problema_completo
from algorithms.simplex_revisado import SimplexRevisado
from algorithms.simplex import AlgoritmoSimplex
from models.resultado import EstadoSolucion


class TestSimplexRevisado:

    def test_maximizacion_basica(self):
        """Max Z = 3x1 + 5x2, 2x1+3x2<=12, 4x1+2x2<=16 -> Z*=20 (x1=0, x2=4)."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        r = SimplexRevisado(p).resolver()
        assert r.estado == EstadoSolucion.OPTIMA
        assert abs(r.valor_objetivo - 20.0) < 1e-5
        assert abs(r.valores_variables.get("x1", 0.0) - 0.0) < 1e-5
        assert abs(r.valores_variables.get("x2", 0.0) - 4.0) < 1e-5

    def test_tres_variables(self):
        """Max Z = 5x1 + 4x2 + 3x3 -> Z*=273.75."""
        p = parsear_problema_completo(
            "Max Z = 5x1 + 4x2 + 3x3",
            [
                "6x1 + 4x2 + 2x3 <= 240",
                "3x1 + 2x2 + 5x3 <= 270",
                "5x1 + 6x2 + 5x3 <= 420",
            ],
        )
        r_rev = SimplexRevisado(p).resolver()
        r_tab = AlgoritmoSimplex(p).resolver()
        assert r_rev.estado == EstadoSolucion.OPTIMA
        assert abs(r_rev.valor_objetivo - 273.75) < 1e-4
        assert abs(r_rev.valor_objetivo - r_tab.valor_objetivo) < 1e-4

    def test_minimizacion_con_artificiales(self):
        """Min Z = 2x1 + 3x2, x1+x2>=4, 2x1+x2>=6 -> Z*=8 (x1=2, x2=2)."""
        p = parsear_problema_completo(
            "Min Z = 2x1 + 3x2",
            ["x1 + x2 >= 4", "2x1 + x2 >= 6"],
        )
        r = SimplexRevisado(p).resolver()
        assert r.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)
        assert abs(r.valor_objetivo - 8.0) < 1e-4

    def test_restriccion_igualdad(self):
        """Max Z = 5x1 + 4x2, x1+x2=5, 10x1+6x2<=45 -> Z*=23.75."""
        p = parsear_problema_completo(
            "Max Z = 5x1 + 4x2",
            ["x1 + x2 = 5", "10x1 + 6x2 <= 45"],
        )
        r = SimplexRevisado(p).resolver()
        assert r.estado == EstadoSolucion.OPTIMA
        assert abs(r.valor_objetivo - 23.75) < 1e-4

    def test_iteraciones_estructura(self):
        """Verificar que las iteraciones contengan B⁻¹, x_B y costos reducidos."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        r = SimplexRevisado(p).resolver()
        assert len(r.iteraciones) > 0
        it0 = r.iteraciones[0]
        assert it0.tabla is not None
        assert len(it0.tabla) == 2  # 2 restricciones -> matriz 2x2 + x_B
        assert len(it0.tabla[0]) == 3  # [B⁻¹_1, B⁻¹_2, x_B]
        assert it0.explicacion != ""
