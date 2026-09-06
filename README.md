# Simplex Solver

Una aplicación de escritorio moderna desarrollada en Python con **CustomTkinter** para resolver problemas de **Programación Lineal** utilizando el Método Simplex y la Teoría de Dualidad.

## Características

- **Interfaz Gráfica Moderna (GUI)**: Diseño limpio, tema claro con un diseño de un solo panel para un uso rápido y sin distracciones.
- **Método Simplex Paso a Paso**: Permite visualizar las tablas (tableaus) de cada iteración, identificando la variable entrante, variable saliente y elemento pivote.
- **Manejo de Variables Artificiales**: Soporte automático para los métodos de **Dos Fases** y **Gran M** (útil para restricciones `>=` y `=`).
- **Forma Estándar Automática**: Conversión automática a la forma estándar, agregando variables de holgura, exceso y artificiales según corresponda, explicando cada paso.
- **Teoría de Dualidad**:
  - Construcción automática del problema Dual a partir del Primal.
  - Tabla de correspondencia Primal ↔ Dual.
  - Verificación de la dualidad fuerte ($Z^* = W^*$).
  - Condiciones de holgura complementaria.
- **Manejo de Casos Especiales**: Detecta y notifica sobre soluciones infinitas, soluciones óptimas múltiples, problemas sin cota (ilimitados) y problemas infactibles.
- **Ejemplos Precargados**: Incluye una lista de problemas de ejemplo para probar las funcionalidades de inmediato.

## Requisitos Previos

- Python 3.8 o superior.
- `customtkinter` (Librería para la interfaz gráfica).

Puedes instalar la dependencia ejecutando:

```bash
pip install customtkinter
```

## Ejecución

1. Clona el repositorio o descarga el código fuente.
2. Abre una terminal y navega hasta el directorio del proyecto.
3. Ejecuta el archivo principal (si estás en el directorio raíz y usas la carpeta `src/`):

```bash
cd src
python main.py
```

## Cómo Usar

### 1. Ingresar el problema
Puedes ingresar manualmente el problema en el panel izquierdo.
- **Función Objetivo**: Escribe en el formato `Max Z = 3x1 + 5x2` o `Min Z = 2x1 - x2 + 4x3`.
- **Restricciones**: Escribe cada restricción en una línea nueva. Ejemplo:
  ```
  2x1 + 3x2 <= 12
  4x1 + 2x2 <= 16
  x1 + x2 >= 4
  ```

### 2. Resolver con Simplex
Elige el método de resolución de variables artificiales (Dos Fases o Gran M) y haz clic en **Resolver con Simplex**. Observarás el paso a paso detallado en el panel derecho.

### 3. Resolver con Dualidad
Haz clic en **Resolver con Dualidad** para analizar el problema desde la perspectiva del Dual. Observarás cómo se construye la función y las restricciones duales.

---
**Desarrollado para facilitar el aprendizaje y la resolución de modelos matemáticos de optimización lineal.**
