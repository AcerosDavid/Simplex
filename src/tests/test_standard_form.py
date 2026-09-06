"""
Pruebas unitarias para la conversión a Forma Estándar.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from algorithms.parser import parsear_problema_completo
from algorithms.forma_estandar import convertir_a_forma_estandar
from models.variable import TipoVariable
from models.restriccion import TipoRestriccion


class TestFormaEstandar:

    def test_solo_leq(self):
        """Solo restricciones <= → solo variables de holgura."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        pe = convertir_a_forma_estandar(p)
        assert not pe.tiene_artificiales
        tipos_aux = [v.tipo for v in pe.variables_auxiliares]
        assert all(t == TipoVariable.HOLGURA for t in tipos_aux)
        assert len(pe.variables_auxiliares) == 2  # s1, s2
        # Todas restricciones deben ser igualdades
        for r in pe.restricciones:
            assert r.tipo == TipoRestriccion.EQ

    def test_geq_agrega_artificial(self):
        """Restricción >= → exceso + artificial."""
        p = parsear_problema_completo(
            "Max Z = 2x1 + 3x2",
            ["x1 + x2 >= 4"],
        )
        pe = convertir_a_forma_estandar(p)
        assert pe.tiene_artificiales
        tipos = [v.tipo for v in pe.variables_auxiliares]
        assert TipoVariable.EXCESO in tipos
        assert TipoVariable.ARTIFICIAL in tipos

    def test_eq_agrega_artificial(self):
        """Restricción = → solo artificial."""
        p = parsear_problema_completo(
            "Max Z = 5x1 + 4x2",
            ["x1 + x2 = 5"],
        )
        pe = convertir_a_forma_estandar(p)
        assert pe.tiene_artificiales
        tipos = [v.tipo for v in pe.variables_auxiliares]
        assert TipoVariable.ARTIFICIAL in tipos
        assert TipoVariable.HOLGURA not in tipos
        assert TipoVariable.EXCESO not in tipos

    def test_base_inicial_correcta(self):
        """La base inicial debe contener holguras/artificiales."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12", "4x1 + 2x2 <= 16"],
        )
        pe = convertir_a_forma_estandar(p)
        assert len(pe.base_inicial) == 2  # s1, s2
        assert "s1" in pe.base_inicial
        assert "s2" in pe.base_inicial

    def test_coef_objetivo_auxiliares_cero(self):
        """Coeficientes de variables auxiliares en objetivo = 0."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12"],
        )
        pe = convertir_a_forma_estandar(p)
        for v in pe.variables_auxiliares:
            assert pe.coef_objetivo.get(v.nombre, 0.0) == 0.0

    def test_pasos_conversion_generados(self):
        """Debe generar pasos de conversión no vacíos."""
        p = parsear_problema_completo(
            "Max Z = 3x1 + 5x2",
            ["2x1 + 3x2 <= 12"],
        )
        pe = convertir_a_forma_estandar(p)
        assert len(pe.pasos_conversion) > 0
