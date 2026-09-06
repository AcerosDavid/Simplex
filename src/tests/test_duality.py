"""
Pruebas unitarias para el algoritmo de dualidad.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from algorithms.parser import parsear_problema_completo
from algorithms.dualidad import AlgoritmoDualidad
from models.problema import TipoOptimizacion
from models.restriccion import TipoRestriccion
from models.resultado import EstadoSolucion


class TestConstruccionDual:

    def test_dual_max_a_min(self):
        """Primal MAX -> Dual MIN."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        dual, pasos = algo.construir_dual()
        assert dual.tipo == TipoOptimizacion.MINIMIZAR
        assert len(dual.variables) == 2  # 2 restricciones -> 2 variables duales
        assert len(dual.restricciones) == 2  # 2 variables -> 2 restricciones duales

    def test_dual_min_a_max(self):
        """Primal MIN -> Dual MAX."""
        p = parsear_problema_completo(
            "Min Z = 2x1 + 3x2",
            ["x1 + x2 >= 4", "2x1 + x2 >= 6"],
        )
        algo = AlgoritmoDualidad(p)
        dual, pasos = algo.construir_dual()
        assert dual.tipo == TipoOptimizacion.MAXIMIZAR

    def test_coef_objetivo_dual(self):
        """Los coeficientes del dual son los RHS del primal."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        dual, _ = algo.construir_dual()
        # RHS primal: 10, 15 -> coefs objetivo dual
        assert abs(dual.coef_objetivo.get("y1", 0) - 10.0) < 1e-8
        assert abs(dual.coef_objetivo.get("y2", 0) - 15.0) < 1e-8

    def test_rhs_dual(self):
        """Los RHS del dual son los coeficientes del objetivo primal."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        dual, _ = algo.construir_dual()
        # Coefs objetivo primal: 3, 5 -> RHS restricciones duales
        rhs_vals = [r.rhs for r in dual.restricciones]
        assert abs(rhs_vals[0] - 3.0) < 1e-8  # Para x1: c1=3
        assert abs(rhs_vals[1] - 5.0) < 1e-8  # Para x2: c2=5

    def test_transpuesta_matriz(self):
        """La matriz del dual es la transpuesta del primal."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        dual, _ = algo.construir_dual()
        # Primal: A = [[2,1],[1,3]], At = [[2,1],[1,3]]
        # Restriccion D1 (para x1): 2*y1 + 1*y2 >= 3
        d1 = dual.restricciones[0]
        assert abs(d1.obtener_coef("y1") - 2.0) < 1e-8
        assert abs(d1.obtener_coef("y2") - 1.0) < 1e-8

    def test_pasos_no_vacios(self):
        """La construccion debe generar pasos explicativos."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        _, pasos = algo.construir_dual()
        assert len(pasos) > 5


class TestResolucionDualidad:

    def test_dualidad_fuerte(self):
        """Z* primal debe ser igual a W* dual para el ejemplo clasico."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        rd = algo.construir_y_resolver()

        assert rd.resultado_primal.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)
        assert rd.resultado_dual.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)
        assert rd.dualidad_fuerte is True
        assert abs(rd.valor_primal - rd.valor_dual) < 1e-4

    def test_holgura_complementaria(self):
        """Las condiciones de holgura complementaria deben cumplirse."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        rd = algo.construir_y_resolver()

        if rd.dualidad_fuerte:
            assert rd.holgura_complementaria.todas_cumplen

    def test_correspondencia_generada(self):
        """La correspondencia Primal-Dual debe contener entradas."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        )
        algo = AlgoritmoDualidad(p)
        rd = algo.construir_y_resolver()
        assert len(rd.correspondencia.filas) > 5

    def test_teoremas_explicacion(self):
        """La explicacion de teoremas debe ser texto no vacio."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + x2 <= 10"],
        )
        algo = AlgoritmoDualidad(p)
        rd = algo.construir_y_resolver()
        assert len(rd.teoremas_explicacion) > 100
