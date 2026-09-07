"""
Algoritmo de Dualidad para Programación Lineal.

Implementa:
- Construcción del problema dual a partir del primal.
- Explicación educativa de la transformación Primal → Dual.
- Tabla de correspondencia Primal-Dual.
- Resolución del dual con AlgoritmoSimplex / DosFases.
- Verificación de dualidad fuerte (Z* = W*).
- Verificación de holgura complementaria.
- Teoremas de dualidad débil y fuerte.

Reglas de conversión estándar:
  Primal MAX  con restricciones <= y variables >= 0
  ↓
  Dual   MIN  con restricciones >= y variables >= 0

Caso general (primal MAX):
  Restricción <= → variable dual y_i >= 0
  Restricción >= → variable dual y_i <= 0
  Restricción  = → variable dual y_i libre

Caso primal MIN: invertir roles (o convertir a MAX antes).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import numpy as np

from models.problema import Problema, TipoOptimizacion
from models.restriccion import Restriccion, TipoRestriccion
from models.variable import Variable, TipoVariable
from models.resultado import Resultado, EstadoSolucion
from algorithms.simplex import AlgoritmoSimplex
from algorithms.dos_fases import DosFases
from utils.format_numbers import format_number, limpiar_cero


# ─────────────────────────────────────────────────────────────────────────────
#  Dataclasses de soporte
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CorrespondenciaDual:
    """
    Tabla educativa de correspondencia Primal ↔ Dual.
    Cada entrada explica la relación entre elementos del primal y del dual.
    """
    filas: List[Tuple[str, str]] = field(default_factory=list)
    # Ejemplo: [("Restricción R1 (<=)", "Variable y1 >= 0"), ...]


@dataclass
class HolguraComplementaria:
    """Resultado de la verificación de holgura complementaria."""
    condicion_yi: List[str] = field(default_factory=list)
    condicion_xj: List[str] = field(default_factory=list)
    cumple_yi: List[bool] = field(default_factory=list)
    cumple_xj: List[bool] = field(default_factory=list)
    todas_cumplen: bool = False


@dataclass
class ResultadoDualidad:
    """
    Resultado educativo completo de la operación de dualidad.

    Attributes:
        primal: Problema original.
        dual: Problema dual construido.
        pasos_construccion: Explicación textual paso a paso de la transformación.
        correspondencia: Tabla Primal ↔ Dual.
        resultado_primal: Resultado de resolver el primal.
        resultado_dual: Resultado de resolver el dual.
        dualidad_fuerte: True si Z* = W* (dentro de tolerancia).
        valor_primal: Z* del primal.
        valor_dual: W* del dual.
        holgura_complementaria: Verificación de holgura complementaria.
        mensaje_verificacion: Texto del resultado de la verificación.
        teoremas_explicacion: Explicación de los teoremas de dualidad.
    """
    primal: Optional[Problema] = None
    dual: Optional[Problema] = None
    pasos_construccion: List[str] = field(default_factory=list)
    correspondencia: CorrespondenciaDual = field(default_factory=CorrespondenciaDual)
    resultado_primal: Optional[Resultado] = None
    resultado_dual: Optional[Resultado] = None
    dualidad_fuerte: bool = False
    valor_primal: Optional[float] = None
    valor_dual: Optional[float] = None
    holgura_complementaria: HolguraComplementaria = field(
        default_factory=HolguraComplementaria
    )
    mensaje_verificacion: str = ""
    teoremas_explicacion: str = ""


# ─────────────────────────────────────────────────────────────────────────────
#  Clase principal
# ─────────────────────────────────────────────────────────────────────────────

class AlgoritmoDualidad:
    """
    Motor del algoritmo de dualidad educativo.

    Uso típico::

        algo = AlgoritmoDualidad(problema_primal)
        resultado = algo.construir_y_resolver()
    """

    _EPSILON = 1e-8

    def __init__(self, primal: Problema, modo_algebraico: bool = False) -> None:
        self.primal = primal
        self.modo_algebraico = modo_algebraico

    # ──────────────────────────────────────────────────────────────────────
    #  API pública
    # ──────────────────────────────────────────────────────────────────────

    def construir_dual(self) -> Tuple[Problema, List[str]]:
        """
        Construye el problema dual a partir del primal.

        Returns:
            (problema_dual, pasos_construccion)
        """
        primal = self.primal
        pasos: List[str] = []

        pasos.append("  CONSTRUCCION DEL PROBLEMA DUAL")
        pasos.append("")
        pasos.append("  PROBLEMA PRIMAL:")
        pasos.append(f"  {primal.funcion_objetivo_str()}")
        for r in primal.restricciones:
            pasos.append(f"  {self._rest_str_bonito(r)}")
        pasos.append(f"  {', '.join(primal.nombres_variables)} >= 0")
        pasos.append("")

        m = primal.num_restricciones  # restricciones primal → variables dual
        n = primal.num_variables      # variables primal → restricciones dual
        nombres_primal = primal.nombres_variables

        pasos.append("  RELACIONES PRIMAL -> DUAL:")
        pasos.append(f"  * {m} restricciones del primal -> {m} variables del dual (y1..y{m})")
        pasos.append(f"  * {n} variables del primal -> {n} restricciones del dual")
        pasos.append(f"  * Coeficientes del objetivo primal -> RHS del dual")
        pasos.append(f"  * RHS del primal -> Coeficientes del objetivo dual")
        pasos.append(f"  * Matriz A del primal -> Transpuesta At en el dual")
        pasos.append("")

        # ── Determinar tipo del dual ──────────────────────────────────────
        if primal.tipo == TipoOptimizacion.MAXIMIZAR:
            tipo_dual = TipoOptimizacion.MINIMIZAR
            pasos.append("  Primal es MAX -> Dual es MIN")
        else:
            tipo_dual = TipoOptimizacion.MAXIMIZAR
            pasos.append("  Primal es MIN -> Dual es MAX")
        pasos.append("")

        # ── Construir variables duales ────────────────────────────────────
        variables_duales: List[Variable] = []
        nombres_duales: List[str] = []
        for i, rest in enumerate(primal.restricciones):
            nombre_y = f"y{i + 1}"
            nombres_duales.append(nombre_y)
            # Signo de la variable dual según tipo de restricción del primal MAX
            if primal.tipo == TipoOptimizacion.MAXIMIZAR:
                if rest.tipo == TipoRestriccion.LEQ:
                    signo_str = ">= 0"
                elif rest.tipo == TipoRestriccion.GEQ:
                    signo_str = "<= 0"
                else:
                    signo_str = "libre"
            else:
                # Primal MIN
                if rest.tipo == TipoRestriccion.GEQ:
                    signo_str = ">= 0"
                elif rest.tipo == TipoRestriccion.LEQ:
                    signo_str = "<= 0"
                else:
                    signo_str = "libre"

            pasos.append(f"  Restriccion {rest.nombre} ({rest.tipo.value}) -> {nombre_y} {signo_str}")
            var_dual = Variable(
                nombre=nombre_y,
                tipo=TipoVariable.DECISION,
                coef_objetivo=rest.rhs,
                indice=i,
                no_negativa=(signo_str == ">= 0"),
            )
            variables_duales.append(var_dual)

        pasos.append("")

        # ── Coeficientes objetivo dual = RHS del primal ───────────────────
        coef_obj_dual: Dict[str, float] = {
            f"y{i + 1}": primal.restricciones[i].rhs
            for i in range(m)
        }

        # ── Construir restricciones duales (Aᵀy {>=/<= } c) ──────────────
        pasos.append("  TRANSPUESTA DE LA MATRIZ A:")
        # Extraer matriz A
        A = np.zeros((m, n))
        for i, rest in enumerate(primal.restricciones):
            for j, nombre_var in enumerate(nombres_primal):
                A[i, j] = rest.obtener_coef(nombre_var)

        At = A.T  # Transpuesta n×m
        pasos.append("  A (primal):")
        for i in range(m):
            fila_str = "  [" + "  ".join(f"{A[i, j]:6.2f}" for j in range(n)) + "  ]"
            pasos.append(fila_str)
        pasos.append("  At (dual):")
        for j in range(n):
            fila_str = "  [" + "  ".join(f"{At[j, i]:6.2f}" for i in range(m)) + "  ]"
            pasos.append(fila_str)
        pasos.append("")

        # Tipo de restricciones duales
        if primal.tipo == TipoOptimizacion.MAXIMIZAR:
            tipo_rest_dual = TipoRestriccion.GEQ  # Aᵀy >= c
        else:
            tipo_rest_dual = TipoRestriccion.LEQ  # Aᵀy <= c

        restricciones_duales: List[Restriccion] = []
        for j, nombre_xj in enumerate(nombres_primal):
            coefs_rest: Dict[str, float] = {}
            for i in range(m):
                coefs_rest[f"y{i + 1}"] = At[j, i]

            cj = primal.coef_objetivo.get(nombre_xj, 0.0)
            rest_dual = Restriccion(
                nombre=f"D{j + 1}",
                coeficientes=coefs_rest,
                tipo=tipo_rest_dual,
                rhs=cj,
                indice=j,
            )
            restricciones_duales.append(rest_dual)
            pasos.append(
                f"  Restriccion dual D{j + 1} (para {nombre_xj}): "
                f"{self._rest_str_bonito(rest_dual)}"
            )

        pasos.append("")

        # ── Construir el Problema dual ────────────────────────────────────
        dual = Problema(
            nombre=f"Dual de '{primal.nombre}'",
            tipo=tipo_dual,
            variables=variables_duales,
            restricciones=restricciones_duales,
            coef_objetivo=coef_obj_dual,
        )

        pasos.append("  PROBLEMA DUAL:")
        pasos.append(f"  {dual.funcion_objetivo_str()}")
        for r in dual.restricciones:
            pasos.append(f"  {self._rest_str_bonito(r)}")
        pasos.append(f"  {', '.join(nombres_duales)} >= 0")
        pasos.append("")

        return dual, pasos

    def construir_correspondencia(self, dual: Problema) -> CorrespondenciaDual:
        """Genera la tabla educativa de correspondencia Primal <-> Dual."""
        corr = CorrespondenciaDual()
        corr.filas = [
            ("PRIMAL", "DUAL"),
            ("-" * 30, "-" * 30),
            ("Funcion objetivo", f"{'Minimizar' if dual.tipo == TipoOptimizacion.MINIMIZAR else 'Maximizar'}"),
            ("Restriccion", "Variable"),
            ("Variable", "Restriccion"),
            ("Coeficientes obj. (c)", "RHS dual (b)"),
            ("RHS primal (b)", "Coeficientes obj. dual (c)"),
            ("Matriz A", "Matriz At"),
        ]
        for i, r in enumerate(self.primal.restricciones):
            corr.filas.append((
                f"  Restriccion {r.nombre} ({r.tipo.value})",
                f"  Variable y{i + 1}",
            ))
        for i, v in enumerate(self.primal.variables):
            corr.filas.append((
                f"  Variable {v.nombre}",
                f"  Restriccion D{i + 1}",
            ))
        return corr

    def resolver_primal(self) -> Resultado:
        """Resuelve el problema primal."""
        from algorithms.forma_estandar import convertir_a_forma_estandar
        pe = convertir_a_forma_estandar(self.primal)
        if pe.tiene_artificiales:
            solver = DosFases(self.primal, modo_algebraico=self.modo_algebraico)
        else:
            solver = AlgoritmoSimplex(self.primal, modo_algebraico=self.modo_algebraico)
        return solver.resolver()

    def resolver_dual(self, dual: Problema) -> Resultado:
        """Resuelve el problema dual."""
        from algorithms.forma_estandar import convertir_a_forma_estandar
        pe = convertir_a_forma_estandar(dual)
        if pe.tiene_artificiales:
            solver = DosFases(dual, modo_algebraico=self.modo_algebraico)
        else:
            solver = AlgoritmoSimplex(dual, modo_algebraico=self.modo_algebraico)
        return solver.resolver()

    def verificar_dualidad_fuerte(
        self,
        res_primal: Resultado,
        res_dual: Resultado,
    ) -> Tuple[bool, str]:
        """
        Verifica el Teorema de Dualidad Fuerte: Z* = W*.

        Returns:
            (cumple, mensaje_educativo)
        """
        if res_primal.estado not in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES):
            return False, "El primal no tiene solucion optima."
        if res_dual.estado not in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES):
            return False, "El dual no tiene solucion optima."

        z = res_primal.valor_objetivo
        w = res_dual.valor_objetivo

        if z is None or w is None:
            return False, "No se pudo obtener el valor objetivo."

        cumple = abs(z - w) < self._EPSILON

        if cumple:
            msg = (
                "  TEOREMA DE DUALIDAD FUERTE VERIFICADO\n\n"
                f"  Z* (primal) = {format_number(z)}\n"
                f"  W* (dual)   = {format_number(w)}\n\n"
                "  Z* = W*\n\n"
                "  Esto confirma que ambos problemas tienen la misma\n"
                "  solucion optima y el gap de dualidad es cero."
            )
        else:
            msg = (
                "  DUALIDAD FUERTE NO VERIFICADA\n\n"
                f"  Z* (primal) = {format_number(z)}\n"
                f"  W* (dual)   = {format_number(w)}\n\n"
                f"  Diferencia = {format_number(abs(z - w))}\n\n"
                "  Posible causa: error numerico o problema con soluciones\n"
                "  multiples / degenerado."
            )
        return cumple, msg

    def verificar_holgura_complementaria(
        self,
        res_primal: Resultado,
        res_dual: Resultado,
        dual: Problema,
    ) -> HolguraComplementaria:
        """
        Verifica las condiciones de holgura complementaria:

        Para cada restriccion i del primal:
          y_i * (b_i - sum a_ij * x_j) = 0

        Para cada variable j del primal:
          x_j * (sum a_ij * y_i - c_j) = 0
        """
        hc = HolguraComplementaria()
        eps = self._EPSILON

        x_vals = res_primal.valores_variables
        y_vals = res_dual.valores_variables

        # Condicion sobre y_i (restricciones primal)
        for i, rest in enumerate(self.primal.restricciones):
            yi_nombre = f"y{i + 1}"
            yi = y_vals.get(yi_nombre, 0.0)

            # Calcular holgura/exceso de la restriccion
            suma = sum(
                rest.obtener_coef(nombre) * x_vals.get(nombre, 0.0)
                for nombre in self.primal.nombres_variables
            )
            slack = rest.rhs - suma  # bi - Ai·x

            producto = yi * slack
            cumple = abs(producto) < eps

            desc = (
                f"  y{i+1} * (b{i+1} - A{i+1}*x) = "
                f"{format_number(yi)} * {format_number(slack)} = "
                f"{format_number(producto)} {'OK' if cumple else 'FALLA'}"
            )
            hc.condicion_yi.append(desc)
            hc.cumple_yi.append(cumple)

        # Condicion sobre x_j (variables primal -> restricciones dual)
        for j, var_primal in enumerate(self.primal.variables):
            xj = x_vals.get(var_primal.nombre, 0.0)

            # Calcular slack de la restriccion dual D_j
            # Restriccion dual: sum_i a_ij * y_i {>= / <=} c_j
            suma_dual = sum(
                self.primal.restricciones[i].obtener_coef(var_primal.nombre)
                * y_vals.get(f"y{i + 1}", 0.0)
                for i in range(self.primal.num_restricciones)
            )
            cj = self.primal.coef_objetivo.get(var_primal.nombre, 0.0)
            slack_dual = suma_dual - cj  # At*y - c

            producto = xj * slack_dual
            cumple = abs(producto) < eps

            desc = (
                f"  {var_primal.nombre} * (At*y - c_{j+1}) = "
                f"{format_number(xj)} * {format_number(slack_dual)} = "
                f"{format_number(producto)} {'OK' if cumple else 'FALLA'}"
            )
            hc.condicion_xj.append(desc)
            hc.cumple_xj.append(cumple)

        hc.todas_cumplen = all(hc.cumple_yi) and all(hc.cumple_xj)
        return hc

    def generar_explicacion_teoremas(self) -> str:
        """Genera la explicacion educativa de los teoremas de dualidad."""
        lines = [
            "  TEOREMAS DE DUALIDAD",
            "",
            "  1. DUALIDAD DEBIL",
            "  -----------------",
            "  Si x es factible para el primal (MAX) y",
            "  y es factible para el dual (MIN), entonces:",
            "",
            "    c^T x <= b^T y",
            "",
            "  Es decir: cualquier solucion factible del primal",
            "  proporciona un limite inferior al dual, y viceversa.",
            "",
            "  2. DUALIDAD FUERTE",
            "  ------------------",
            "  Si el primal tiene solucion optima x*, entonces",
            "  el dual tambien tiene solucion optima y*, y:",
            "",
            "    Z* = c^T x* = b^T y* = W*",
            "",
            "  El gap de dualidad es cero en la solucion optima.",
            "",
            "  3. HOLGURA COMPLEMENTARIA",
            "  -------------------------",
            "  En la solucion optima se deben cumplir:",
            "",
            "  a) Para cada restriccion i del primal:",
            "     y_i * (b_i - Ai*x*) = 0",
            "     -> O la restriccion es activa (b_i = Ai*x*)",
            "        o la variable dual y_i = 0.",
            "",
            "  b) Para cada variable j del primal:",
            "     x_j * (At*y* - c_j) = 0",
            "     -> O la restriccion dual j es activa",
            "        o la variable primal x_j = 0.",
            "",
            "  Estas condiciones son necesarias y suficientes",
            "  para la optimalidad en PL.",
        ]
        return "\n".join(lines)

    def construir_y_resolver(self) -> ResultadoDualidad:
        """
        Ejecuta el flujo completo:
        1. Construye el dual.
        2. Resuelve primal y dual.
        3. Verifica dualidad fuerte.
        4. Verifica holgura complementaria.
        5. Genera explicaciones educativas.

        Returns:
            ResultadoDualidad con toda la informacion.
        """
        rd = ResultadoDualidad()
        rd.primal = self.primal

        # 1. Construir dual
        dual, pasos = self.construir_dual()
        rd.dual = dual
        rd.pasos_construccion = pasos

        # 2. Correspondencia
        rd.correspondencia = self.construir_correspondencia(dual)

        # 3. Resolver primal
        rd.resultado_primal = self.resolver_primal()

        # 4. Resolver dual
        rd.resultado_dual = self.resolver_dual(dual)

        rd.valor_primal = rd.resultado_primal.valor_objetivo
        rd.valor_dual = rd.resultado_dual.valor_objetivo

        # 5. Verificar dualidad fuerte
        rd.dualidad_fuerte, rd.mensaje_verificacion = self.verificar_dualidad_fuerte(
            rd.resultado_primal, rd.resultado_dual
        )

        # 6. Holgura complementaria
        if (
            rd.resultado_primal.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)
            and rd.resultado_dual.estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES)
        ):
            rd.holgura_complementaria = self.verificar_holgura_complementaria(
                rd.resultado_primal, rd.resultado_dual, dual
            )

        # 7. Teoremas
        rd.teoremas_explicacion = self.generar_explicacion_teoremas()

        return rd

    # ──────────────────────────────────────────────────────────────────────
    #  Helpers privados
    # ──────────────────────────────────────────────────────────────────────

    def _rest_str_bonito(self, rest: Restriccion) -> str:
        """Representacion legible de una restriccion."""
        terminos = []
        for var, coef in rest.coeficientes.items():
            coef = limpiar_cero(coef)
            if coef == 1.0:
                terminos.append(var)
            elif coef == -1.0:
                terminos.append(f"-{var}")
            elif coef != 0.0:
                terminos.append(f"{format_number(coef)}{var}")
        lado_izq = " + ".join(terminos).replace("+ -", "- ")
        return f"{lado_izq} {rest.tipo.value} {format_number(rest.rhs)}"
