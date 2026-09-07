"""
Panel de entrada del problema de PL — tema claro moderno.
"""
import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional

from models.problema import Problema
from algorithms.parser import parsear_problema_completo, ParseError
from algorithms.validaciones import validar_problema
from examples.simplex_examples import EJEMPLOS
from gui.theme import (
    BG_CARD, BG_CONTENT, BG_INPUT, BG_CODE, BORDER_LIGHT, BORDER_MEDIUM,
    EMERALD, EMERALD_DARK, EMERALD_LIGHT,
    SKY, SKY_DARK, SKY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_WHITE,
    STATE_INFEASIBLE,
    FONT_FAMILY_UI, FONT_FAMILY_MONO,
    FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL,
)


class ProblemInputPanel(ctk.CTkFrame):
    """Panel de entrada del problema — tema claro."""

    def __init__(self, master, on_solve_simplex: Callable,
                 on_solve_duality: Callable, **kwargs):
        kwargs.setdefault("fg_color", BG_CONTENT)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)
        self._on_solve_simplex = on_solve_simplex
        self._on_solve_duality = on_solve_duality
        self._metodo = tk.StringVar(value="dos_fases")
        self._modo_simplex = tk.StringVar(value="tabular")
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────────
    #  UI
    # ──────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Encabezado ────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                            border_width=1, border_color=BORDER_LIGHT)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="📝  Ingresa tu Problema",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_XL, weight="bold"),
            text_color=EMERALD_DARK,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        # ── Tarjeta de entrada ────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER_LIGHT)
        card.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        card.grid_columnconfigure(0, weight=1)

        # Función objetivo
        ctk.CTkLabel(
            card,
            text="Función objetivo",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        self._entry_obj = ctk.CTkEntry(
            card,
            placeholder_text="Ej:  Max Z = 3x1 + 5x2",
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=13),
            height=40,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            border_color=BORDER_MEDIUM,
            border_width=1,
            corner_radius=8,
        )
        self._entry_obj.grid(row=1, column=0, sticky="ew",
                              padx=16, pady=(0, 10))

        # Restricciones
        ctk.CTkLabel(
            card,
            text="Restricciones  (una por línea)",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(4, 2))

        txt_frame = ctk.CTkFrame(card, fg_color=BG_INPUT, corner_radius=8,
                                  border_width=1, border_color=BORDER_MEDIUM)
        txt_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 10))
        txt_frame.grid_columnconfigure(0, weight=1)
        txt_frame.grid_rowconfigure(0, weight=1)

        self._txt_rest = ctk.CTkTextbox(
            txt_frame,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_FAMILY_MONO, size=12),
            height=120,
            wrap="none",
            border_spacing=10,
        )
        self._txt_rest.grid(row=0, column=0, sticky="nsew")

        # Método para artificiales
        met_frame = ctk.CTkFrame(card, fg_color=BG_CONTENT, corner_radius=8)
        met_frame.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            met_frame,
            text="Variables artificiales:",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_SM),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(8, 10))

        for texto, valor in [("Dos Fases", "dos_fases"), ("Gran M", "gran_m")]:
            ctk.CTkRadioButton(
                met_frame, text=texto,
                variable=self._metodo, value=valor,
                font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_SM),
                text_color=TEXT_PRIMARY,
                fg_color=EMERALD,
                hover_color=EMERALD_DARK,
            ).pack(side="left", padx=6, pady=6)

        # ── Modo de evaluación de la fila Z ────────────────────────────────
        modo_frame = ctk.CTkFrame(card, fg_color=BG_CONTENT, corner_radius=8)
        modo_frame.grid(row=5, column=0, sticky="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            modo_frame,
            text="Modo Simplex:",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_SM),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(8, 10))

        for texto, valor in [
            ("Tabular (Cj-Zj)", "tabular"),
            ("Algebraico (-Cj)", "algebraico"),
        ]:
            ctk.CTkRadioButton(
                modo_frame, text=texto,
                variable=self._modo_simplex, value=valor,
                font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_SM),
                text_color=TEXT_PRIMARY,
                fg_color=EMERALD,
                hover_color=EMERALD_DARK,
            ).pack(side="left", padx=6, pady=6)

        # ── Botones de acción ─────────────────────────────────────────────
        btn_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                                 border_width=1, border_color=BORDER_LIGHT)
        btn_card.grid(row=2, column=0, sticky="ew", padx=12, pady=6)
        btn_card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_card,
            text="▶  Resolver con Simplex",
            command=self._resolver_simplex,
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            fg_color=EMERALD, hover_color=EMERALD_DARK,
            text_color=TEXT_WHITE,
            height=42, corner_radius=8,
        ).grid(row=0, column=0, padx=(12, 4), pady=12, sticky="ew")

        ctk.CTkButton(
            btn_card,
            text="⇌  Resolver con Dualidad",
            command=self._resolver_dualidad,
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD, weight="bold"),
            fg_color=SKY_DARK, hover_color=SKY,
            text_color=TEXT_WHITE,
            height=42, corner_radius=8,
        ).grid(row=0, column=1, padx=4, pady=12, sticky="ew")

        ctk.CTkButton(
            btn_card,
            text="🗑  Limpiar",
            command=self._limpiar,
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD),
            fg_color=BG_CONTENT, hover_color=BORDER_LIGHT,
            text_color=TEXT_SECONDARY,
            border_color=BORDER_MEDIUM, border_width=1,
            height=42, corner_radius=8,
        ).grid(row=0, column=2, padx=(4, 12), pady=12, sticky="ew")

        # ── Ejemplos ──────────────────────────────────────────────────────
        ej_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                                border_width=1, border_color=BORDER_LIGHT)
        ej_card.grid(row=3, column=0, sticky="ew", padx=12, pady=6)

        ctk.CTkLabel(
            ej_card,
            text="💡  Cargar ejemplo:",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_MD),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(14, 8), pady=10)

        self._combo = ctk.CTkComboBox(
            ej_card,
            values=list(EJEMPLOS.keys()),
            command=self._cargar_ejemplo,
            width=340,
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_SM),
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            button_color=EMERALD,
            button_hover_color=EMERALD_DARK,
            border_color=BORDER_MEDIUM,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=EMERALD_LIGHT,
            corner_radius=8,
        )
        self._combo.pack(side="left", pady=10)

        # ── Mensaje de error ──────────────────────────────────────────────
        self._lbl_error = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=FONT_FAMILY_UI, size=FONT_SIZE_SM),
            text_color=STATE_INFEASIBLE,
            wraplength=520,
        )
        self._lbl_error.grid(row=4, column=0, sticky="w", padx=16, pady=4)

    # ──────────────────────────────────────────────────────────────────────
    #  Acciones
    # ──────────────────────────────────────────────────────────────────────

    def _resolver_simplex(self):
        p = self._parsear_y_validar()
        if p:
            self._on_solve_simplex(p, self._metodo.get(), self._modo_simplex.get())

    def _resolver_dualidad(self):
        p = self._parsear_y_validar()
        if p:
            self._on_solve_duality(p, self._modo_simplex.get())

    def _limpiar(self):
        self._entry_obj.delete(0, "end")
        self._txt_rest.delete("1.0", "end")
        self._lbl_error.configure(text="")

    def _cargar_ejemplo(self, nombre: str):
        if nombre not in EJEMPLOS:
            return
        p = EJEMPLOS[nombre]()
        self._entry_obj.delete(0, "end")
        self._entry_obj.insert(0, p.funcion_objetivo_str())
        self._txt_rest.delete("1.0", "end")
        for rest in p.restricciones:
            terminos = []
            for var, coef in rest.coeficientes.items():
                if coef == 1.0:
                    terminos.append(var)
                elif coef == -1.0:
                    terminos.append(f"-{var}")
                else:
                    terminos.append(f"{coef}{var}")
            lado_izq = " + ".join(terminos).replace("+ -", "- ")
            self._txt_rest.insert("end", f"{lado_izq} {rest.tipo.value} {rest.rhs}\n")
        self._lbl_error.configure(text="")

    def _parsear_y_validar(self) -> Optional[Problema]:
        obj  = self._entry_obj.get().strip()
        rest = self._txt_rest.get("1.0", "end").strip()

        if not obj:
            self._lbl_error.configure(text="⚠  Ingresa la función objetivo.")
            return None
        if not rest:
            self._lbl_error.configure(text="⚠  Ingresa al menos una restricción.")
            return None

        lineas = [l for l in rest.split("\n") if l.strip()]
        try:
            problema = parsear_problema_completo(obj, lineas)
        except ParseError as e:
            self._lbl_error.configure(text=f"⚠  Error de análisis:\n{e}")
            return None
        except Exception as e:
            self._lbl_error.configure(text=f"⚠  Error inesperado:\n{e}")
            return None

        ok, errores = validar_problema(problema)
        if not ok:
            self._lbl_error.configure(text="\n".join(errores))
            return None

        self._lbl_error.configure(text="")
        return problema
