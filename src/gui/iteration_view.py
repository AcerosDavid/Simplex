"""
Panel de visualización de iteraciones — tema claro moderno.
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional

from models.resultado import Iteracion, Resultado, EstadoSolucion
from gui.widgets.simplex_table import SimplexTableWidget
from gui.theme import (
    BG_CARD, BG_CONTENT, BG_CODE, BORDER_LIGHT,
    EMERALD, EMERALD_DARK, EMERALD_LIGHT, SKY, SKY_DARK, SKY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_WHITE, TEXT_MUTED,
    STATE_OPTIMAL, STATE_MULTIPLE, STATE_UNBOUNDED, STATE_INFEASIBLE,
    FONT_FAMILY_UI, FONT_FAMILY_MONO, FONT_SIZE_SM, FONT_SIZE_MD,
    FONT_SIZE_LG,
)
from utils.format_numbers import format_number


class IterationView(ctk.CTkFrame):
    """
    Panel de iteraciones con navegación y explicación — tema claro.
    """

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", BG_CONTENT)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self._resultado: Optional[Resultado] = None
        self._idx: int = 0
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    #  UI
    # ──────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=2)

        # ── Barra de navegación ───────────────────────────────────────────
        nav = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=10,
            border_width=1, border_color=BORDER_LIGHT,
        )
        nav.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        nav.grid_columnconfigure(5, weight=1)

        btn_style = dict(
            width=36, height=30,
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=13, weight="bold"),
            fg_color=SKY_LIGHT, text_color=SKY_DARK,
            hover_color=SKY_DARK, corner_radius=6,
            border_width=0,
        )

        self._btn_first = ctk.CTkButton(nav, text="⏮", command=self._ir_primera,
                                         **btn_style)
        self._btn_prev  = ctk.CTkButton(nav, text="◀", command=self._ir_anterior,
                                         **btn_style)
        self._lbl_iter  = ctk.CTkLabel(
            nav, text="Iteración 0 de 0",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            text_color=TEXT_PRIMARY, width=170,
        )
        self._btn_next  = ctk.CTkButton(nav, text="▶", command=self._ir_siguiente,
                                         **btn_style)
        self._btn_last  = ctk.CTkButton(nav, text="⏭", command=self._ir_ultima,
                                         **btn_style)

        self._btn_first.grid(row=0, column=0, padx=(10, 3), pady=8)
        self._btn_prev.grid (row=0, column=1, padx=3, pady=8)
        self._lbl_iter.grid (row=0, column=2, padx=10, pady=8)
        self._btn_next.grid (row=0, column=3, padx=3, pady=8)
        self._btn_last.grid (row=0, column=4, padx=(3, 10), pady=8)

        self._lbl_estado = ctk.CTkLabel(
            nav, text="",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            text_color=STATE_OPTIMAL,
        )
        self._lbl_estado.grid(row=0, column=6, padx=16, pady=8, sticky="e")

        # ── Tabla Simplex ─────────────────────────────────────────────────
        self._table = SimplexTableWidget(
            self, corner_radius=10,
            border_width=1, border_color=BORDER_LIGHT,
        )
        self._table.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)

        # ── Panel de explicación ──────────────────────────────────────────
        exp_card = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=10,
            border_width=1, border_color=BORDER_LIGHT,
        )
        exp_card.grid(row=2, column=0, sticky="nsew", padx=12, pady=(4, 12))
        exp_card.grid_columnconfigure(0, weight=1)
        exp_card.grid_rowconfigure(1, weight=1)

        # Encabezado del panel de explicación
        hdr = ctk.CTkFrame(exp_card, fg_color=EMERALD_LIGHT, corner_radius=8,
                            height=32)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew",
                 padx=6, pady=(6, 0))
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr,
            text="📖  Explicación del paso",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            text_color=EMERALD_DARK,
        ).grid(row=0, column=0, sticky="w", padx=10, pady=4)

        self._txt_exp = ctk.CTkTextbox(
            exp_card,
            fg_color=BG_CODE,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=FONT_SIZE_SM),
            wrap="word",
            border_spacing=10,
        )
        self._txt_exp.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

    # ──────────────────────────────────────────────────────────────────────
    #  API pública
    # ──────────────────────────────────────────────────────────────────────

    def mostrar_resultado(self, resultado: Resultado):
        self._resultado = resultado
        self._idx = 0
        self._actualizar_vista()

    def limpiar(self):
        self._resultado = None
        self._idx = 0
        self._lbl_iter.configure(text="Iteración 0 de 0")
        self._lbl_estado.configure(text="")
        self._txt_exp.delete("1.0", "end")

    # ──────────────────────────────────────────────────────────────────────
    #  Navegación
    # ──────────────────────────────────────────────────────────────────────

    def _ir_primera(self):
        self._idx = 0; self._actualizar_vista()

    def _ir_ultima(self):
        if self._resultado:
            self._idx = len(self._resultado.iteraciones) - 1
            self._actualizar_vista()

    def _ir_anterior(self):
        if self._idx > 0:
            self._idx -= 1; self._actualizar_vista()

    def _ir_siguiente(self):
        if self._resultado and self._idx < len(self._resultado.iteraciones) - 1:
            self._idx += 1; self._actualizar_vista()

    def _actualizar_vista(self):
        if not self._resultado or not self._resultado.iteraciones:
            return
        total = len(self._resultado.iteraciones)
        it    = self._resultado.iteraciones[self._idx]

        fase_str = f"  (Fase {it.fase})" if it.fase else ""
        self._lbl_iter.configure(
            text=f"Iteración {self._idx} de {total - 1}{fase_str}"
        )

        if self._idx == total - 1:
            estado = self._resultado.estado
            badge = {
                EstadoSolucion.OPTIMA:     ("✓ Óptima",      STATE_OPTIMAL),
                EstadoSolucion.MULTIPLES:  ("∞ Múltiples",   STATE_MULTIPLE),
                EstadoSolucion.ILIMITADO:  ("⚠ Ilimitado",   STATE_UNBOUNDED),
                EstadoSolucion.INFACTIBLE: ("✗ Infactible",  STATE_INFEASIBLE),
            }.get(estado, ("", TEXT_MUTED))
            self._lbl_estado.configure(text=badge[0], text_color=badge[1])
        else:
            self._lbl_estado.configure(text="")

        self._table.mostrar_iteracion(it)

        self._txt_exp.configure(state="normal")
        self._txt_exp.delete("1.0", "end")
        self._txt_exp.insert("1.0", it.explicacion or "")
        self._txt_exp.configure(state="disabled")

        dis = "disabled"
        nor = "normal"
        self._btn_first.configure(state=nor if self._idx > 0 else dis)
        self._btn_prev.configure (state=nor if self._idx > 0 else dis)
        self._btn_next.configure (state=nor if self._idx < total - 1 else dis)
        self._btn_last.configure (state=nor if self._idx < total - 1 else dis)
