# Resumen de Documentación Técnica: Proyecto STT (Vosk vs Whisper) 📝

Este documento sirve como memoria de la sesión de trabajo realizada para estructurar la explicación académica del proyecto. Toda la lógica se encuentra detallada paso a paso en el archivo `codigos.md`.

## 🏗️ Estructura del Proyecto

El sistema está dividido en tres pilares fundamentales que trabajan en conjunto como un equipo coordinado:

1.  **`modulo_vosk.py` (Respuesta Rápida)**: 
    *   Usa el motor Kaldi. 
    *   **Analía**: El intérprete de restaurante / Traductor de oficina.
2.  **`modulos_wisper.py` (Precisión y Contexto)**: 
    *   Usa redes neuronales Transformer de OpenAI.
    *   **Analogía**: El erudito de biblioteca.
3.  **`juez.py` (El Orquestador Central)**: 
    *   Gestiona el micrófono, los menús y la lógica de comparación.
    *   **Analogía**: El árbitro de boxeo.

---

## 💡 Conceptos Clave para la Explicación

### 1. El Manejo de Audio (Buffers y Chunks)
Explicamos por qué no le damos todo el audio de golpe a la IA:
*   Usar un **Buffer de 4000 frames** (0.25 seg) permite un equilibrio entre carga de CPU y latencia para que la transcripción parezca instantánea.

### 2. Normalización de Datos
Para Whisper, el audio debe ser "preparado" matemáticamente:
*   Dividir el audio por **32768** convierte los pulsos eléctricos del micrófono en decimales entre -1 y 1, que es el lenguaje que entiende la red neuronal.

### 3. Medición de Precisión (WER)
El **Word Error Rate** es nuestra métrica científica:
*   Compara la referencia contra el resultado y cuenta: Inserciones (sobran palabras), Borrados (faltan palabras) y Sustituciones (palabras cambiadas).

---

## 📜 Historial de Cambios en la Documentación

Durante esta sesión, se realizaron las siguientes mejoras en `codigos.md`:
*   ✅ **Unificación de Estilo**: Eliminación de etiquetas "técnico/cristiano" para crear un texto académico fluido.
*   ✅ **Desglose Modular**: División de cada archivo en bloques lógicos (Importaciones, Inicialización, Funciones Principales).
*   ✅ **Código Íntegro**: Actualización de los bloques de código para que sean literales y no resumidos, incluyendo todas las funciones de `juez.py`.
*   ✅ **Soporte Visual**: Inserción de gráficas en Mermaid para explicar la eficiencia de los frames y tablas comparativas para la arquitectura de Whisper.

---
*Este resumen ha sido generado para facilitar el estudio y la presentación de la lógica del Trabajo de Grado.*
