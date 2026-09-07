"""
Vista del método de Dualidad — tema claro moderno.
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional

from models.problema import Problema
from algorithms.dualidad import AlgoritmoDualidad, ResultadoDualidad
from gui.iteration_view import IterationView
from gui.theme import (
    BG_CARD, BG_CONTENT, BG_CODE, BORDER_LIGHT,
    EMERALD, EMERALD_DARK, EMERALD_LIGHT,
    SKY_DARK, SKY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATE_OPTIMAL, STATE_INFEASIBLE,
    FONT_FAMILY_UI, FONT_FAMILY_MONO, FONT_SIZE_SM, FONT_SIZE_LG,
)
from utils.format_numbers import format_number


class DualityView(ctk.CTkFrame):
    """Vista completa del análisis de Dualidad."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", BG_CONTENT)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self._rd: Optional[ResultadoDualidad] = None
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Encabezado
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                            border_width=1, border_color=BORDER_LIGHT)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr,
            text="⇌  Dualidad",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_LG, weight="bold"),
            text_color=SKY_DARK,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=10)

        # Pestañas
        self._tabs = ctk.CTkTabview(
            self,
            fg_color=BG_CARD,
            segmented_button_fg_color=BG_CONTENT,
            segmented_button_selected_color=SKY_DARK,
            segmented_button_selected_hover_color=SKY_DARK,
            segmented_button_unselected_color=BG_CONTENT,
            segmented_button_unselected_hover_color=SKY_LIGHT,
            text_color=TEXT_SECONDARY,
            border_color=BORDER_LIGHT,
            border_width=1,
        )
        self._tabs.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        tab_names = [
            "📐  Construcción",
            "🔵  Primal",
            "🟢  Dual",
            "🔍  Verificación",
            "📚  Teoremas",
        ]
        for t in tab_names:
            self._tabs.add(t)
            self._tabs.tab(t).grid_columnconfigure(0, weight=1)
            self._tabs.tab(t).grid_rowconfigure(0, weight=1)

        # Construcción
        self._txt_construccion = self._make_text(
            self._tabs.tab("📐  Construcción"))

        # Primal
        self._iter_primal = IterationView(self._tabs.tab("🔵  Primal"))
        self._iter_primal.grid(row=0, column=0, sticky="nsew")

        # Dual
        self._iter_dual = IterationView(self._tabs.tab("🟢  Dual"))
        self._iter_dual.grid(row=0, column=0, sticky="nsew")

        # Verificación
        self._txt_verif = self._make_text(self._tabs.tab("🔍  Verificación"))

        # Teoremas
        self._txt_teoremas = self._make_text(self._tabs.tab("📚  Teoremas"))

    def _make_text(self, parent) -> tk.Text:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        txt = ctk.CTkTextbox(
            parent,
            fg_color=BG_CODE,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=11),
            wrap="word",
            border_spacing=10,
        )
        txt.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        return txt

    # ──────────────────────────────────────────────────────────────────────
    #  API pública
    # ──────────────────────────────────────────────────────────────────────

    def resolver(self, problema: Problema, modo_simplex: str = "tabular"):
        modo_algebraico = (modo_simplex == "algebraico")
        algo = AlgoritmoDualidad(problema, modo_algebraico=modo_algebraico)
        rd   = algo.construir_y_resolver()
        self._rd = rd

        # Construcción
        self._set_text(self._txt_construccion, "\n".join(rd.pasos_construccion))
        self._txt_construccion.configure(state="normal")
        self._txt_construccion.insert("end", "\n\n")
        self._txt_construccion.insert("end", "=" * 55 + "\n")
        self._txt_construccion.insert("end",
            "  TABLA DE CORRESPONDENCIA PRIMAL <-> DUAL\n")
        self._txt_construccion.insert("end", "=" * 55 + "\n\n")
        for izq, der in rd.correspondencia.filas:
            self._txt_construccion.insert(
                "end", f"  {izq:<38} {der}\n")
        self._txt_construccion.configure(state="disabled")

        # Iteraciones
        if rd.resultado_primal:
            self._iter_primal.mostrar_resultado(rd.resultado_primal)
        if rd.resultado_dual:
            self._iter_dual.mostrar_resultado(rd.resultado_dual)

        # Verificación
        lines = [rd.mensaje_verificacion, ""]
        hc = rd.holgura_complementaria
        if hc.condicion_yi:
            lines += [
                "=" * 50,
                "  HOLGURA COMPLEMENTARIA",
                "=" * 50, "",
                "  Condiciones sobre variables duales (y_i):",
            ]
            lines.extend(hc.condicion_yi)
            lines += [
                "",
                "  Condiciones sobre variables primales (x_j):",
            ]
            lines.extend(hc.condicion_xj)
            lines += [
                "",
                "  Resultado: " + (
                    "TODAS las condiciones se cumplen."
                    if hc.todas_cumplen
                    else "ALGUNA condicion no se cumple."
                ),
            ]

        if rd.valor_primal is not None and rd.valor_dual is not None:
            lines += [
                "",
                "=" * 50,
                "  COMPARACION",
                "=" * 50,
                f"  Z* primal = {format_number(rd.valor_primal)}",
                f"  W* dual   = {format_number(rd.valor_dual)}",
                f"  Dualidad fuerte: {'SI' if rd.dualidad_fuerte else 'NO'}",
            ]

        self._set_text(self._txt_verif, "\n".join(lines))
        self._set_text(self._txt_teoremas, rd.teoremas_explicacion)
        self._tabs.set("📐  Construcción")
        return rd

    def _set_text(self, txt: tk.Text, contenido: str):
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert("1.0", contenido)
        txt.configure(state="disabled")

    def limpiar(self):
        for t in (self._txt_construccion, self._txt_verif, self._txt_teoremas):
            self._set_text(t, "")
        self._iter_primal.limpiar()
        self._iter_dual.limpiar()
