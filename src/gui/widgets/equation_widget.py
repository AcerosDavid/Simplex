"""
Widget para mostrar ecuaciones matemáticas como texto formateado.
"""
import customtkinter as ctk


class EquationWidget(ctk.CTkLabel):
    """
    Etiqueta estilizada para mostrar expresiones matemáticas.
    """

    def __init__(self, master, equation: str = "", **kwargs):
        kwargs.setdefault("font", ctk.CTkFont(family="Consolas", size=13))
        kwargs.setdefault("text_color", "#E0E0E0")
        super().__init__(master, text=equation, **kwargs)

    def set_equation(self, text: str):
        self.configure(text=text)
