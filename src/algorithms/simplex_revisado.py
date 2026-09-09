"""
Método Simplex Revisado para Programación Lineal.

A diferencia del Simplex tabular (Big Tableau), el Simplex Revisado:
  - NO mantiene toda la tabla transformada en memoria.
  - Trabaja directamente con la inversa de la base B⁻¹.
  - En cada iteración calcula SOLO la columna/fila que necesita.

Algoritmo:
  1. Convertir a forma estándar (Ax = b, x ≥ 0).
  2. Elegir base inicial B (variables de holgura / artificiales).
  3. Calcular B⁻¹.
  4. Calcular x_B = B⁻¹ b.
  5. Calcular costos reducidos c̄_j = c_j - c_B^T B⁻¹ A_j  (∀ j no básico).
  6. Si todos c̄_j ≤ 0  → ÓPTIMO (para Maximización).
  7. Seleccionar variable entrante: mayor c̄_j > 0.
  8. Calcular dirección y = B⁻¹ A_j (columna transformada).
  9. Prueba de razón mínima θ = x_Bi / y_i  (y_i > 0).
 10. Actualizar base, recalcular B⁻¹ y repetir.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from models.problema import Problema, TipoOptimizacion
from models.resultado import EstadoSolucion, Iteracion, Resultado
from models.variable import TipoVariable
from algorithms.forma_estandar import ProblemaEstandar, convertir_a_forma_estandar
from algorithms.validaciones import validar_problema
from utils.format_numbers import limpiar_cero, format_number


# ─────────────────────────────────────────────────────────────────────────────
#  Constantes
# ─────────────────────────────────────────────────────────────────────────────

_EPSILON = 1e-10
_MAX_ITERACIONES = 200


# ─────────────────────────────────────────────────────────────────────────────
#  Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class SimplexRevisado:
    """
    Motor del Método Simplex Revisado.

    Uso::
        solver = SimplexRevisado(problema)
        resultado = solver.resolver()
        for it in resultado.iteraciones:
            print(it.explicacion)
    """

    def __init__(self, problema: Problema) -> None:
        self.problema = problema
        self.resultado = Resultado(metodo="Simplex Revisado")

    # ──────────────────────────────────────────────────────────────────────
    #  Punto de entrada público
    # ──────────────────────────────────────────────────────────────────────

    def resolver(self) -> Resultado:
        """Resuelve el problema usando el Método Simplex Revisado."""
        # 1. Validar
        es_valido, errores = validar_problema(self.problema)
        if not es_valido:
            self.resultado.estado = EstadoSolucion.INFACTIBLE
            self.resultado.mensaje = "Problema inválido:\n" + "\n".join(errores)
            return self.resultado

        # 2. Convertir a forma estándar
        pe = convertir_a_forma_estandar(self.problema)

        # 3. Construir matrices A, b, c
        A, b, c, nombres_vars = self._construir_matrices(pe)

        # 4. Inicializar base con las variables de base_inicial de la forma estándar
        base_idx = [nombres_vars.index(bv) for bv in pe.base_inicial]
        base_vars = list(pe.base_inicial)

        iteraciones: List[Iteracion] = []
        num_iter = 0

        while num_iter <= _MAX_ITERACIONES:
            # ── Calcular B y B⁻¹ ──────────────────────────────────────────
            B = A[:, base_idx]
            try:
                B_inv = np.linalg.inv(B)
            except np.linalg.LinAlgError:
                self.resultado.estado = EstadoSolucion.INFACTIBLE
                self.resultado.mensaje = (
                    "La base es singular. El problema puede ser infactible o degenerado."
                )
                self.resultado.iteraciones = iteraciones
                return self.resultado

            # ── Calcular x_B = B⁻¹ b ──────────────────────────────────────
            x_B = B_inv @ b
            x_B = np.array([limpiar_cero(v) for v in x_B])

            # ── Verificar factibilidad (x_B ≥ 0) ──────────────────────────
            if np.any(x_B < -_EPSILON):
                self.resultado.estado = EstadoSolucion.INFACTIBLE
                self.resultado.mensaje = (
                    "Solución básica no factible. "
                    "El problema es INFACTIBLE con la base actual."
                )
                self.resultado.iteraciones = iteraciones
                return self.resultado

            # ── Coeficientes de la base c_B ────────────────────────────────
            c_B = c[base_idx]

            # ── Multiplicadores duales w = c_B^T · B⁻¹ ────────────────────
            w = c_B @ B_inv  # shape (m,)

            # ── Costos reducidos c̄_j = c_j - w^T A_j ─────────────────────
            c_barra = np.array([
                limpiar_cero(float(c[j] - w @ A[:, j]))
                for j in range(len(nombres_vars))
            ])

            # ── Valor actual de la función objetivo según el problema original ──
            z_actual = limpiar_cero(sum(
                self.problema.coef_objetivo.get(bv, 0.0) * float(x_B[i])
                for i, bv in enumerate(base_vars)
            ))

            # ── Registrar iteración ────────────────────────────────────────
            it = self._crear_iteracion(
                numero=num_iter,
                B=B,
                B_inv=B_inv,
                x_B=x_B,
                base_idx=base_idx,
                base_vars=base_vars,
                c_B=c_B,
                c_barra=c_barra,
                nombres_vars=nombres_vars,
                w=w,
                A=A,
                c=c,
                z_actual=z_actual,
            )

            # ── Verificar optimalidad ──────────────────────────────────────
            es_optimo = self._verificar_optimalidad(c_barra, base_idx)

            if es_optimo:
                it.explicacion += self._explicacion_optimalidad(
                    base_vars, x_B, z_actual, c_barra, nombres_vars, base_idx
                )
                iteraciones.append(it)
                # Detectar artificiales en base con valor > ε → infactible
                estado = self._verificar_artificiales_base(base_vars, x_B, pe)
                if estado == EstadoSolucion.INFACTIBLE:
                    self.resultado.estado = EstadoSolucion.INFACTIBLE
                    self.resultado.mensaje = (
                        "⚠ El problema es INFACTIBLE.\n"
                        "Variables artificiales permanecen en la base con valor > 0."
                    )
                    self.resultado.iteraciones = iteraciones
                    return self.resultado

                estado = self._detectar_multiples(c_barra, base_idx, estado)
                self._extraer_solucion(x_B, base_vars, nombres_vars, pe)
                self.resultado.estado = estado
                self.resultado.iteraciones = iteraciones
                self.resultado.num_iteraciones = len(iteraciones) - 1
                self.resultado.variables_base_final = list(base_vars)
                self.resultado.mensaje = self._mensaje_solucion(estado)
                return self.resultado

            # ── Seleccionar variable entrante ──────────────────────────────
            col_ent_idx = self._seleccionar_entrante(c_barra, base_idx)
            if col_ent_idx is None:
                break  # Óptimo (ya capturado) o sin candidatos

            # ── Calcular y = B⁻¹ A_j (dirección de mejora) ────────────────
            y = B_inv @ A[:, col_ent_idx]
            y = np.array([limpiar_cero(v) for v in y])

            # ── Prueba de razón mínima ─────────────────────────────────────
            fila_sal, razones = self._prueba_razon_minima(x_B, y)

            if fila_sal is None:
                # Todos y_i ≤ 0 → solución ilimitada
                it.variable_entrante = nombres_vars[col_ent_idx]
                it.y_columna = [limpiar_cero(float(v)) for v in y]
                it.explicacion += self._explicacion_ilimitado(
                    nombres_vars[col_ent_idx], y
                )
                iteraciones.append(it)
                self.resultado.estado = EstadoSolucion.ILIMITADO
                self.resultado.mensaje = (
                    "⚠ El problema es ILIMITADO.\n"
                    f"La variable '{nombres_vars[col_ent_idx]}' puede crecer sin límite."
                )
                self.resultado.iteraciones = iteraciones
                return self.resultado

            var_ent = nombres_vars[col_ent_idx]
            var_sal = base_vars[fila_sal]

            # Completar datos del pivote en la iteración
            it.variable_entrante = var_ent
            it.variable_saliente = var_sal
            it.col_pivote = col_ent_idx
            it.fila_pivote = fila_sal
            it.elemento_pivote = limpiar_cero(float(y[fila_sal]))
            it.y_columna = [limpiar_cero(float(v)) for v in y]
            it.razones = [limpiar_cero(r) if r is not None else None for r in razones]
            it.explicacion += self._explicacion_pivote(
                var_ent, var_sal, y, razones, base_vars, c_barra, col_ent_idx, x_B, fila_sal
            )

            iteraciones.append(it)

            # ── Actualizar base ────────────────────────────────────────────
            base_idx[fila_sal] = col_ent_idx
            base_vars[fila_sal] = var_ent
            num_iter += 1

        # Máximo de iteraciones alcanzado
        self.resultado.estado = EstadoSolucion.SIN_RESOLVER
        self.resultado.mensaje = (
            f"Máximo de iteraciones ({_MAX_ITERACIONES}) alcanzado sin convergencia."
        )
        self.resultado.iteraciones = iteraciones
        return self.resultado

    # ──────────────────────────────────────────────────────────────────────
    #  Construcción de matrices
    # ──────────────────────────────────────────────────────────────────────

    def _construir_matrices(
        self, pe: ProblemaEstandar
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
        """Construye A (m×n), b (m,), c (n,) desde el ProblemaEstandar."""
        nombres_vars = pe.nombres_variables
        m = pe.num_restricciones
        n = len(nombres_vars)

        A = np.zeros((m, n), dtype=float)
        b = np.zeros(m, dtype=float)
        c = np.zeros(n, dtype=float)

        for i, rest in enumerate(pe.restricciones):
            for j, nombre in enumerate(nombres_vars):
                A[i, j] = rest.obtener_coef(nombre)
            b[i] = rest.rhs

        for j, nombre in enumerate(nombres_vars):
            c[j] = pe.coef_objetivo.get(nombre, 0.0)

        # Para minimización convertimos a maximización negando c
        # (los costos reducidos de un problema Min ≡ los de Max -Z)
        if pe.tipo == TipoOptimizacion.MINIMIZAR:
            c = -c

        # Penalización Big-M para variables artificiales en la formulación de maximización
        if pe.tiene_artificiales:
            from config.config import APP_CONFIG
            M = APP_CONFIG.big_m_value
            nombres_art = {
                v.nombre for v in pe.variables_auxiliares
                if v.tipo == TipoVariable.ARTIFICIAL
            }
            for j, nombre in enumerate(nombres_vars):
                if nombre in nombres_art:
                    c[j] = -M

        return A, b, c, nombres_vars

    # ──────────────────────────────────────────────────────────────────────
    #  Criterios de parada y detección de casos especiales
    # ──────────────────────────────────────────────────────────────────────

    def _verificar_optimalidad(
        self, c_barra: np.ndarray, base_idx: List[int]
    ) -> bool:
        """Óptimo si todos los costos reducidos no básicos ≤ 0."""
        non_basic = [j for j in range(len(c_barra)) if j not in base_idx]
        if not non_basic:
            return True
        return bool(np.all(c_barra[non_basic] <= _EPSILON))

    def _verificar_artificiales_base(
        self, base_vars: List[str], x_B: np.ndarray, pe: ProblemaEstandar
    ) -> EstadoSolucion:
        """Si alguna artificial queda en la base con valor > ε → INFACTIBLE."""
        nombres_art = {
            v.nombre for v in pe.variables_auxiliares
            if v.tipo == TipoVariable.ARTIFICIAL
        }
        for i, bv in enumerate(base_vars):
            if bv in nombres_art and abs(x_B[i]) > _EPSILON:
                return EstadoSolucion.INFACTIBLE
        return EstadoSolucion.OPTIMA

    def _detectar_multiples(
        self, c_barra: np.ndarray, base_idx: List[int], estado: EstadoSolucion
    ) -> EstadoSolucion:
        """Detecta soluciones óptimas múltiples: algún c̄_j no básico = 0."""
        if estado != EstadoSolucion.OPTIMA:
            return estado
        non_basic = [j for j in range(len(c_barra)) if j not in base_idx]
        for j in non_basic:
            if abs(c_barra[j]) < _EPSILON:
                return EstadoSolucion.MULTIPLES
        return estado

    # ──────────────────────────────────────────────────────────────────────
    #  Selección de pivote
    # ──────────────────────────────────────────────────────────────────────

    def _seleccionar_entrante(
        self, c_barra: np.ndarray, base_idx: List[int]
    ) -> Optional[int]:
        """Variable entrante: no básica con mayor c̄_j > 0 (regla de Dantzig)."""
        non_basic = [j for j in range(len(c_barra)) if j not in base_idx]
        candidatos = [(c_barra[j], j) for j in non_basic if c_barra[j] > _EPSILON]
        if not candidatos:
            return None
        return max(candidatos, key=lambda x: x[0])[1]

    def _prueba_razon_minima(
        self, x_B: np.ndarray, y: np.ndarray
    ) -> Tuple[Optional[int], List[Optional[float]]]:
        """Razón mínima θ = x_Bi / y_i  (solo para y_i > 0)."""
        razones: List[Optional[float]] = []
        min_theta = float("inf")
        fila_sal = None

        for i in range(len(x_B)):
            if y[i] > _EPSILON:
                theta = limpiar_cero(float(x_B[i]) / float(y[i]))
                razones.append(theta)
                if theta < min_theta - _EPSILON:
                    min_theta = theta
                    fila_sal = i
            else:
                razones.append(None)

        return fila_sal, razones

    # ──────────────────────────────────────────────────────────────────────
    #  Construcción de Iteracion para la GUI
    # ──────────────────────────────────────────────────────────────────────

    def _crear_iteracion(
        self,
        numero: int,
        B: np.ndarray,
        B_inv: np.ndarray,
        x_B: np.ndarray,
        base_idx: List[int],
        base_vars: List[str],
        c_B: np.ndarray,
        c_barra: np.ndarray,
        nombres_vars: List[str],
        w: np.ndarray,
        A: np.ndarray,
        c: np.ndarray,
        z_actual: float,
    ) -> Iteracion:
        """
        Crea una Iteracion completa para Simplex Revisado.
        Empaqueta la matriz inversa B⁻¹, la solución básica x_B, los multiplicadores
        duales w, y los costos reducidos para su renderizado especializado.
        """
        m = B_inv.shape[0]
        non_basic_idx = [j for j in range(len(nombres_vars)) if j not in base_idx]

        # Tabla tradicional de fallback: filas de B⁻¹ con x_B al final
        tabla = []
        for i in range(m):
            fila = [limpiar_cero(v) for v in B_inv[i].tolist()]
            fila.append(limpiar_cero(float(x_B[i])))
            tabla.append(fila)

        nombres_cols = [f"B\u207b\u00b9_{i+1}" for i in range(m)] + ["x_B"]

        it = Iteracion(numero=numero)
        it.es_revisado = True
        it.tabla = tabla
        it.nombres_columnas = nombres_cols
        it.variables_base = list(base_vars)
        it.coefs_base = [limpiar_cero(float(v)) for v in c_B.tolist()]

        # Costos y multiplicadores
        c_barra_list = [limpiar_cero(float(c_barra[j])) for j in range(len(nombres_vars))]
        it.cj = c_barra_list + [0.0]
        it.cj_zj = c_barra_list + [0.0]
        it.zj = [limpiar_cero(float(w[i])) for i in range(m)] + [0.0]

        # Atributos extendidos para Simplex Revisado
        it.B_inv = [[limpiar_cero(float(v)) for v in fila] for fila in B_inv]
        it.x_B = [limpiar_cero(float(v)) for v in x_B]
        it.w_duales = [limpiar_cero(float(v)) for v in w]
        it.todas_variables = list(nombres_vars)
        it.cj_todas = [limpiar_cero(float(c[j])) for j in range(len(nombres_vars))]
        it.zj_todas = [limpiar_cero(float(w @ A[:, j])) for j in range(len(nombres_vars))]
        it.c_barra_todas = c_barra_list
        it.valor_z_actual = z_actual

        it.explicacion = self._explicacion_iteracion(
            numero, B, B_inv, x_B, c_barra, base_vars, nombres_vars, base_idx, w, c_B, A, c, z_actual
        )
        return it

    # ──────────────────────────────────────────────────────────────────────
    #  Extracción de solución final
    # ──────────────────────────────────────────────────────────────────────

    def _extraer_solucion(
        self,
        x_B: np.ndarray,
        base_vars: List[str],
        nombres_vars: List[str],
        pe: ProblemaEstandar,
    ) -> None:
        """Extrae los valores de todas las variables y el valor objetivo Z*."""
        valores = {n: 0.0 for n in nombres_vars}
        for i, bv in enumerate(base_vars):
            valores[bv] = limpiar_cero(float(x_B[i]))
        self.resultado.valores_variables = valores

        # Valor objetivo con coeficientes ORIGINALES (sin negar)
        z = limpiar_cero(sum(
            self.problema.coef_objetivo.get(n, 0.0) * valores.get(n, 0.0)
            for n in self.problema.nombres_variables
        ))
        self.resultado.valor_objetivo = z

    # ──────────────────────────────────────────────────────────────────────
    #  Mensajes y textos explicativos
    # ──────────────────────────────────────────────────────────────────────

    def _mensaje_solucion(self, estado: EstadoSolucion) -> str:
        r = self.resultado
        if estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES):
            lines = [
                "══════════════════════════════════════════════════════════════════",
                "  ✓ SOLUCIÓN ÓPTIMA ALCANZADA (Método Simplex Revisado)",
                "══════════════════════════════════════════════════════════════════",
                "",
                "  Valores óptimos de las variables:",
            ]
            for n in self.problema.nombres_variables:
                v = r.valores_variables.get(n, 0.0)
                lines.append(f"    {n:>6} = {format_number(v)}")

            # Variables de holgura / auxiliares si existen
            auxiliares = [n for n in r.valores_variables if n not in self.problema.nombres_variables]
            if auxiliares:
                lines.append("\n  Variables auxiliares (holgura / exceso):")
                for n in auxiliares:
                    v = r.valores_variables.get(n, 0.0)
                    lines.append(f"    {n:>6} = {format_number(v)}")

            lines.append(f"\n  Valor Óptimo de la Función Objetivo:")
            lines.append(f"    Z* = {format_number(r.valor_objetivo)}")
            if estado == EstadoSolucion.MULTIPLES:
                lines.append("\n  ⚠ NOTA: Existen infinitas soluciones óptimas alternativas (al menos un costo reducido no básico es 0).")
            return "\n".join(lines)
        return str(estado.value)

    def _explicacion_iteracion(
        self,
        numero: int,
        B: np.ndarray,
        B_inv: np.ndarray,
        x_B: np.ndarray,
        c_barra: np.ndarray,
        base_vars: List[str],
        nombres_vars: List[str],
        base_idx: List[int],
        w: np.ndarray,
        c_B: np.ndarray,
        A: np.ndarray,
        c: np.ndarray,
        z_actual: float,
    ) -> str:
        m = B_inv.shape[0]
        non_basic_idx = [j for j in range(len(nombres_vars)) if j not in base_idx]
        lines: List[str] = []

        lines.append("══════════════════════════════════════════════════════════════════════════════════")
        if numero == 0:
            lines.append("  ⚡ MÉTODO SIMPLEX REVISADO — ITERACIÓN INICIAL (Iteración 0)")
        else:
            lines.append(f"  ⚡ MÉTODO SIMPLEX REVISADO — ITERACIÓN {numero}")
        lines.append("══════════════════════════════════════════════════════════════════════════════════\n")

        # PASO 1
        lines.append("▶ [PASO 1] BASE ACTUAL Y MATRICES ASOCIADAS")
        base_desc = ", ".join(f"{bv} (c={format_number(c_B[i])})" for i, bv in enumerate(base_vars))
        lines.append(f"  • Variables en la Base: [ {base_desc} ]")
        lines.append(f"  • Vector c_B = [ {', '.join(format_number(v) for v in c_B)} ]")
        lines.append("\n  • Matriz Base B (columnas de A en la base):")
        for i in range(m):
            fila_B = "    [ " + "  ".join(f"{format_number(B[i, j]):>9}" for j in range(m)) + " ]"
            lines.append(fila_B)

        lines.append("\n  • Matriz Inversa de la Base B⁻¹:")
        for i in range(m):
            fila_inv = "    [ " + "  ".join(f"{format_number(B_inv[i, j]):>9}" for j in range(m)) + " ]"
            lines.append(fila_inv)

        # PASO 2
        lines.append("\n▶ [PASO 2] SOLUCIÓN BÁSICA ACTUAL Y VALOR OBJETIVO")
        lines.append("  • Se calcula mediante el producto matriz-vector:  x_B = B⁻¹ · b")
        for i, bv in enumerate(base_vars):
            lines.append(f"    {bv} = {format_number(x_B[i])}")
        no_basicas_str = ", ".join(f"{nombres_vars[j]} = 0" for j in non_basic_idx)
        lines.append(f"  • Variables no básicas (nulas por definición): [ {no_basicas_str} ]")
        lines.append(f"  • Valor actual de la función objetivo: Z = c_B^T · x_B = {format_number(z_actual)}")

        # PASO 3
        lines.append("\n▶ [PASO 3] MULTIPLICADORES DUALES / VECTOR SIMPLEX (Precios Sombra)")
        lines.append("  • Se calcula el vector fila dual:  w^T = c_B^T · B⁻¹")
        w_str = ", ".join(format_number(wi) for wi in w)
        lines.append(f"    w = [ {w_str} ]")
        lines.append("  • Significado: Cada componente w_i representa la tasa marginal de cambio en Z")
        lines.append("    ante un aumento unitario en el lado derecho b_i de la restricción i.")

        # PASO 4
        lines.append("\n▶ [PASO 4] EVALUACIÓN DE COSTOS REDUCIDOS (Criterio de Parada)")
        lines.append("  • Fórmula:  c̄_j = c_j - z_j = c_j - w^T · A_j   (para cada variable no básica)")
        for j in non_basic_idx:
            nombre = nombres_vars[j]
            cj_val = c[j]
            zj_val = float(w @ A[:, j])
            cb_val = c_barra[j]
            if cb_val > _EPSILON:
                tag = " ← CANDIDATA A ENTRAR (Mejora Z)"
            elif abs(cb_val) <= _EPSILON:
                tag = " (Coste neutro = 0)"
            else:
                tag = " (No mejora Z)"
            lines.append(f"    c̄({nombre:<4}) = {format_number(cj_val):>7} - ({format_number(zj_val):>7}) = {format_number(cb_val):>8}{tag}")

        return "\n".join(lines)

    def _explicacion_pivote(
        self,
        var_ent: str,
        var_sal: str,
        y: np.ndarray,
        razones: List[Optional[float]],
        base_vars: List[str],
        c_barra: np.ndarray,
        col_ent_idx: int,
        x_B: np.ndarray,
        fila_sal: int,
    ) -> str:
        lines: List[str] = []

        # PASO 5
        lines.append("\n▶ [PASO 5] SELECCIÓN DE LA VARIABLE ENTRANTE (Regla de Dantzig)")
        lines.append(f"  • Variable seleccionada: {var_ent}")
        lines.append(f"  • Costo reducido: c̄({var_ent}) = {format_number(c_barra[col_ent_idx])} (el más positivo).")
        lines.append(f"  • Justificación: Por cada unidad que {var_ent} aumente en la solución,")
        lines.append(f"    la función objetivo mejorará a una tasa neta de {format_number(c_barra[col_ent_idx])}.")

        # PASO 6
        lines.append("\n▶ [PASO 6] DIRECCIÓN DE MEJORA / COLUMNA TRANSFORMADA (y = B⁻¹ · A_j)")
        lines.append(f"  • Se calcula el vector dirección:  y = B⁻¹ · A_{var_ent}")
        y_str = ", ".join(format_number(v) for v in y)
        lines.append(f"    y = [ {y_str} ]")
        lines.append(f"  • Interpretación: Indica cómo se ajustan las variables básicas actuales al entrar {var_ent}.")
        for i, bv in enumerate(base_vars):
            signo = "disminuye a tasa" if y[i] > _EPSILON else ("aumenta a tasa" if y[i] < -_EPSILON else "no varía con")
            lines.append(f"    - {bv}: {signo} {format_number(abs(y[i]))}")

        # PASO 7
        lines.append("\n▶ [PASO 7] PRUEBA DE LA RAZÓN MÍNIMA (Variable Saliente)")
        lines.append("  • Fórmula:  θ_i = x_Bi / y_i   (válido únicamente para y_i > 0)")
        for i, r in enumerate(razones):
            bv = base_vars[i]
            if r is not None:
                marca = "  ← MÍNIMO (Variable Saliente)" if i == fila_sal else ""
                lines.append(f"    Fila {i+1} [{bv}]:  θ_{i+1} = {format_number(x_B[i])} / {format_number(y[i])} = {format_number(r)}{marca}")
            else:
                lines.append(f"    Fila {i+1} [{bv}]:  y_{i+1} = {format_number(y[i])} ≤ 0 → No impone cota superior")

        lines.append(f"\n  • Variable Saliente: {var_sal}")
        lines.append(f"  • Elemento Pivote:  y_pivote = y[{fila_sal+1}] = {format_number(y[fila_sal])}")
        lines.append(f"  • Criterio: La variable {var_sal} llega primero a cero cuando {var_ent} = {format_number(razones[fila_sal])},")
        lines.append("    garantizando que todas las variables permanezcan no negativas (x ≥ 0).")

        # PASO 8
        nueva_base = list(base_vars)
        nueva_base[fila_sal] = var_ent
        lines.append("\n▶ [PASO 8] ACTUALIZACIÓN DE LA BASE")
        lines.append(f"  • La variable entrante '{var_ent}' reemplaza a '{var_sal}' en la posición {fila_sal+1}.")
        lines.append(f"  • Nueva base resultante: [ {', '.join(nueva_base)} ]")
        lines.append("  • En la siguiente iteración se recalculará B⁻¹ y se repetirán los pasos hasta la optimalidad.")

        return "\n".join(lines)

    def _explicacion_optimalidad(
        self,
        base_vars: List[str],
        x_B: np.ndarray,
        z_actual: float,
        c_barra: np.ndarray,
        nombres_vars: List[str],
        base_idx: List[int],
    ) -> str:
        non_basic_idx = [j for j in range(len(nombres_vars)) if j not in base_idx]
        lines = [
            "",
            "══════════════════════════════════════════════════════════════════════════════════",
            "  ✓ CONDICIÓN DE PARADA CUMPLIDA — SOLUCIÓN ÓPTIMA ALCANZADA",
            "══════════════════════════════════════════════════════════════════════════════════",
            "  • Todos los costos reducidos de las variables no básicas satisfacen:  c̄_j ≤ 0",
            "  • Ninguna variable externa puede entrar a la base para aumentar el valor de Z.",
            f"  • Valor Objetivo Óptimo:  Z* = {format_number(z_actual)}",
            "  • Solución Básica Óptima:",
        ]
        for i, bv in enumerate(base_vars):
            lines.append(f"      {bv} = {format_number(x_B[i])}")
        for j in non_basic_idx:
            lines.append(f"      {nombres_vars[j]} = 0.0000")
        return "\n".join(lines)

    def _explicacion_ilimitado(self, var_ent: str, y: np.ndarray) -> str:
        return (
            "\n"
            "══════════════════════════════════════════════════════════════════════════════════\n"
            "  ⚠ PROBLEMA ILIMITADO (UNBOUNDED)\n"
            "══════════════════════════════════════════════════════════════════════════════════\n"
            f"  • Variable entrante: {var_ent}\n"
            f"  • Vector transformado: y = B⁻¹ · A_{var_ent} = [{', '.join(format_number(v) for v in y)}]\n"
            "  • Todos los componentes y_i son ≤ 0.\n"
            f"  • La variable '{var_ent}' puede crecer indefinidamente sin que ninguna variable básica\n"
            "    se reduzca ni viole la condición de no negatividad x ≥ 0.\n"
            "  • Por tanto, la función objetivo Z no está acotada superiormente (Z → +∞)."
        )

