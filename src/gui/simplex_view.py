"""
Vista completa del método Simplex — tema claro moderno.
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional

from models.resultado import Resultado, EstadoSolucion
from models.problema import Problema
from algorithms.simplex import AlgoritmoSimplex
from algorithms.dos_fases import DosFases
from algorithms.gran_m import GranM
from algorithms.forma_estandar import convertir_a_forma_estandar
from gui.iteration_view import IterationView
from gui.results_view import ResultsView
from gui.theme import (
    BG_CARD, BG_CONTENT, BG_CODE, BORDER_LIGHT, BORDER_MEDIUM,
    EMERALD_DARK, EMERALD_LIGHT, SKY_DARK, SKY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_FAMILY_UI, FONT_FAMILY_MONO, FONT_SIZE_SM, FONT_SIZE_LG,
)


class SimplexView(ctk.CTkFrame):
    """Vista principal del método Simplex con pestañas."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", BG_CONTENT)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self._resultado: Optional[Resultado] = None
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
            text="▶  Método Simplex",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_LG, weight="bold"),
            text_color=EMERALD_DARK,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=10)

        # Pestañas
        self._tabs = ctk.CTkTabview(
            self,
            fg_color=BG_CARD,
            segmented_button_fg_color=BG_CONTENT,
            segmented_button_selected_color=EMERALD_DARK,
            segmented_button_selected_hover_color=EMERALD_DARK,
            segmented_button_unselected_color=BG_CONTENT,
            segmented_button_unselected_hover_color=EMERALD_LIGHT,
            text_color=TEXT_SECONDARY,
            text_color_disabled=TEXT_SECONDARY,
            border_color=BORDER_LIGHT,
            border_width=1,
        )
        self._tabs.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        for tab in ["📋  Forma Estándar", "🔄  Iteraciones", "✅  Resultados"]:
            self._tabs.add(tab)
            self._tabs.tab(tab).grid_columnconfigure(0, weight=1)
            self._tabs.tab(tab).grid_rowconfigure(0, weight=1)

        # ── Pestaña Forma Estándar ────────────────────────────────────────
        tab_fe = self._tabs.tab("📋  Forma Estándar")
        self._txt_estandar = ctk.CTkTextbox(
            tab_fe,
            fg_color=BG_CODE,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=11),
            wrap="word",
            border_spacing=10,
        )
        self._txt_estandar.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # ── Pestaña Iteraciones ───────────────────────────────────────────
        self._iter_view = IterationView(self._tabs.tab("🔄  Iteraciones"))
        self._iter_view.grid(row=0, column=0, sticky="nsew")

        # ── Pestaña Resultados ────────────────────────────────────────────
        self._results_view = ResultsView(self._tabs.tab("✅  Resultados"))
        self._results_view.grid(row=0, column=0, sticky="nsew")

    # ──────────────────────────────────────────────────────────────────────
    #  API pública
    # ──────────────────────────────────────────────────────────────────────

    def resolver(self, problema: Problema, metodo: str = "dos_fases"):
        # Forma estándar
        pe = convertir_a_forma_estandar(problema)
        self._txt_estandar.configure(state="normal")
        self._txt_estandar.delete("1.0", "end")
        for paso in pe.pasos_conversion:
            self._txt_estandar.insert("end", paso + "\n")
        self._txt_estandar.configure(state="disabled")

        # Resolver
        if pe.tiene_artificiales:
            solver = GranM(problema) if metodo == "gran_m" else DosFases(problema)
        else:
            solver = AlgoritmoSimplex(problema)

        resultado = solver.resolver()
        self._resultado = resultado

        self._iter_view.mostrar_resultado(resultado)
        self._results_view.mostrar_resultado(resultado)
        self._tabs.set("🔄  Iteraciones")
        return resultado

    def limpiar(self):
        self._iter_view.limpiar()
        self._results_view.limpiar()
        self._txt_estandar.configure(state="normal")
        self._txt_estandar.delete("1.0", "end")
        self._txt_estandar.configure(state="disabled")
