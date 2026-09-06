"""
Widget de tabla Simplex — Tema claro con Verde Esmeralda y Azul Cielo.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Optional

from models.resultado import Iteracion
from utils.format_numbers import format_number
from config.config import APP_CONFIG
from gui.theme import (
    BG_CARD, BG_ROW_EVEN, BG_ROW_ODD, BG_HEADER_TBL, BG_ZJ_ROW,
    COLOR_PIVOT, COLOR_PIVOT_BG, COLOR_ENT_BG, COLOR_ENT_FG,
    COLOR_SAL_BG, COLOR_SAL_FG, COLOR_POSITIVE, COLOR_NEGATIVE,
    COLOR_NEUTRAL, BORDER_LIGHT, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_WHITE, EMERALD_DARK, SKY_DARK, FONT_FAMILY_MONO,
    BG_SEPARATOR, EMERALD_LIGHT, SKY_LIGHT,
)


class SimplexTableWidget(ctk.CTkFrame):
    """
    Muestra el tableau del Simplex — tema claro moderno.
    """

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", BG_CARD)
        kwargs.setdefault("corner_radius", 10)
        super().__init__(master, **kwargs)
        self._iteracion: Optional[Iteracion] = None
        self._decimales: int = APP_CONFIG.decimal_places
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    #  Construcción UI
    # ──────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Light.Vertical.TScrollbar",
                        background=BG_CARD, troughcolor=BG_SEPARATOR,
                        bordercolor=BORDER_LIGHT, arrowcolor=TEXT_SECONDARY)
        style.configure("Light.Horizontal.TScrollbar",
                        background=BG_CARD, troughcolor=BG_SEPARATOR,
                        bordercolor=BORDER_LIGHT, arrowcolor=TEXT_SECONDARY)

        self._canvas = tk.Canvas(self, bg=BG_CARD, highlightthickness=0)
        self._scroll_x = ttk.Scrollbar(self, orient="horizontal",
                                        command=self._canvas.xview,
                                        style="Light.Horizontal.TScrollbar")
        self._scroll_y = ttk.Scrollbar(self, orient="vertical",
                                        command=self._canvas.yview,
                                        style="Light.Vertical.TScrollbar")
        self._inner = tk.Frame(self._canvas, bg=BG_CARD)

        self._canvas.configure(
            xscrollcommand=self._scroll_x.set,
            yscrollcommand=self._scroll_y.set,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scroll_x.grid(row=1, column=0, sticky="ew")
        self._scroll_y.grid(row=0, column=1, sticky="ns")

        self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")
        ))

    # ──────────────────────────────────────────────────────────────────────
    #  Renderizado
    # ──────────────────────────────────────────────────────────────────────

    def mostrar_iteracion(self, iteracion: Iteracion):
        self._iteracion = iteracion
        self._limpiar()
        if not iteracion or not iteracion.tabla:
            return

        it = iteracion
        nombres_cols = it.nombres_columnas
        m = len(it.tabla)
        n_cols = len(nombres_cols)
        col_piv  = it.col_pivote
        fila_piv = it.fila_pivote

        # ── Fila de encabezado ────────────────────────────────────────────
        self._cell_header("Cb",   0, 0)
        self._cell_header("Base", 0, 1)
        for j, nombre in enumerate(nombres_cols):
            # Resaltar encabezado de columna entrante
            if col_piv is not None and j == col_piv:
                self._cell_header(nombre, 0, j + 2,
                                   bg=EMERALD_DARK, fg=TEXT_WHITE)
            elif nombre == "RHS":
                self._cell_header(nombre, 0, j + 2,
                                   bg=SKY_DARK, fg=TEXT_WHITE)
            else:
                self._cell_header(nombre, 0, j + 2)

        # ── Filas del tableau ─────────────────────────────────────────────
        for i in range(m):
            r = i + 1
            es_fila_sal = (fila_piv is not None and i == fila_piv)
            bg_row = COLOR_SAL_BG if es_fila_sal else (
                BG_ROW_EVEN if i % 2 == 0 else BG_ROW_ODD
            )
            fg_row = COLOR_SAL_FG if es_fila_sal else TEXT_PRIMARY

            # Cb
            cb_val = it.coefs_base[i] if i < len(it.coefs_base) else 0.0
            self._cell(format_number(cb_val, self._decimales), r, 0,
                       bg=bg_row, fg=TEXT_SECONDARY)

            # Variable base
            bv = it.variables_base[i] if i < len(it.variables_base) else "?"
            self._cell(bv, r, 1, bg=bg_row, fg=fg_row, bold=True)

            # Coeficientes
            for j, val in enumerate(it.tabla[i]):
                cell_bg = bg_row
                cell_fg = fg_row
                bold    = False

                if col_piv is not None and fila_piv is not None \
                        and j == col_piv and i == fila_piv:
                    # Elemento pivote — naranja
                    cell_bg = COLOR_PIVOT
                    cell_fg = TEXT_WHITE
                    bold    = True
                elif col_piv is not None and j == col_piv:
                    # Columna entrante — verde esmeralda claro
                    cell_bg = COLOR_ENT_BG
                    cell_fg = COLOR_ENT_FG
                elif es_fila_sal:
                    # Fila saliente — amarillo
                    cell_bg = COLOR_SAL_BG
                    cell_fg = COLOR_SAL_FG
                    bold    = True

                self._cell(format_number(val, self._decimales),
                           r, j + 2, bg=cell_bg, fg=cell_fg, bold=bold)

        # ── Separador ─────────────────────────────────────────────────────
        sep_r = m + 1
        for j in range(n_cols + 2):
            lbl = tk.Label(
                self._inner, text="",
                bg=BORDER_LIGHT, height=1,
            )
            lbl.grid(row=sep_r, column=j, sticky="ew",
                     padx=1, pady=0, ipady=0)

        # ── Fila Zj ───────────────────────────────────────────────────────
        zj_r = m + 2
        self._cell_label("Zj",    zj_r, 0, colspan=2,
                          bg=EMERALD_LIGHT, fg=EMERALD_DARK)
        for j, val in enumerate(it.zj if it.zj else []):
            self._cell(format_number(val, self._decimales),
                       zj_r, j + 2, bg=EMERALD_LIGHT, fg=EMERALD_DARK)

        # ── Fila Cj-Zj ────────────────────────────────────────────────────
        cz_r = m + 3
        self._cell_label("Cj-Zj", cz_r, 0, colspan=2,
                          bg=SKY_LIGHT, fg=SKY_DARK)
        for j, val in enumerate(it.cj_zj if it.cj_zj else []):
            if abs(val) < 1e-9:
                fg = COLOR_NEUTRAL
            elif val > 0:
                fg = COLOR_POSITIVE
            else:
                fg = COLOR_NEGATIVE

            # Resaltar columna entrante en Cj-Zj
            is_entering = (
                it.variable_entrante is not None
                and j < len(nombres_cols) - 1
                and nombres_cols[j] == it.variable_entrante
            )
            bg_cz = EMERALD_LIGHT if is_entering else SKY_LIGHT
            bold_cz = is_entering

            self._cell(format_number(val, self._decimales),
                       cz_r, j + 2, bg=bg_cz, fg=fg, bold=bold_cz)

    # ──────────────────────────────────────────────────────────────────────
    #  Helpers de celda
    # ──────────────────────────────────────────────────────────────────────

    def _cell_header(self, text, row, col,
                     bg=BG_HEADER_TBL, fg=SKY_DARK):
        lbl = tk.Label(
            self._inner, text=text,
            bg=bg, fg=fg,
            font=(FONT_FAMILY_MONO, 10, "bold"),
            width=10, height=1,
            padx=6, pady=4,
            relief="flat",
        )
        lbl.grid(row=row, column=col, sticky="nsew",
                 padx=1, pady=1)

    def _cell(self, text, row, col,
              bg=BG_ROW_EVEN, fg=TEXT_PRIMARY, bold=False):
        font = (FONT_FAMILY_MONO, 10, "bold") if bold else (FONT_FAMILY_MONO, 10)
        lbl = tk.Label(
            self._inner, text=text,
            bg=bg, fg=fg, font=font,
            width=10, height=1,
            padx=6, pady=3,
            relief="flat",
        )
        lbl.grid(row=row, column=col, sticky="nsew",
                 padx=1, pady=1)

    def _cell_label(self, text, row, col, colspan=1,
                    bg=BG_ZJ_ROW, fg=TEXT_PRIMARY):
        lbl = tk.Label(
            self._inner, text=text,
            bg=bg, fg=fg,
            font=(FONT_FAMILY_MONO, 10, "bold"),
            width=10 * colspan, height=1,
            padx=6, pady=3,
            relief="flat",
        )
        lbl.grid(row=row, column=col, columnspan=colspan,
                 sticky="nsew", padx=1, pady=1)

    def _limpiar(self):
        for w in self._inner.winfo_children():
            w.destroy()
