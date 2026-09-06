"""
Ventana principal de Simplex — tema claro premium.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import customtkinter as ctk
import tkinter as tk
from typing import Optional

from config.config import APP_CONFIG
from models.problema import Problema
from gui.problem_input import ProblemInputPanel
from gui.simplex_view import SimplexView
from gui.duality_view import DualityView
from gui.theme import (
    BG_APP, BG_SIDEBAR, BG_CARD, BG_CONTENT,
    BORDER_LIGHT, BORDER_MEDIUM,
    EMERALD, EMERALD_DARK, EMERALD_LIGHT, EMERALD_MID,
    SKY, SKY_DARK, SKY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_WHITE,
    SIDEBAR_ACTIVE_BG, SIDEBAR_ACTIVE_FG, SIDEBAR_HOVER_BG,
    FONT_FAMILY_UI, FONT_FAMILY_MONO,
    FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    FONT_SIZE_XL, FONT_SIZE_2XL, FONT_SIZE_3XL, FONT_SIZE_HERO,
)

# ── CustomTkinter en modo claro ───────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")




class MainWindow(ctk.CTk):
    """
    Ventana principal de Simplex modificada a un solo panel sin menú superior.
    """

    def __init__(self):
        super().__init__()
        self._problema_actual: Optional[Problema] = None

        self._configurar_ventana()
        self._setup_ui()

    def _configurar_ventana(self):
        self.title(APP_CONFIG.app_title)
        self.geometry(f"{APP_CONFIG.window_width}x{APP_CONFIG.window_height}")
        self.minsize(APP_CONFIG.min_width, APP_CONFIG.min_height)
        self.configure(fg_color=BG_APP)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - APP_CONFIG.window_width)  // 2
        y = (self.winfo_screenheight() - APP_CONFIG.window_height) // 2
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)   # row 0=content

        self._build_content()

    def _build_content(self):
        self._content = ctk.CTkFrame(
            self, fg_color=BG_CONTENT, corner_radius=0
        )
        self._content.grid(row=0, column=0, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=0, minsize=420)
        self._content.grid_columnconfigure(1, weight=1)

        # Separador visual entre paneles
        sep = ctk.CTkFrame(self._content, width=1, fg_color=BORDER_LIGHT, corner_radius=0)
        sep.grid(row=0, column=0, sticky="nse")

        # Panel Izquierdo: Input
        self._panel_input = ProblemInputPanel(
            self._content,
            on_solve_simplex=self._ejecutar_simplex,
            on_solve_duality=self._ejecutar_dualidad,
            fg_color=BG_CONTENT,
        )
        self._panel_input.grid(row=0, column=0, sticky="nsew", padx=(0, 1), pady=0)

        # Panel Derecho: Resultados
        self._right_panel = ctk.CTkFrame(self._content, fg_color=BG_CONTENT, corner_radius=0)
        self._right_panel.grid(row=0, column=1, sticky="nsew")
        self._right_panel.grid_columnconfigure(0, weight=1)
        self._right_panel.grid_rowconfigure(0, weight=1)

        self._simplex_view  = SimplexView(self._right_panel)
        self._duality_view  = DualityView(self._right_panel)

        self._panel_inicio_simple = ctk.CTkLabel(
            self._right_panel,
            text="Ingrese un problema a la izquierda y haga clic en\nResolver para ver los resultados aquí.",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD)
        )
        self._panel_inicio_simple.grid(row=0, column=0, sticky="nsew")

    def _ejecutar_simplex(self, problema: Problema, metodo: str):
        self._panel_inicio_simple.grid_forget()
        self._duality_view.grid_forget()
        self._problema_actual = problema
        self._simplex_view.grid(row=0, column=0, sticky="nsew")
        self._simplex_view.resolver(problema, metodo)

    def _ejecutar_dualidad(self, problema: Problema):
        self._panel_inicio_simple.grid_forget()
        self._simplex_view.grid_forget()
        self._problema_actual = problema
        self._duality_view.grid(row=0, column=0, sticky="nsew")
        self._duality_view.resolver(problema)
