"""
Implementación del algoritmo Simplex para Programación Lineal.

Implementa el Simplex de tableau (Big Tableau) de forma educativa:
- Construye la tabla inicial a partir de la forma estándar.
- Calcula Zj y Cj-Zj en cada iteración.
- Selecciona variable entrante (criterio de optimalidad).
- Realiza prueba de razón mínima para variable saliente.
- Ejecuta las operaciones de fila del pivoteo.
- Guarda el historial completo de cada iteración con explicaciones.
- Detecta: solución óptima, ilimitada, infactible, múltiples soluciones.

NO usa scipy.optimize.linprog ni ningún solver externo para las iteraciones.
"""
from __future__ import annotations

import copy
from typing import List, Optional, Tuple, Dict

import numpy as np

from models.problema import Problema, TipoOptimizacion
from models.resultado import (
    EstadoSolucion,
    Iteracion,
    OperacionFila,
    Resultado,
)
from algorithms.forma_estandar import ProblemaEstandar, convertir_a_forma_estandar
from algorithms.validaciones import validar_problema
from utils.format_numbers import limpiar_cero, format_number


# ─────────────────────────────────────────────────────────────────────────────
#  Constantes
# ─────────────────────────────────────────────────────────────────────────────

_EPSILON = 1e-10          # Tolerancia para ceros
_MAX_ITERACIONES = 200    # Límite anti-bucle infinito


# ─────────────────────────────────────────────────────────────────────────────
#  Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class AlgoritmoSimplex:
    """
    Motor del algoritmo Simplex educativo.

    Uso típico::

        solver = AlgoritmoSimplex(problema)
        resultado = solver.resolver()
        for it in resultado.iteraciones:
            print(it.explicacion)
    """

    def __init__(self, problema: Problema, modo_algebraico: bool = False) -> None:
        self.problema = problema
        self.modo_algebraico = modo_algebraico
        self.resultado = Resultado(metodo="Simplex Primal")
        self._cj_original: Optional[List[float]] = None

    # ──────────────────────────────────────────────────────────────────────
    #  Punto de entrada público
    # ──────────────────────────────────────────────────────────────────────

    def resolver(self) -> Resultado:
        """
        Resuelve el problema y devuelve el Resultado con todas las iteraciones.
        """
        # 1. Validar
        es_valido, errores = validar_problema(self.problema)
        if not es_valido:
            self.resultado.estado = EstadoSolucion.INFACTIBLE
            self.resultado.mensaje = "Problema inválido:\n" + "\n".join(errores)
            return self.resultado

        # 2. Convertir a forma estándar
        pe = convertir_a_forma_estandar(self.problema)

        # 3. Si hay artificiales → delegar a Dos Fases o Gran M
        #    (en esta fase se usa Gran M interno simplificado)
        if pe.tiene_artificiales:
            return self._resolver_con_gran_m(pe)
        else:
            return self._resolver_simplex_puro(pe)

    # ──────────────────────────────────────────────────────────────────────
    #  Simplex sin variables artificiales
    # ──────────────────────────────────────────────────────────────────────

    def _resolver_simplex_puro(self, pe: ProblemaEstandar) -> Resultado:
        """Simplex clásico para problemas con solo holguras en la base inicial."""

        tableau, nombres_cols, cj, base_vars, base_coefs = self._construir_tableau(pe)
        iteraciones: List[Iteracion] = []

        # Iteración 0 — tabla inicial
        it0 = self._crear_iteracion(
            numero=0,
            tableau=tableau,
            nombres_cols=nombres_cols,
            cj=cj,
            base_vars=base_vars,
            base_coefs=base_coefs,
            pe=pe,
        )
        it0.explicacion = self._explicacion_tabla_inicial(pe)
        iteraciones.append(it0)

        num_iter = 0
        while num_iter < _MAX_ITERACIONES:
            num_iter += 1

            zj, cj_zj = self._calcular_zj_cjzj(tableau, cj, base_coefs, pe)

            # Criterio de parada
            estado_parada = self._verificar_optimalidad(cj_zj, pe)
            if estado_parada == EstadoSolucion.OPTIMA:
                # Actualizar última iteración con los vectores finales
                iteraciones[-1].zj = [limpiar_cero(v) for v in zj.tolist()]
                iteraciones[-1].cj_zj = [limpiar_cero(v) for v in cj_zj.tolist()]
                break

            # Variable entrante
            col_piv = self._seleccionar_entrante(cj_zj, pe)
            if col_piv is None:
                estado_parada = EstadoSolucion.OPTIMA
                break

            # Prueba de razón mínima → variable saliente
            fila_piv, razones = self._prueba_razon_minima(tableau, col_piv)
            if fila_piv is None:
                estado_parada = EstadoSolucion.ILIMITADO
                var_ent = nombres_cols[col_piv]
                self.resultado.estado = EstadoSolucion.ILIMITADO
                self.resultado.mensaje = (
                    f"⚠ El problema es ilimitado.\n"
                    f"La variable {var_ent} puede aumentar indefinidamente "
                    f"sin violar las restricciones y mejorando la función objetivo."
                )
                self.resultado.iteraciones = iteraciones
                return self.resultado

            var_ent = nombres_cols[col_piv]
            var_sal = base_vars[fila_piv]
            elem_piv = tableau[fila_piv, col_piv]

            # Construir iteración con info de pivote
            it = self._crear_iteracion(
                numero=num_iter - 1,
                tableau=copy.deepcopy(tableau),
                nombres_cols=nombres_cols,
                cj=cj,
                base_vars=list(base_vars),
                base_coefs=list(base_coefs),
                pe=pe,
            )
            it.zj = [limpiar_cero(v) for v in zj.tolist()]
            it.cj_zj = [limpiar_cero(v) for v in cj_zj.tolist()]
            it.variable_entrante = var_ent
            it.variable_saliente = var_sal
            it.col_pivote = col_piv
            it.fila_pivote = fila_piv
            it.elemento_pivote = elem_piv
            it.razones = [limpiar_cero(r) if r is not None else None for r in razones]
            # Actualizar la iteracion anterior (la que tenia la tabla pre-pivote)
            iteraciones[-1].variable_entrante = var_ent
            iteraciones[-1].variable_saliente = var_sal
            iteraciones[-1].col_pivote = col_piv
            iteraciones[-1].fila_pivote = fila_piv
            iteraciones[-1].elemento_pivote = elem_piv
            iteraciones[-1].razones = it.razones
            iteraciones[-1].zj = it.zj
            iteraciones[-1].cj_zj = it.cj_zj
            iteraciones[-1].explicacion = self._explicacion_iteracion(
                iteraciones[-1], pe, nombres_cols
            )

            # Realizar el pivoteo
            operaciones = self._pivotear(tableau, fila_piv, col_piv, nombres_cols)

            # Actualizar base
            base_vars[fila_piv] = var_ent
            base_coefs[fila_piv] = cj[col_piv]

            # Guardar tabla resultante como nueva iteración
            it_nueva = self._crear_iteracion(
                numero=num_iter,
                tableau=copy.deepcopy(tableau),
                nombres_cols=nombres_cols,
                cj=cj,
                base_vars=list(base_vars),
                base_coefs=list(base_coefs),
                pe=pe,
            )
            it_nueva.operaciones = operaciones
            iteraciones.append(it_nueva)

        else:
            estado_parada = EstadoSolucion.INFACTIBLE
            self.resultado.mensaje = "Se alcanzó el límite máximo de iteraciones."

        # Calcular Zj/Cj-Zj de la última tabla
        zj_final, cj_zj_final = self._calcular_zj_cjzj(tableau, cj, base_coefs, pe)
        iteraciones[-1].zj = [limpiar_cero(v) for v in zj_final.tolist()]
        iteraciones[-1].cj_zj = [limpiar_cero(v) for v in cj_zj_final.tolist()]
        iteraciones[-1].explicacion = self._explicacion_solucion_final(
            iteraciones[-1], pe, estado_parada
        )

        # Detectar soluciones múltiples
        if estado_parada == EstadoSolucion.OPTIMA:
            estado_parada = self._detectar_multiples(
                cj_zj_final, nombres_cols, base_vars, estado_parada
            )

        # Construir resultado final
        self.resultado.estado = estado_parada
        self.resultado.iteraciones = iteraciones
        self.resultado.num_iteraciones = len(iteraciones) - 1
        self.resultado.variables_base_final = list(base_vars)

        if estado_parada in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES):
            self._extraer_solucion(tableau, nombres_cols, base_vars, pe)
            self.resultado.mensaje = self._mensaje_solucion(estado_parada)

        return self.resultado

    # ──────────────────────────────────────────────────────────────────────
    #  Gran M (para problemas con artificiales)
    # ──────────────────────────────────────────────────────────────────────

    def _resolver_con_gran_m(self, pe: ProblemaEstandar) -> Resultado:
        """
        Resuelve usando el método de la Gran M.
        Las variables artificiales reciben coeficiente -M (max) o +M (min).
        """
        from config.config import APP_CONFIG
        M = APP_CONFIG.big_m_value

        tableau, nombres_cols, cj, base_vars, base_coefs = self._construir_tableau(pe)

        # Asignar penalización M a las artificiales en cj
        for j, nombre in enumerate(nombres_cols[:-1]):  # excluir RHS
            from models.variable import TipoVariable
            var = pe.problema_original.obtener_variable(nombre)
            if var is None:
                # buscar en auxiliares
                for v in pe.variables_auxiliares:
                    if v.nombre == nombre:
                        var = v
                        break
            if var is not None and var.tipo == TipoVariable.ARTIFICIAL:
                if self.modo_algebraico:
                    # En modo algebraico, los signos se invierten
                    if pe.tipo == TipoOptimizacion.MAXIMIZAR:
                        cj[j] = M   # negado de -M
                    else:
                        cj[j] = -M  # negado de +M
                else:
                    if pe.tipo == TipoOptimizacion.MAXIMIZAR:
                        cj[j] = -M
                    else:
                        cj[j] = M
                # Actualizar coef_base si la artificial está en la base
                for k, bv in enumerate(base_vars):
                    if bv == nombre:
                        base_coefs[k] = cj[j]

        iteraciones: List[Iteracion] = []
        it0 = self._crear_iteracion(
            numero=0,
            tableau=tableau,
            nombres_cols=nombres_cols,
            cj=cj,
            base_vars=base_vars,
            base_coefs=base_coefs,
            pe=pe,
        )
        it0.explicacion = self._explicacion_tabla_inicial(pe, gran_m=True, M=M)
        iteraciones.append(it0)

        num_iter = 0
        while num_iter < _MAX_ITERACIONES:
            num_iter += 1
            zj, cj_zj = self._calcular_zj_cjzj(tableau, cj, base_coefs, pe)

            estado_parada = self._verificar_optimalidad(cj_zj, pe)
            if estado_parada == EstadoSolucion.OPTIMA:
                iteraciones[-1].zj = [limpiar_cero(v) for v in zj.tolist()]
                iteraciones[-1].cj_zj = [limpiar_cero(v) for v in cj_zj.tolist()]
                break

            col_piv = self._seleccionar_entrante(cj_zj, pe)
            if col_piv is None:
                break

            fila_piv, razones = self._prueba_razon_minima(tableau, col_piv)
            if fila_piv is None:
                self.resultado.estado = EstadoSolucion.ILIMITADO
                self.resultado.mensaje = "⚠ El problema es ilimitado."
                self.resultado.iteraciones = iteraciones
                return self.resultado

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
            iteraciones[-1].explicacion = self._explicacion_iteracion(
                iteraciones[-1], pe, nombres_cols
            )

            operaciones = self._pivotear(tableau, fila_piv, col_piv, nombres_cols)
            base_vars[fila_piv] = var_ent
            base_coefs[fila_piv] = cj[col_piv]

            it_nueva = self._crear_iteracion(
                numero=num_iter,
                tableau=copy.deepcopy(tableau),
                nombres_cols=nombres_cols,
                cj=cj,
                base_vars=list(base_vars),
                base_coefs=list(base_coefs),
                pe=pe,
            )
            it_nueva.operaciones = operaciones
            iteraciones.append(it_nueva)

        else:
            self.resultado.estado = EstadoSolucion.INFACTIBLE
            self.resultado.mensaje = "Límite de iteraciones alcanzado."
            self.resultado.iteraciones = iteraciones
            return self.resultado

        # Verificar si quedan artificiales en la base con valor > 0
        from models.variable import TipoVariable
        for i, bv in enumerate(base_vars):
            for v in pe.variables_auxiliares:
                if v.nombre == bv and v.tipo == TipoVariable.ARTIFICIAL:
                    rhs_val = tableau[i, -1]
                    if abs(rhs_val) > _EPSILON:
                        self.resultado.estado = EstadoSolucion.INFACTIBLE
                        self.resultado.mensaje = (
                            "⚠ El problema es infactible.\n"
                            "Las variables artificiales no pudieron salir de la base, "
                            "lo que indica que no existe región factible."
                        )
                        self.resultado.iteraciones = iteraciones
                        return self.resultado

        # Calcular Zj/Cj-Zj final
        zj_final, cj_zj_final = self._calcular_zj_cjzj(tableau, cj, base_coefs, pe)
        iteraciones[-1].zj = [limpiar_cero(v) for v in zj_final.tolist()]
        iteraciones[-1].cj_zj = [limpiar_cero(v) for v in cj_zj_final.tolist()]

        estado_parada = EstadoSolucion.OPTIMA
        iteraciones[-1].explicacion = self._explicacion_solucion_final(
            iteraciones[-1], pe, estado_parada
        )

        estado_parada = self._detectar_multiples(cj_zj_final, nombres_cols, base_vars, estado_parada)

        self.resultado.estado = estado_parada
        self.resultado.iteraciones = iteraciones
        self.resultado.num_iteraciones = len(iteraciones) - 1
        self.resultado.variables_base_final = list(base_vars)
        self._extraer_solucion(tableau, nombres_cols, base_vars, pe)
        self.resultado.mensaje = self._mensaje_solucion(estado_parada)

        return self.resultado

    # ──────────────────────────────────────────────────────────────────────
    #  Construcción del tableau
    # ──────────────────────────────────────────────────────────────────────

    def _construir_tableau(
        self, pe: ProblemaEstandar
    ) -> Tuple[np.ndarray, List[str], List[float], List[str], List[float]]:
        """
        Construye el tableau inicial numpy.

        Returns:
            tableau: ndarray (m × n+1)  donde n = num_variables, +1 = RHS
            nombres_cols: lista de nombres de columnas (variables + 'RHS')
            cj: lista de coeficientes objetivo para cada columna (sin RHS)
            base_vars: nombres de variables en la base
            base_coefs: coeficientes objetivo de las variables en base
        """
        m = pe.num_restricciones
        nombres_vars = pe.nombres_variables  # sin RHS
        n = len(nombres_vars)

        tableau = np.zeros((m, n + 1), dtype=float)

        for i, rest in enumerate(pe.restricciones):
            for j, nombre in enumerate(nombres_vars):
                tableau[i, j] = rest.obtener_coef(nombre)
            tableau[i, n] = rest.rhs  # RHS

        nombres_cols = nombres_vars + ["RHS"]

        cj = [pe.coef_objetivo.get(nombre, 0.0) for nombre in nombres_vars]

        # Construir base inicial
        base_vars: List[str] = []
        base_coefs: List[float] = []
        for nombre_base in pe.base_inicial:
            base_vars.append(nombre_base)
            base_coefs.append(pe.coef_objetivo.get(nombre_base, 0.0))

        # Modo Algebraico: negar coeficientes de la función objetivo
        if self.modo_algebraico:
            self._cj_original = list(cj)
            cj = [-c for c in cj]
            base_coefs = [-c for c in base_coefs]

        return tableau, nombres_cols, cj, base_vars, base_coefs

    # ──────────────────────────────────────────────────────────────────────
    #  Cálculo Zj y Cj-Zj
    # ──────────────────────────────────────────────────────────────────────

    def _calcular_zj_cjzj(
        self,
        tableau: np.ndarray,
        cj: List[float],
        base_coefs: List[float],
        pe: ProblemaEstandar,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula los vectores Zj y Cj-Zj.

        Zj[j] = sum(base_coefs[i] * tableau[i,j])  para cada columna j
        Cj-Zj[j] = cj[j] - Zj[j]
        """
        cb = np.array(base_coefs, dtype=float)
        n_vars = tableau.shape[1] - 1  # excluir RHS

        zj = np.zeros(n_vars + 1)
        for j in range(n_vars + 1):
            zj[j] = float(cb @ tableau[:, j])

        cj_arr = np.array(cj + [0.0])  # 0 para la columna RHS
        cj_zj = cj_arr - zj

        return zj, cj_zj

    # ──────────────────────────────────────────────────────────────────────
    #  Criterio de optimalidad
    # ──────────────────────────────────────────────────────────────────────

    def _verificar_optimalidad(
        self, cj_zj: np.ndarray, pe: ProblemaEstandar
    ) -> EstadoSolucion:
        """
        Verifica si se cumple el criterio de optimalidad.

        Modo Tabular:
            Maximización: óptimo cuando todos Cj-Zj <= 0
            Minimización: óptimo cuando todos Cj-Zj >= 0
        Modo Algebraico (Cj negados):
            Maximización: óptimo cuando todos Cj-Zj >= 0
            Minimización: óptimo cuando todos Cj-Zj <= 0
        """
        n_vars = len(cj_zj) - 1  # excluir RHS
        valores = cj_zj[:n_vars]

        if pe.tipo == TipoOptimizacion.MAXIMIZAR:
            if self.modo_algebraico:
                if all(v >= -_EPSILON for v in valores):
                    return EstadoSolucion.OPTIMA
            else:
                if all(v <= _EPSILON for v in valores):
                    return EstadoSolucion.OPTIMA
        else:
            if self.modo_algebraico:
                if all(v <= _EPSILON for v in valores):
                    return EstadoSolucion.OPTIMA
            else:
                if all(v >= -_EPSILON for v in valores):
                    return EstadoSolucion.OPTIMA

        return EstadoSolucion.SIN_RESOLVER

    # ──────────────────────────────────────────────────────────────────────
    #  Selección de variable entrante
    # ──────────────────────────────────────────────────────────────────────

    def _seleccionar_entrante(
        self, cj_zj: np.ndarray, pe: ProblemaEstandar
    ) -> Optional[int]:
        """
        Regla de Dantzig: selecciona la variable entrante.

        Modo Tabular:
            Maximización: columna con mayor Cj-Zj positivo.
            Minimización: columna con menor Cj-Zj negativo (más negativo).
        Modo Algebraico (Cj negados):
            Maximización: columna con Cj-Zj más negativo (mínimo).
            Minimización: columna con Cj-Zj más positivo (máximo).
        """
        n_vars = len(cj_zj) - 1  # excluir RHS

        if pe.tipo == TipoOptimizacion.MAXIMIZAR:
            if self.modo_algebraico:
                col = int(np.argmin(cj_zj[:n_vars]))
                if cj_zj[col] >= -_EPSILON:
                    return None
            else:
                col = int(np.argmax(cj_zj[:n_vars]))
                if cj_zj[col] <= _EPSILON:
                    return None
        else:
            if self.modo_algebraico:
                col = int(np.argmax(cj_zj[:n_vars]))
                if cj_zj[col] <= _EPSILON:
                    return None
            else:
                col = int(np.argmin(cj_zj[:n_vars]))
                if cj_zj[col] >= -_EPSILON:
                    return None

        return col

    # ──────────────────────────────────────────────────────────────────────
    #  Prueba de razón mínima
    # ──────────────────────────────────────────────────────────────────────

    def _prueba_razon_minima(
        self, tableau: np.ndarray, col_piv: int
    ) -> Tuple[Optional[int], List[Optional[float]]]:
        """
        Determina la fila pivote mediante la prueba de razón mínima (θ-test).

        Solo considera filas donde el coeficiente de la columna pivote > ε.
        Si todas las razones son negativas o cero → problema ilimitado.

        Returns:
            (fila_pivote, lista_razones)
            fila_pivote es None si el problema es ilimitado.
        """
        m = tableau.shape[0]
        razones: List[Optional[float]] = []
        min_razon = float('inf')
        fila_piv = None

        for i in range(m):
            coef = tableau[i, col_piv]
            rhs = tableau[i, -1]
            if coef > _EPSILON:
                razon = rhs / coef
                razones.append(razon)
                if razon < min_razon - _EPSILON:
                    min_razon = razon
                    fila_piv = i
                elif abs(razon - min_razon) < _EPSILON and fila_piv is not None:
                    # Empate: criterio de Bland (fila menor)
                    pass
            else:
                razones.append(None)

        return fila_piv, razones

    # ──────────────────────────────────────────────────────────────────────
    #  Pivoteo
    # ──────────────────────────────────────────────────────────────────────

    def _pivotear(
        self,
        tableau: np.ndarray,
        fila_piv: int,
        col_piv: int,
        nombres_cols: List[str],
    ) -> List[OperacionFila]:
        """
        Realiza las operaciones elementales de fila para el pivoteo.

        1. Normaliza la fila pivote dividiendo por el elemento pivote.
        2. Elimina los coeficientes de las demás filas en la columna pivote.

        Returns:
            Lista de OperacionFila con la descripción de cada paso.
        """
        operaciones: List[OperacionFila] = []
        elem_piv = tableau[fila_piv, col_piv]

        # Paso 1: Normalizar fila pivote
        tableau[fila_piv] = tableau[fila_piv] / elem_piv
        # Limpiar valores cercanos a cero
        for j in range(tableau.shape[1]):
            tableau[fila_piv, j] = limpiar_cero(tableau[fila_piv, j])

        op_norm = OperacionFila(
            descripcion=(
                f"R{fila_piv + 1} = R{fila_piv + 1} / {format_number(elem_piv)}"
                f"  (elemento pivote = {format_number(elem_piv)})"
            ),
            fila_resultado=tableau[fila_piv].tolist(),
        )
        operaciones.append(op_norm)

        # Paso 2: Eliminar en las demás filas
        m = tableau.shape[0]
        for i in range(m):
            if i == fila_piv:
                continue
            factor = tableau[i, col_piv]
            if abs(factor) < _EPSILON:
                continue
            tableau[i] = tableau[i] - factor * tableau[fila_piv]
            for j in range(tableau.shape[1]):
                tableau[i, j] = limpiar_cero(tableau[i, j])

            signo = "-" if factor > 0 else "+"
            abs_factor = abs(factor)
            factor_str = (
                format_number(abs_factor)
                if abs(abs_factor - 1.0) > _EPSILON
                else ""
            )
            op = OperacionFila(
                descripcion=(
                    f"R{i + 1} = R{i + 1} {signo} {factor_str}·R{fila_piv + 1}"
                ),
                fila_resultado=tableau[i].tolist(),
            )
            operaciones.append(op)

        return operaciones

    # ──────────────────────────────────────────────────────────────────────
    #  Extracción de la solución
    # ──────────────────────────────────────────────────────────────────────

    def _extraer_solucion(
        self,
        tableau: np.ndarray,
        nombres_cols: List[str],
        base_vars: List[str],
        pe: ProblemaEstandar,
    ) -> None:
        """Extrae los valores de las variables de la solución óptima."""
        nombres_vars = nombres_cols[:-1]
        valores: Dict[str, float] = {n: 0.0 for n in nombres_vars}

        for i, bv in enumerate(base_vars):
            valores[bv] = limpiar_cero(tableau[i, -1])

        self.resultado.valores_variables = valores

        # Valor objetivo = Zj de la columna RHS
        # En modo algebraico, usar los coeficientes originales (no negados)
        if self.modo_algebraico and self._cj_original is not None:
            cj_obj = self._cj_original
        else:
            cj_obj = [pe.coef_objetivo.get(bv, 0.0) for bv in base_vars]
            cb = np.array(cj_obj)
            z = float(cb @ tableau[:, -1])
            self.resultado.valor_objetivo = limpiar_cero(z)
            return

        cb = np.array([cj_obj[nombres_vars.index(bv)] if bv in nombres_vars else pe.coef_objetivo.get(bv, 0.0) for bv in base_vars])
        z = float(cb @ tableau[:, -1])
        self.resultado.valor_objetivo = limpiar_cero(z)

    def _detectar_multiples(
        self,
        cj_zj: np.ndarray,
        nombres_cols: List[str],
        base_vars: List[str],
        estado_actual: EstadoSolucion,
    ) -> EstadoSolucion:
        """
        Detecta si existen soluciones múltiples (Cj-Zj = 0 para variable no básica).
        """
        n_vars = len(cj_zj) - 1
        for j in range(n_vars):
            nombre = nombres_cols[j]
            if nombre not in base_vars and abs(cj_zj[j]) < _EPSILON:
                return EstadoSolucion.MULTIPLES
        return estado_actual

    # ──────────────────────────────────────────────────────────────────────
    #  Construcción de la Iteracion
    # ──────────────────────────────────────────────────────────────────────

    def _crear_iteracion(
        self,
        numero: int,
        tableau: np.ndarray,
        nombres_cols: List[str],
        cj: List[float],
        base_vars: List[str],
        base_coefs: List[float],
        pe: ProblemaEstandar,
    ) -> Iteracion:
        """Empaqueta el estado actual del tableau en un objeto Iteracion."""
        it = Iteracion(numero=numero)
        it.tabla = [
            [limpiar_cero(v) for v in fila.tolist()]
            for fila in tableau
        ]
        it.nombres_columnas = list(nombres_cols)
        it.cj = list(cj) + [0.0]  # incluir columna RHS
        it.variables_base = list(base_vars)
        it.coefs_base = list(base_coefs)
        it.modo_algebraico = self.modo_algebraico
        return it

    # ──────────────────────────────────────────────────────────────────────
    #  Generación de explicaciones
    # ──────────────────────────────────────────────────────────────────────

    def _explicacion_tabla_inicial(
        self, pe: ProblemaEstandar, gran_m: bool = False, M: float = 0
    ) -> str:
        """Genera el texto explicativo de la tabla inicial."""
        lines = [
            "═" * 55,
            "  TABLA INICIAL — Iteración 0",
            "═" * 55,
            "",
            f"  Problema: {pe.problema_original.funcion_objetivo_str()}",
            "",
        ]
        if self.modo_algebraico:
            lines += [
                "  Modo: ALGEBRAICO",
                "  La función objetivo se despeja igualando a cero:",
                f"    Z",
            ]
            for nombre, coef in pe.coef_objetivo.items():
                if coef != 0:
                    signo = "-" if coef > 0 else "+"
                    lines[-1] += f" {signo} {abs(coef)}{nombre}"
            lines[-1] += " = 0"
            lines += [
                "  Los coeficientes se multiplican por -1 en la tabla.",
                "",
            ]
        lines += [
            "  Conversión a Forma Estándar:",
        ]
        for paso in pe.pasos_conversion:
            lines.append(f"    {paso}")
        lines += [
            "",
            f"  Variables en la base inicial: {', '.join(pe.base_inicial)}",
            "",
        ]
        if gran_m:
            lines += [
                f"  Método: Gran M  (M = {M:.0e})",
                "  Las variables artificiales tienen coeficiente",
                f"  {'-M' if pe.tipo == TipoOptimizacion.MAXIMIZAR else '+M'} en la función objetivo.",
                "",
            ]
        if self.modo_algebraico:
            lines += [
                "  Nota: Cj = coeficientes de la función objetivo (negados).",
                "        Cb = coeficientes de las variables en la base (negados).",
                "        Zj = Σ(Cb · columna j).",
                "        Cj - Zj = índice de mejora.",
                "        Variable entrante: Cj-Zj más negativo (Max) o más positivo (Min).",
            ]
        else:
            lines += [
                "  Nota: Cj = coeficientes de la función objetivo.",
                "        Cb = coeficientes de las variables en la base.",
                "        Zj = Σ(Cb · columna j).",
                "        Cj - Zj = índice de mejora de cada variable.",
            ]
        return "\n".join(lines)

    def _explicacion_iteracion(
        self,
        it: Iteracion,
        pe: ProblemaEstandar,
        nombres_cols: List[str],
    ) -> str:
        """Genera la explicación detallada de una iteración."""
        lines = [
            "═" * 55,
            f"  ITERACIÓN {it.numero}",
            "═" * 55,
            "",
            "  1. Calcular Cj - Zj:",
        ]

        # Mostrar Cj-Zj
        n_vars = len(it.cj_zj) - 1 if it.cj_zj else 0
        for j in range(n_vars):
            nombre = nombres_cols[j] if j < len(nombres_cols) else f"col{j}"
            val = it.cj_zj[j] if it.cj_zj else 0
            lines.append(f"     {nombre} = {format_number(val)}")

        lines.append("")

        # Variable entrante
        if it.variable_entrante:
            if self.modo_algebraico:
                if pe.tipo == TipoOptimizacion.MAXIMIZAR:
                    lines.append("  2. Selección de variable entrante (Min Cj-Zj < 0):")
                    lines.append(
                        f"     El valor más negativo de Cj-Zj corresponde a {it.variable_entrante}."
                    )
                else:
                    lines.append("  2. Selección de variable entrante (Max Cj-Zj > 0):")
                    lines.append(
                        f"     El mayor valor positivo de Cj-Zj corresponde a {it.variable_entrante}."
                    )
            else:
                if pe.tipo == TipoOptimizacion.MAXIMIZAR:
                    lines.append("  2. Selección de variable entrante (Max Cj-Zj > 0):")
                    lines.append(
                        f"     El mayor valor positivo de Cj-Zj corresponde a {it.variable_entrante}."
                    )
                else:
                    lines.append("  2. Selección de variable entrante (Min Cj-Zj < 0):")
                    lines.append(
                        f"     El valor más negativo de Cj-Zj corresponde a {it.variable_entrante}."
                    )
            lines.append(f"     → {it.variable_entrante} ENTRA a la base.")
            lines.append("")

        # Prueba de razón mínima
        if it.razones:
            lines.append("  3. Prueba de razón mínima (θ-test):")
            lines.append("     Solo se consideran razones con coeficiente > 0 en la columna pivote.")
            for i, r in enumerate(it.razones):
                bv = it.variables_base[i] if i < len(it.variables_base) else f"R{i+1}"
                if r is not None:
                    lines.append(f"     R{i+1} ({bv}): {format_number(it.tabla[i][-1])} / {format_number(it.elemento_pivote)} = {format_number(r)}")
                else:
                    lines.append(f"     R{i+1} ({bv}): ratio no válido (coeficiente ≤ 0)")
            lines.append("")

        # Variable saliente
        if it.variable_saliente:
            lines.append(f"  4. Variable saliente:")
            lines.append(f"     La razón mínima positiva corresponde a {it.variable_saliente}.")
            lines.append(f"     → {it.variable_saliente} SALE de la base.")
            lines.append("")

        # Elemento pivote
        if it.elemento_pivote is not None:
            lines.append(f"  5. Elemento pivote = {format_number(it.elemento_pivote)}")
            lines.append(f"     Fila pivote: R{it.fila_pivote + 1}  |  Columna pivote: {it.variable_entrante}")
            lines.append("")

        # Operaciones de fila
        if it.operaciones:
            lines.append("  6. Operaciones de fila (pivoteo):")
            for op in it.operaciones:
                lines.append(f"     {op.descripcion}")
            lines.append("")

        lines.append("  → Se obtiene la nueva tabla para la siguiente iteración.")
        return "\n".join(lines)

    def _explicacion_solucion_final(
        self, it: Iteracion, pe: ProblemaEstandar, estado: EstadoSolucion
    ) -> str:
        """Genera la explicación de la condición de parada."""
        lines = [
            "═" * 55,
            f"  ITERACIÓN {it.numero} — CONDICIÓN DE PARADA",
            "═" * 55,
            "",
        ]

        if estado == EstadoSolucion.OPTIMA:
            if self.modo_algebraico:
                if pe.tipo == TipoOptimizacion.MAXIMIZAR:
                    lines += [
                        "  ✓ Condición de optimalidad cumplida (Modo Algebraico).",
                        "",
                        "  No existen valores negativos en Cj - Zj.",
                        "  Por lo tanto, ninguna variable no básica puede",
                        "  mejorar el valor de la función objetivo.",
                        "  La solución actual es ÓPTIMA.",
                    ]
                else:
                    lines += [
                        "  ✓ Condición de optimalidad cumplida (Modo Algebraico).",
                        "",
                        "  No existen valores positivos en Cj - Zj.",
                        "  La solución actual es ÓPTIMA.",
                    ]
            else:
                if pe.tipo == TipoOptimizacion.MAXIMIZAR:
                    lines += [
                        "  ✓ Condición de optimalidad cumplida.",
                        "",
                        "  No existen valores positivos en Cj - Zj.",
                        "  Por lo tanto, ninguna variable no básica puede",
                        "  mejorar el valor de la función objetivo.",
                        "  La solución actual es ÓPTIMA.",
                    ]
                else:
                    lines += [
                        "  ✓ Condición de optimalidad cumplida.",
                        "",
                        "  No existen valores negativos en Cj - Zj.",
                        "  Por lo tanto, la solución actual es ÓPTIMA.",
                    ]
        elif estado == EstadoSolucion.ILIMITADO:
            lines += [
                "  ⚠ Problema ILIMITADO.",
                "  Todos los coeficientes en la columna pivote son ≤ 0.",
                "  La función objetivo puede mejorar indefinidamente.",
            ]
        elif estado == EstadoSolucion.INFACTIBLE:
            lines += [
                "  ⚠ Problema INFACTIBLE.",
                "  No existe región factible para el problema dado.",
            ]

        return "\n".join(lines)

    def _mensaje_solucion(self, estado: EstadoSolucion) -> str:
        """Genera el mensaje de resumen de la solución."""
        if estado == EstadoSolucion.OPTIMA:
            r = self.resultado
            lines = ["✓ SOLUCIÓN ÓPTIMA ENCONTRADA", ""]
            for nombre, valor in r.valores_variables.items():
                lines.append(f"  {nombre} = {format_number(valor)}")
            lines.append("")
            lines.append(f"  Z* = {format_number(r.valor_objetivo)}")
            return "\n".join(lines)
        elif estado == EstadoSolucion.MULTIPLES:
            return "✓ SOLUCIONES MÚLTIPLES — existen infinitas soluciones óptimas."
        elif estado == EstadoSolucion.ILIMITADO:
            return "⚠ Problema ILIMITADO."
        elif estado == EstadoSolucion.INFACTIBLE:
            return "⚠ Problema INFACTIBLE — no existe región factible."
        return "Sin resolver."
