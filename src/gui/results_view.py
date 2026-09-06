"""
Panel de resultados finales — tema claro moderno.
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional

from models.resultado import Resultado, EstadoSolucion
from utils.format_numbers import format_number
from gui.theme import (
    BG_CARD, BG_CODE, BG_CONTENT, BORDER_LIGHT,
    EMERALD, EMERALD_DARK, EMERALD_LIGHT, EMERALD_MID,
    SKY_DARK, SKY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_WHITE,
    STATE_OPTIMAL, STATE_MULTIPLE, STATE_UNBOUNDED, STATE_INFEASIBLE,
    FONT_FAMILY_UI, FONT_FAMILY_MONO,
    FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL,
)


class ResultsView(ctk.CTkFrame):
    """Panel de resultados con tarjetas de variables y valor óptimo."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", BG_CONTENT)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Encabezado
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                            border_width=1, border_color=BORDER_LIGHT, height=44)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr,
            text="📊  Resultados de la Solución",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_LG, weight="bold"),
            text_color=EMERALD_DARK,
        ).grid(row=0, column=0, sticky="w", padx=14, pady=10)

        # Área de texto con scroll
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER_LIGHT)
        card.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        self._txt = ctk.CTkTextbox(
            card,
            fg_color=BG_CODE,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=FONT_SIZE_SM),
            wrap="word",
            border_spacing=10,
        )
        self._txt.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Tags de color
        self._txt.tag_config("titulo",
            foreground=EMERALD_DARK,
        )
        self._txt.tag_config("subtitulo",
            foreground=EMERALD_DARK,
        )
        self._txt.tag_config("z_value",
            foreground=SKY_DARK,
        )
        self._txt.tag_config("var",
            foreground=TEXT_PRIMARY,
        )
        self._txt.tag_config("var_bold",
            foreground=EMERALD_DARK,
        )
        self._txt.tag_config("error",
            foreground=STATE_INFEASIBLE,
        )
        self._txt.tag_config("warning",
            foreground=STATE_UNBOUNDED,
        )
        self._txt.tag_config("info",
            foreground=TEXT_SECONDARY,
        )
        self._txt.tag_config("sep",
            foreground=BORDER_LIGHT,
        )
        self._txt.tag_config("multiple",
            foreground=STATE_MULTIPLE,
        )

    # ──────────────────────────────────────────────────────────────────────
    #  API pública
    # ──────────────────────────────────────────────────────────────────────

    def mostrar_resultado(self, resultado: Resultado):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")

        estado = resultado.estado
        ins = self._txt.insert  # alias

        sep = "─" * 48

        if estado in (EstadoSolucion.OPTIMA, EstadoSolucion.MULTIPLES):
            if estado == EstadoSolucion.OPTIMA:
                ins("end", "  ✓  SOLUCIÓN ÓPTIMA\n", "titulo")
            else:
                ins("end", "  ∞  SOLUCIONES MÚLTIPLES\n", "titulo")
            ins("end", f"  {sep}\n\n", "sep")

            # Variables de decisión
            ins("end", "  Variables de decisión\n", "subtitulo")
            primal = [
                n for n in resultado.valores_variables
                if not any(n.startswith(p) for p in ('s', 'a', 'e'))
            ]
            for nombre in primal:
                val = resultado.valores_variables[nombre]
                ins("end", f"    {nombre}", "var_bold")
                ins("end", f"  =  {format_number(val)}\n", "var")

            # Variables de holgura
            slack = [n for n in resultado.valores_variables if n.startswith('s')]
            if slack:
                ins("end", "\n  Variables de holgura\n", "subtitulo")
                for nombre in slack:
                    val = resultado.valores_variables[nombre]
                    ins("end", f"    {nombre}", "info")
                    ins("end", f"  =  {format_number(val)}\n", "info")

            # Valor óptimo
            ins("end", f"\n  {sep}\n", "sep")
            ins("end",
                f"  Z*  =  {format_number(resultado.valor_objetivo)}\n",
                "z_value")
            ins("end", f"  {sep}\n\n", "sep")

            # Interpretación
            ins("end", "  Interpretación\n", "subtitulo")
            for nombre in primal:
                val = resultado.valores_variables[nombre]
                ins("end",
                    f"    {nombre} = {format_number(val)} unidades\n",
                    "info")
            direccion = "máximo" if (resultado.valor_objetivo or 0) >= 0 else "mínimo"
            ins("end",
                f"\n  El valor {direccion} de la función objetivo es "
                f"{format_number(resultado.valor_objetivo)}.\n",
                "info")

            ins("end", f"\n  Método:      {resultado.metodo}\n", "info")
            ins("end", f"  Iteraciones: {resultado.num_iteraciones}\n", "info")

            if estado == EstadoSolucion.MULTIPLES:
                ins("end",
                    "\n  ⚠  Existen infinitas soluciones óptimas.\n",
                    "multiple")
                ins("end",
                    "     Alguna variable no básica tiene  Cj-Zj = 0.\n",
                    "info")

        elif estado == EstadoSolucion.ILIMITADO:
            ins("end", "  ⚠  PROBLEMA ILIMITADO\n\n", "warning")
            ins("end", f"  {resultado.mensaje}\n", "info")

        elif estado == EstadoSolucion.INFACTIBLE:
            ins("end", "  ✗  PROBLEMA INFACTIBLE\n\n", "error")
            ins("end", f"  {resultado.mensaje}\n", "info")

        else:
            ins("end", resultado.mensaje or "Sin resultado.", "info")

        self._txt.configure(state="disabled")

    def limpiar(self):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")
