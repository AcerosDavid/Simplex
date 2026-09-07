"""
Método de las Dos Fases para problemas con variables artificiales.

Fase I:  Min W = a1 + a2 + ...
         Si W* = 0 → solución factible encontrada → continuar con Fase II.
         Si W* > 0 → problema infactible.

Fase II: Recuperar la función objetivo original y resolver desde la base factible.
"""
from __future__ import annotations

import copy
from typing import List, Optional, Tuple, Dict

import numpy as np

from models.problema import Problema, TipoOptimizacion
from models.resultado import EstadoSolucion, Iteracion, OperacionFila, Resultado
from models.variable import TipoVariable
from algorithms.forma_estandar import ProblemaEstandar, convertir_a_forma_estandar
from algorithms.validaciones import validar_problema
from algorithms.simplex import AlgoritmoSimplex, _EPSILON, _MAX_ITERACIONES
from utils.format_numbers import limpiar_cero, format_number


class DosFases:
    """
    Implementa el método de las Dos Fases.

    Uso::
        solver = DosFases(problema)
        resultado = solver.resolver()
    """

    def __init__(self, problema: Problema, modo_algebraico: bool = False) -> None:
        self.problema = problema
        self.modo_algebraico = modo_algebraico
        self.resultado = Resultado(metodo="Dos Fases")

    def resolver(self) -> Resultado:
        """Resuelve el problema usando el método de las Dos Fases."""
        es_valido, errores = validar_problema(self.problema)
        if not es_valido:
            self.resultado.estado = EstadoSolucion.INFACTIBLE
            self.resultado.mensaje = "Problema inválido:\n" + "\n".join(errores)
            return self.resultado

        pe = convertir_a_forma_estandar(self.problema)

        if not pe.tiene_artificiales:
            # Sin artificiales → usar Simplex directo
            solver = AlgoritmoSimplex(self.problema, modo_algebraico=self.modo_algebraico)
            return solver.resolver()

        # ─── FASE I ───────────────────────────────────────────────────────
        tableau_f1, nombres_cols, cj_f1, base_vars, base_coefs = \
            self._construir_tableau_fase1(pe)

        iteraciones_f1 = self._ejecutar_simplex(
            tableau_f1, nombres_cols, cj_f1, base_vars, base_coefs,
            pe, tipo_opt=TipoOptimizacion.MINIMIZAR, fase=1,
        )

        # Verificar W* = 0
        w_star = limpiar_cero(float(
            np.array(base_coefs) @ tableau_f1[:, -1]
        ))

        for it in iteraciones_f1:
            it.fase = 1

        if abs(w_star) > _EPSILON:
            self.resultado.estado = EstadoSolucion.INFACTIBLE
            self.resultado.mensaje = (
                f"⚠ El problema es INFACTIBLE.\n"
                f"W* = {format_number(w_star)} ≠ 0 al final de la Fase I.\n"
                "No existe una solución factible para el problema original."
            )
            self.resultado.iteraciones = iteraciones_f1
            return self.resultado

        # ─── FASE II ──────────────────────────────────────────────────────
        tableau_f2, cj_f2 = self._preparar_fase2(
            tableau_f1, nombres_cols, base_vars, pe
        )

        base_coefs_f2 = [
            pe.coef_objetivo.get(bv, 0.0) for bv in base_vars
        ]

        iteraciones_f2 = self._ejecutar_simplex(
            tableau_f2, nombres_cols, cj_f2, base_vars, base_coefs_f2,
            pe, tipo_opt=pe.tipo, fase=2,
        )

        for it in iteraciones_f2:
            it.fase = 2

        # Resultado final
        todas_iteraciones = iteraciones_f1 + iteraciones_f2

        zj_final, cj_zj_final = self._calcular_zj_cjzj(
            tableau_f2, cj_f2, base_coefs_f2, pe
        )

        estado = self._verificar_optimalidad(cj_zj_final, pe)
        estado = self._detectar_multiples(
            cj_zj_final, nombres_cols, base_vars, estado
        )

        self.resultado.estado = estado
        self.resultado.iteraciones = todas_iteraciones
        self.resultado.num_iteraciones = len(todas_iteraciones) - 1
        self.resultado.variables_base_final = list(base_vars)
        self._extraer_solucion(tableau_f2, nombres_cols, base_vars, pe, cj_f2)
        self.resultado.mensaje = self._mensaje_solucion(estado)

        return self.resultado

    # ──────────────────────────────────────────────────────────────────────
    #  Construcción del tableau Fase I
    # ──────────────────────────────────────────────────────────────────────

    def _construir_tableau_fase1(
        self, pe: ProblemaEstandar
    ) -> Tuple[np.ndarray, List[str], List[float], List[str], List[float]]:
        """Crea el tableau para la Fase I con función objetivo W = Σ artificiales."""
        m = pe.num_restricciones
        nombres_vars = pe.nombres_variables
        n = len(nombres_vars)

        tableau = np.zeros((m, n + 1), dtype=float)
        for i, rest in enumerate(pe.restricciones):
            for j, nombre in enumerate(nombres_vars):
                tableau[i, j] = rest.obtener_coef(nombre)
            tableau[i, n] = rest.rhs

        nombres_cols = nombres_vars + ["RHS"]

        # Fase I: cj = 1 para artificiales, 0 para el resto
        cj_f1 = []
        for nombre in nombres_vars:
            es_artificial = any(
                v.nombre == nombre and v.tipo == TipoVariable.ARTIFICIAL
                for v in pe.variables_auxiliares
            )
            cj_f1.append(1.0 if es_artificial else 0.0)

        base_vars = list(pe.base_inicial)
        base_coefs = [cj_f1[nombres_vars.index(bv)] for bv in base_vars]

        return tableau, nombres_cols, cj_f1, base_vars, base_coefs

    # ──────────────────────────────────────────────────────────────────────
    #  Preparar Fase II
    # ──────────────────────────────────────────────────────────────────────

    def _preparar_fase2(
        self,
        tableau: np.ndarray,
        nombres_cols: List[str],
        base_vars: List[str],
        pe: ProblemaEstandar,
    ) -> Tuple[np.ndarray, List[float]]:
        """
        Prepara el tableau para la Fase II eliminando columnas de artificiales
        que no están en la base y restaurando la función objetivo original.
        """
        nombres_vars = nombres_cols[:-1]

        # Mantener solo columnas sin artificiales (o artificiales en base con valor 0)
        cols_mantener = []
        nombres_mantener = []
        for j, nombre in enumerate(nombres_vars):
            es_artificial = any(
                v.nombre == nombre and v.tipo == TipoVariable.ARTIFICIAL
                for v in pe.variables_auxiliares
            )
            if not es_artificial or nombre in base_vars:
                cols_mantener.append(j)
                nombres_mantener.append(nombre)

        # Reconstruir tableau sin columnas artificiales innecesarias
        cols_idx = cols_mantener + [len(nombres_vars)]  # + RHS
        tableau_f2 = tableau[:, cols_idx].copy()

        # Actualizar nombres_cols
        nombres_cols.clear()
        nombres_cols.extend(nombres_mantener + ["RHS"])

        # Función objetivo original
        cj_f2 = [pe.coef_objetivo.get(nombre, 0.0) for nombre in nombres_mantener]

        return tableau_f2, cj_f2

    # ──────────────────────────────────────────────────────────────────────
    #  Motor Simplex reutilizable
    # ──────────────────────────────────────────────────────────────────────

    def _ejecutar_simplex(
        self,
        tableau: np.ndarray,
        nombres_cols: List[str],
        cj: List[float],
        base_vars: List[str],
        base_coefs: List[float],
        pe: ProblemaEstandar,
        tipo_opt: TipoOptimizacion,
        fase: int,
    ) -> List[Iteracion]:
        """Ejecuta el Simplex sobre un tableau dado y devuelve las iteraciones."""
        _pe_fake = copy.copy(pe)
        _pe_fake.tipo = tipo_opt

        iteraciones: List[Iteracion] = []
        it0 = self._crear_iteracion(0, tableau, nombres_cols, cj, list(base_vars), list(base_coefs))
        it0.fase = fase
        it0.explicacion = self._explicacion_fase(fase, tipo_opt)
        iteraciones.append(it0)

        helper = _SimplexHelper()

        num_iter = 0
        while num_iter < _MAX_ITERACIONES:
            num_iter += 1
            zj, cj_zj = helper.calcular_zj_cjzj(tableau, cj, base_coefs)

            es_optimo = helper.verificar_optimalidad(cj_zj, tipo_opt)
            if es_optimo:
                iteraciones[-1].zj = [limpiar_cero(v) for v in zj.tolist()]
                iteraciones[-1].cj_zj = [limpiar_cero(v) for v in cj_zj.tolist()]
                break

            col_piv = helper.seleccionar_entrante(cj_zj, tipo_opt)
            if col_piv is None:
                break

            fila_piv, razones = helper.prueba_razon_minima(tableau, col_piv)
            if fila_piv is None:
                break

            var_ent = nombres_cols[col_piv]
            var_sal = base_vars[fila_piv]
            elem_piv = tableau[fila_piv, col_piv]

            iteraciones[-1].zj = [limpiar_cero(v) for v in zj.tolist()]
            iteraciones[-1].cj_zj = [limpiar_cero(v) for v in cj_zj.tolist()]
            iteraciones[-1].variable_entrante = var_ent
            iteraciones[-1].variable_saliente = var_sal
            iteraciones[-1].col_pivote = col_piv
            iteraciones[-1].fila_pivote = fila_piv
            iteraciones[-1].elemento_pivote = elem_piv
            iteraciones[-1].razones = [limpiar_cero(r) if r is not None else None for r in razones]
            iteraciones[-1].explicacion += self._explicacion_pivote(
                var_ent, var_sal, elem_piv, razones, list(base_vars), nombres_cols, tableau, tipo_opt
            )

            operaciones = helper.pivotear(tableau, fila_piv, col_piv)
            base_vars[fila_piv] = var_ent
            base_coefs[fila_piv] = cj[col_piv]

            it_nueva = self._crear_iteracion(
                num_iter, tableau, nombres_cols, cj, list(base_vars), list(base_coefs)
            )
            it_nueva.operaciones = operaciones
            it_nueva.fase = fase
            iteraciones.append(it_nueva)

        return iteraciones

    def _crear_iteracion(self, numero, tableau, nombres_cols, cj, base_vars, base_coefs):
        it = Iteracion(numero=numero)
        it.tabla = [[limpiar_cero(v) for v in fila.tolist()] for fila in tableau]
        it.nombres_columnas = list(nombres_cols)
        it.cj = list(cj) + [0.0]
        it.variables_base = list(base_vars)
        it.coefs_base = list(base_coefs)
        it.modo_algebraico = self.modo_algebraico
        return it

    def _calcular_zj_cjzj(self, tableau, cj, base_coefs, pe):
        cb = np.array(base_coefs, dtype=float)
        n_vars = tableau.shape[1] - 1
        zj = np.array([float(cb @ tableau[:, j]) for j in range(n_vars + 1)])
        cj_arr = np.array(cj + [0.0])
        return zj, cj_arr - zj

    def _verificar_optimalidad(self, cj_zj, pe):
        n = len(cj_zj) - 1
        vals = cj_zj[:n]
        if pe.tipo == TipoOptimizacion.MAXIMIZAR:
            if all(v <= _EPSILON for v in vals):
                return EstadoSolucion.OPTIMA
        else:
            if all(v >= -_EPSILON for v in vals):
                return EstadoSolucion.OPTIMA
        return EstadoSolucion.SIN_RESOLVER

    def _detectar_multiples(self, cj_zj, nombres_cols, base_vars, estado):
        n = len(cj_zj) - 1
        for j in range(n):
            if nombres_cols[j] not in base_vars and abs(cj_zj[j]) < _EPSILON:
                return EstadoSolucion.MULTIPLES
        return estado

    def _extraer_solucion(self, tableau, nombres_cols, base_vars, pe, cj):
        nombres_vars = nombres_cols[:-1]
        valores = {n: 0.0 for n in nombres_vars}
        for i, bv in enumerate(base_vars):
            valores[bv] = limpiar_cero(tableau[i, -1])
        self.resultado.valores_variables = valores
        cb = np.array([pe.coef_objetivo.get(bv, 0.0) for bv in base_vars])
        z = limpiar_cero(float(cb @ tableau[:, -1]))
        self.resultado.valor_objetivo = z

    def _mensaje_solucion(self, estado):
        r = self.resultado
        if estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES):
            lines = ["✓ SOLUCIÓN ÓPTIMA (Dos Fases)", ""]
            for n, v in r.valores_variables.items():
                lines.append(f"  {n} = {format_number(v)}")
            lines.append(f"\n  Z* = {format_number(r.valor_objetivo)}")
            return "\n".join(lines)
        return str(estado.value)

    def _explicacion_fase(self, fase, tipo_opt):
        if fase == 1:
            return (
                "═" * 55 + "\n"
                "  FASE I — Encontrar solución factible\n"
                "═" * 55 + "\n\n"
                "  Se construye un problema auxiliar:\n"
                "  Min W = Σ (variables artificiales)\n\n"
                "  Si W* = 0 al terminar → existe solución factible.\n"
                "  Si W* > 0 → el problema original es INFACTIBLE.\n"
            )
        else:
            return (
                "═" * 55 + "\n"
                "  FASE II — Optimizar función objetivo original\n"
                "═" * 55 + "\n\n"
                "  Se recupera la función objetivo original.\n"
                "  Las variables artificiales se eliminan del tableau.\n"
                "  Se continúa el Simplex desde la base factible de Fase I.\n"
            )

    def _explicacion_pivote(self, var_ent, var_sal, elem_piv, razones, base_vars, nombres_cols, tableau, tipo_opt):
        lines = [
            f"\n  Variable entrante: {var_ent}",
            f"  Variable saliente: {var_sal}",
            f"  Elemento pivote:   {format_number(elem_piv)}",
            "  Razones:",
        ]
        for i, r in enumerate(razones):
            bv = base_vars[i] if i < len(base_vars) else f"R{i+1}"
            if r is not None:
                lines.append(f"    R{i+1} ({bv}): {format_number(r)}")
            else:
                lines.append(f"    R{i+1} ({bv}): no válida")
        return "\n".join(lines)


class _SimplexHelper:
    """Helper interno con las operaciones básicas del Simplex."""

    def calcular_zj_cjzj(self, tableau, cj, base_coefs):
        cb = np.array(base_coefs, dtype=float)
        n_vars = tableau.shape[1] - 1
        zj = np.array([float(cb @ tableau[:, j]) for j in range(n_vars + 1)])
        cj_arr = np.array(list(cj) + [0.0])
        return zj, cj_arr - zj

    def verificar_optimalidad(self, cj_zj, tipo_opt):
        n = len(cj_zj) - 1
        vals = cj_zj[:n]
        if tipo_opt == TipoOptimizacion.MAXIMIZAR:
            return all(v <= _EPSILON for v in vals)
        else:
            return all(v >= -_EPSILON for v in vals)

    def seleccionar_entrante(self, cj_zj, tipo_opt):
        n = len(cj_zj) - 1
        if tipo_opt == TipoOptimizacion.MAXIMIZAR:
            col = int(np.argmax(cj_zj[:n]))
            return col if cj_zj[col] > _EPSILON else None
        else:
            col = int(np.argmin(cj_zj[:n]))
            return col if cj_zj[col] < -_EPSILON else None

    def prueba_razon_minima(self, tableau, col_piv):
        m = tableau.shape[0]
        razones = []
        min_r = float('inf')
        fila_piv = None
        for i in range(m):
            coef = tableau[i, col_piv]
            rhs = tableau[i, -1]
            if coef > _EPSILON:
                r = rhs / coef
                razones.append(r)
                if r < min_r - _EPSILON:
                    min_r = r
                    fila_piv = i
            else:
                razones.append(None)
        return fila_piv, razones

    def pivotear(self, tableau, fila_piv, col_piv):
        operaciones = []
        elem_piv = tableau[fila_piv, col_piv]
        tableau[fila_piv] = tableau[fila_piv] / elem_piv
        for j in range(tableau.shape[1]):
            tableau[fila_piv, j] = limpiar_cero(tableau[fila_piv, j])
        operaciones.append(OperacionFila(
            descripcion=f"R{fila_piv+1} = R{fila_piv+1} / {format_number(elem_piv)}",
            fila_resultado=tableau[fila_piv].tolist(),
        ))
        for i in range(tableau.shape[0]):
            if i == fila_piv:
                continue
            factor = tableau[i, col_piv]
            if abs(factor) < _EPSILON:
                continue
            tableau[i] = tableau[i] - factor * tableau[fila_piv]
            for j in range(tableau.shape[1]):
                tableau[i, j] = limpiar_cero(tableau[i, j])
            signo = "-" if factor > 0 else "+"
            operaciones.append(OperacionFila(
                descripcion=f"R{i+1} = R{i+1} {signo} {format_number(abs(factor))}·R{fila_piv+1}",
                fila_resultado=tableau[i].tolist(),
            ))
        return operaciones
