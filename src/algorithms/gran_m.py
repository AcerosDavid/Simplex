"""
Método de la Gran M para problemas con variables artificiales.

Penaliza las variables artificiales con un coeficiente -M (max) o +M (min)
en la función objetivo, donde M es un número muy grande.

La lógica principal ya está integrada en AlgoritmoSimplex._resolver_con_gran_m().
Este módulo provee la clase GranM como interfaz explícita.
"""
from models.problema import Problema
from models.resultado import Resultado
from algorithms.simplex import AlgoritmoSimplex
from algorithms.validaciones import validar_problema
from algorithms.forma_estandar import convertir_a_forma_estandar


class GranM:
    """
    Interfaz para resolver mediante el método de la Gran M.

    Uso::
        solver = GranM(problema)
        resultado = solver.resolver()
    """

    def __init__(self, problema: Problema, valor_m: float = 1e6) -> None:
        self.problema = problema
        self.valor_m = valor_m
        self._resultado: Resultado = Resultado(metodo="Gran M")

    def resolver(self) -> Resultado:
        """Delega al AlgoritmoSimplex con penalización M."""
        from config.config import APP_CONFIG
        APP_CONFIG.big_m_value = self.valor_m

        solver = AlgoritmoSimplex(self.problema)
        resultado = solver.resolver()
        resultado.metodo = f"Gran M (M = {self.valor_m:.0e})"
        return resultado
