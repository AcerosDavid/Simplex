"""
Punto de entrada principal de la aplicación Simplex.
"""
import sys
import os

# Agregar el directorio raíz al path para importaciones relativas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Función principal — lanza la interfaz gráfica."""
    try:
        from gui.main_window import MainWindow
        app = MainWindow()
        app.mainloop()
    except ImportError as e:
        print(f"[INFO] GUI no disponible: {e}")
        print("Instala las dependencias: pip install customtkinter")
        print("\nEjecutando demo de consola...\n")
        demo_consola()
    except Exception as e:
        print(f"[ERROR] Error al iniciar la GUI: {e}")
        import traceback
        traceback.print_exc()


def demo_consola():
    """Demo en consola para verificar que el backend funciona."""
    from algorithms.parser import parsear_problema_completo
    from algorithms.validaciones import validar_problema
    from algorithms.forma_estandar import convertir_a_forma_estandar
    from algorithms.simplex import AlgoritmoSimplex

    print("=" * 60)
    print("  Simplex — Demo Consola")
    print("=" * 60)

    p = parsear_problema_completo(
        "Max Z = 3x1 + 5x2",
        ["2x1 + x2 <= 10", "x1 + 3x2 <= 15"],
        nombre="Ejemplo Dualidad",
    )
    solver = AlgoritmoSimplex(p)
    r = solver.resolver()
    print(f"\nEstado: {r.estado.value}")
    print(f"Z* = {r.valor_objetivo}")
    for k, v in r.valores_variables.items():
        if not k.startswith('s'):
            print(f"  {k} = {v}")
    print(f"\nIteraciones: {r.num_iteraciones}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
