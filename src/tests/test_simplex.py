"""
Pruebas unitarias para el algoritmo Simplex.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from algorithms.parser import parsear_problema_completo
from algorithms.simplex import AlgoritmoSimplex
from algorithms.dos_fases import DosFases
from models.resultado import EstadoSolucion


class TestSimplexBasico:

    def test_ejemplo_clasico_max(self):
        """Max Z = 3x1 + 5x2, 2x1+3x2<=12, 4x1+2x2<=16 → Z*=20 (x1=0, x2=4)."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        solver = AlgoritmoSimplex(p)
        r = solver.resolver()
        assert r.estado == EstadoSolucion.OPTIMA
        assert abs(r.valor_objetivo - 20.0) < 1e-6

    def test_ejemplo_dualidad(self):
        """Max Z = 3x1 + 5x2, 2x1+x2<=10, x1+3x2<=15 → Z*=29 (x1=3, x2=4)."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        solver = AlgoritmoSimplex(p)
        r = solver.resolver()
        assert r.estado == EstadoSolucion.OPTIMA
        assert abs(r.valor_objetivo - 29.0) < 1e-4

    def test_minimizacion(self):
        """Min Z = 2x1 + 3x2, x1+x2>=4, 2x1+x2>=6."""
        p = parsear_problema_completo(
            "Min Z = 2x1 + 3x2",
            ["x1 + x2 >= 4", "2x1 + x2 >= 6"],
        )
        solver = DosFases(p)
        r = solver.resolver()
        assert r.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)
        assert r.valor_objetivo is not None
        assert r.valor_objetivo >= 0

    def test_tres_variables(self):
        """Max Z = 5x1 + 4x2 + 3x3 con restricciones estándar."""
        p = parsear_problema_completo(
            "Max Z = 5x1 + 4x2 + 3x3",
            [
                "6x1 + 4x2 + 2x3 <= 240",
                "3x1 + 2x2 + 5x3 <= 270",
                "5x1 + 6x2 + 5x3 <= 420",
            ],
        )
        solver = AlgoritmoSimplex(p)
        r = solver.resolver()
        assert r.estado == EstadoSolucion.OPTIMA
        assert r.valor_objetivo > 0

    def test_iteraciones_guardadas(self):
        """Verifica que se guarden al menos 2 iteraciones (inicial + óptima)."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        solver = AlgoritmoSimplex(p)
        r = solver.resolver()
        assert len(r.iteraciones) >= 2

    def test_variable_entrante_guardada(self):
        """La primera iteración debe tener variable entrante registrada."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        solver = AlgoritmoSimplex(p)
        r = solver.resolver()
        it0 = r.iteraciones[0]
        assert it0.variable_entrante is not None

    def test_explicacion_no_vacia(self):
        """Las iteraciones deben tener explicación."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12"],
        )
        solver = AlgoritmoSimplex(p)
        r = solver.resolver()
        for it in r.iteraciones:
            assert len(it.explicacion) > 0


class TestDosFases:

    def test_problema_con_geq(self):
        """Problema con restricción >= resuelto por Dos Fases."""
        p = parsear_problema_completo(
            "Max Z = 2x1 + 3x2",
            ["x1 + x2 >= 4", "x1 + 3x2 <= 12", "x1 <= 6"],
        )
        solver = DosFases(p)
        r = solver.resolver()
        assert r.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)

    def test_problema_infactible(self):
        """Problema infactible debe retornar EstadoSolucion.INFACTIBLE."""
        p = parsear_problema_completo(
            "Max Z = x1 + x2",
            ["x1 + x2 <= 4", "x1 + x2 >= 6"],
        )
        solver = DosFases(p)
        r = solver.resolver()
        assert r.estado == EstadoSolucion.INFACTIBLE
