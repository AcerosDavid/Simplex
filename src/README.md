# SimplexEdu — Sistema Educativo de Programación Lineal

Aplicación de escritorio educativa para resolver problemas de **Programación Lineal** paso a paso, enfocada en el **Método Simplex** y la **Teoría de Dualidad**.

---

## ¿Qué hace el programa?

- Resuelve problemas de PL con el **Método Simplex** completo (no usa solvers externos).
- Muestra **cada iteración** del algoritmo con tablas, explicaciones matemáticas y colores.
- Convierte el problema a **Forma Estándar** con explicación de cada variable auxiliar.
- Implementa el **Método de las Dos Fases** y el **Método de la Gran M**.
- Construye automáticamente el **Problema Dual** con explicación de la transposición.
- Verifica el **Teorema de Dualidad Fuerte** (Z\* = W\*).
- Verifica las condiciones de **Holgura Complementaria**.
- Detecta: solución óptima, problema ilimitado, infactible y soluciones múltiples.
- Incluye **5 ejemplos precargados**.

---

## Requisitos

- Python 3.11 o superior
- Sistema operativo: Windows, macOS o Linux

---

## Instalación

```bash
# 1. Clonar o descargar el proyecto
cd programacion_lineal

# 2. Instalar dependencias
pip install -r requirements.txt
```

---

## Ejecución

```bash
python main.py
```

---

## Dependencias (`requirements.txt`)

```
customtkinter>=5.2.0
numpy>=1.26.0
sympy>=1.12
pandas>=2.1.0
matplotlib>=3.8.0
reportlab>=4.1.0
openpyxl>=3.1.2
Pillow>=10.0.0
```

---

## Cómo ingresar un problema

### Función objetivo
```
Max Z = 3x1 + 5x2
Min Z = 2x1 - x2 + 4x3
```

### Restricciones (una por línea)
```
2x1 + 3x2 <= 12
4x1 + 2x2 <= 16
x1 + x2 >= 4
x1 + 2x2 = 8
```

Los nombres de variables pueden ser: `x1`, `x2`, `x10`, etc.

---

## Cómo usar el Método Simplex

1. Hacer clic en **Nuevo Problema** en el menú lateral.
2. Ingresar la función objetivo y las restricciones.
3. Seleccionar el método para variables artificiales (Dos Fases recomendado).
4. Hacer clic en **Resolver con Simplex**.
5. Navegar entre iteraciones con los botones `|< < > >|`.
6. Leer la explicación matemática en el panel inferior.

---

## Cómo usar el Método de Dualidad

1. Ingresar el problema primal.
2. Hacer clic en **Resolver con Dualidad**.
3. La aplicación mostrará:
   - Problema dual construido paso a paso
   - Tabla de correspondencia Primal ↔ Dual
   - Iteraciones del primal y del dual
   - Verificación de dualidad fuerte
   - Holgura complementaria

---

## Ejemplos precargados

| Ejemplo | Descripción |
|---|---|
| Ejemplo 1 — Simplex Básico | Max Z = 3x1 + 5x2 con restricciones <= |
| Ejemplo 2 — Dos Fases | Problema con restricción >= |
| Ejemplo 3 — Igualdad | Problema con restricción = |
| Ejemplo 4 — Minimización | Min Z con restricciones >= |
| Ejemplo 5 — Dualidad | Primal diseñado para demostrar dualidad |

---

## Estructura del proyecto

```
programacion_lineal/
├── main.py                        # Punto de entrada
├── requirements.txt
├── README.md
│
├── config/
│   └── config.py                  # Configuración global (AppConfig)
│
├── models/
│   ├── variable.py                # Clase Variable (decisión, holgura, artificial...)
│   ├── restriccion.py             # Clase Restriccion con tipo (<=, >=, =)
│   ├── problema.py                # Clase Problema (función obj + restricciones)
│   └── resultado.py               # Clases Resultado, Iteracion, OperacionFila
│
├── algorithms/
│   ├── parser.py                  # Texto → Problema (parser de expresiones)
│   ├── validaciones.py            # Validación antes de resolver
│   ├── forma_estandar.py          # Conversión a Forma Estándar
│   ├── simplex.py                 # Algoritmo Simplex completo (tableau real)
│   ├── dos_fases.py               # Método de las Dos Fases
│   ├── gran_m.py                  # Método de la Gran M
│   └── dualidad.py                # Construcción y resolución del dual
│
├── gui/
│   ├── main_window.py             # Ventana principal + menú lateral
│   ├── problem_input.py           # Panel de entrada del problema
│   ├── simplex_view.py            # Vista Simplex (Forma estándar + Iteraciones + Resultados)
│   ├── duality_view.py            # Vista Dualidad (Construcción + Verificación)
│   ├── iteration_view.py          # Navegación entre iteraciones
│   ├── results_view.py            # Panel de resultados finales
│   └── widgets/
│       ├── simplex_table.py       # Tabla del tableau con resaltado visual
│       └── equation_widget.py     # Etiqueta para expresiones matemáticas
│
├── utils/
│   ├── format_numbers.py          # Formateo de números (decimal/fracción)
│   └── helpers.py                 # Funciones auxiliares
│
├── examples/
│   ├── simplex_examples.py        # 5 ejemplos precargados
│   └── duality_examples.py        # Ejemplos para dualidad
│
└── tests/
    ├── test_parser.py             # 12 pruebas del parser
    ├── test_standard_form.py      # 6 pruebas de la forma estándar
    ├── test_simplex.py            # 11 pruebas del algoritmo Simplex
    └── test_duality.py            # 10 pruebas de dualidad  ← 41 total
```

---

## Ejecutar pruebas

```bash
python -m pytest tests/ -v
```

---

## Colores en la tabla Simplex

| Color | Significado |
|---|---|
| Naranja | Elemento pivote (intersección fila/columna pivote) |
| Verde azul | Columna de la variable entrante |
| Amarillo | Fila de la variable saliente |
| Rojo en Cj-Zj | Valor negativo (empeoraría el objetivo) |
| Verde en Cj-Zj | Valor favorable |

---

## Algoritmo matemático

El Simplex implementado sigue estos pasos en cada iteración:

1. Calcular `Zj = Σ(Cb · columna j)` para cada variable.
2. Calcular `Cj - Zj` para cada variable.
3. **Variable entrante:** mayor `Cj-Zj > 0` (max) o menor `Cj-Zj < 0` (min).
4. **Prueba de razón mínima (θ-test):** `min(RHS / aij)` para `aij > 0`.
5. **Variable saliente:** la de menor razón positiva.
6. **Pivoteo:** normalizar fila pivote; eliminar en demás filas.
7. **Criterio de parada:** todos `Cj-Zj ≤ 0` (max) o `≥ 0` (min).

---

## Notas

- El algoritmo implementa internamente el tableau y todas las operaciones de fila. No usa `scipy.optimize.linprog` ni ningún solver externo para las iteraciones.
- La precisión numérica usa una tolerancia `ε = 1e-10` para evitar errores de punto flotante.
- Las variables artificiales se manejan con Dos Fases o Gran M seleccionable por el usuario.
