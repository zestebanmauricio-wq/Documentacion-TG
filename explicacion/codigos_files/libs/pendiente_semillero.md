# Análisis Profundo de Evaluación con JiWER

JiWER (Just instance Word Error Rate) es una herramienta que utiliza el algoritmo de **Alineación Dinámica** (basado en Levenshtein) para comparar una "Referencia" (lo que el humano dijo) contra una "Hipótesis" (lo que la IA transcribió).

## 1. ¿Cómo funciona el proceso de revisión?

El motor de JiWER no compara frases completas como bloques de texto, sino que alinea las palabras una a una buscando el camino de menor resistencia (el número mínimo de ediciones necesarias para igualarlas).

### Los 3 Tipos de Errores que detecta:

1.  **Sustitución (S):** La palabra existe en la misma posición pero es diferente.
    *   *Referencia:* "El sistema **funciona** bien"
    *   *Hipótesis:* "El sistema **camina** bien"
    *   **Resultado:** 1 Sustitución.
2.  **Eliminación (D - Deletion):** La palabra se dijo pero la IA no la detectó.
    *   *Referencia:* "Hoy es **lunes** seis"
    *   *Hipótesis:* "Hoy es seis"
    *   **Resultado:** 1 Eliminación.
3.  **Inserción (I):** La IA "escuchó" una palabra que nunca se dijo (ruido ambiental o errores del modelo).
    *   *Referencia:* "Prueba de audio"
    *   *Hipótesis:* "Prueba **de de** audio"
    *   **Resultado:** 1 Inserción.

---

## 2. Ejemplo Paso a Paso: El cálculo del WER

Imagina esta prueba real en tu script `juez.py`:

*   **Referencia original:** "mi nombre es esteban" (N = 4 palabras)
*   **Transcripción IA:** "nombre es esteban mauricio"

### Alineación interna de JiWER:
| Referencia    | mi                  | nombre   | es       | esteban  | (vacío)           |
| :------------ | :------------------ | :------- | :------- | :------- | :---------------- |
| **Hipótesis** | (borrado)           | nombre   | es       | esteban  | mauricio          |
| **Acción**    | **Eliminación (D)** | Correcto | Correcto | Correcto | **Inserción (I)** |

**Conteo de errores:**
*   Sustituciones (S) = 0
*   Eliminaciones (D) = 1 (se perdió "mi")
*   Inserciones (I) = 1 (se inventó "mauricio")
*   Total de palabras referencia (N) = 4

**Cálculo final:**
$$WER = \frac{S + D + I}{N} = \frac{0 + 1 + 1}{4} = 0.50 \text{ (50\% de error)}$$

---

## 3. ¿Qué pasa con los puntos, comas y mayúsculas?

Este es el punto más crítico para tu proyecto. Por defecto, **JiWER es estrictamente literal**.

*   **Puntuación:** Si la referencia es `"Hola."` y la IA escribe `"Hola"`, JiWER cuenta una **Sustitución** porque `"Hola."` no es igual a `"Hola"`.
*   **Mayúsculas:** `"Esteban"` vs `"esteban"` se cuenta como error de sustitución.

### Tu estrategia en `juez.py`:
En tu código estás usando el método `.lower()`. Esto es fundamental porque:
1.  **Normaliza el texto:** Evita que el modelo falle por no usar mayúsculas al inicio.
2.  **Enfoque fonético:** En el semillero nos interesa si la IA entendió la palabra, no si puso la coma correctamente.

**Recomendación:** Para reportes más precisos, deberías limpiar los signos de puntuación de la referencia. Si tu referencia tiene puntos y la transcripción de Whisper no, el WER subirá aunque la transcripción sea perfecta fonéticamente.

---

## 4. Análisis Detallado de Métricas (Ventajas y Desventajas)

No todas las métricas sirven para lo mismo. Aquí tienes el desglose para que elijas la mejor para tu reporte:

### A. WER (Word Error Rate)
*   **Características:** Basado estrictamente en conteo de ediciones (Levenshtein).
*   **Ventajas:** Es el estándar de la industria; todo investigador de STT lo usa. Muy fácil de entender como "tasa de error".
*   **Desventajas:** Puede superar el 100% si hay muchas inserciones. Trata por igual errores graves (cambiar un nombre) que errores leves (quitar un "la").
*   **¿Qué analiza exactamente?:** Analiza la **fidelidad mecánica**. Es ideal cuando el orden y la cantidad exacta de palabras son críticos (ej: dictados legales o comandos de voz cortos).
*   **Ejemplo:**
    *   *Ref:* "hola mundo"
    *   *Hip:* "hola **a todos** mundo"
    *   **Resultado (WER): 100%** (2 errores / 2 palabras ref). El WER se dispara porque las palabras extra cuentan mucho.

### B. MER (Match Error Rate)
*   **Características:** Define el error como la probabilidad de que una palabra sea incorrecta.
*   **Ventajas:** Su valor siempre está entre 0 y 100%. Es más estable matemáticamente para hacer promedios de muchos audios.
*   **Desventajas:** Es menos intuitivo que el WER y no se usa tanto en publicaciones comerciales.
*   **¿Qué analiza exactamente?:** Analiza el **rendimiento por unidad de palabra**. Trata la transcripción como una serie de decisiones; cada palabra es una oportunidad de acierto o error, lo que lo hace más "justo" estadísticamente que el WER.
*   **Ejemplo:**
    *   *Ref:* "hola mundo"
    *   *Hip:* "hola **a todos** mundo"
    *   **Resultado (MER): 50%** (2 errores / 4 palabras totales). A diferencia del WER, aquí el error no llega al 100% porque se divide por la frase larga.

### C. WIL (Word Information Lost)
*   **Características:** Mide la pérdida de información mutua entre los textos.
*   **Ventajas:** **Es la métrica más humana.** Si el modelo cambia palabras sin importancia pero mantiene el mensaje, el WIL será bajo. Es ideal para evaluar transcripciones de reuniones largas.
*   **Desventajas:** La fórmula es compleja y difícil de explicar a personas que no son del área técnica.
*   **¿Qué analiza exactamente?:** Analiza la **entropía de la información**. Se fija en si el par de textos (Referencia e Hipótesis) son estadísticamente independientes. Si la IA falla en palabras "ruido" pero acierta en los sustantivos y verbos clave, el WIL dirá que hubo poca pérdida de información.
*   **Ejemplo:**
    *   *Ref:* "**hola** esteban"
    *   *Hip:* "**buenos dias** esteban"
    *   **Resultado (WIL): Muy bajo.** Aunque cambió "hola" por "buenos días", el WIL entiende que la información (saludo a Esteban) sigue ahí.

### D. WIP (Word Information Preserved)
*   **Características:** Complemento directo del WIL (1 - WIL).
*   **Ventajas:** Ideal para **gráficos de éxito**. Es más "vendedor" decir que el modelo "Preservó el 95% de la información" a decir que tuvo un "Error del 5%".
*   **Desventajas:** Misma complejidad matemática que el WIL.
*   **¿Qué analiza exactamente?:** Analiza la **supervivencia del mensaje**. Es una medida de correlación que responde a la pregunta: "¿Qué porcentaje del significado original sigue presente después de pasar por el motor de IA?".
*   **Ejemplo:**
    *   *Ref:* "clave secreta **123**"
    *   *Hip:* "clave secreta **456**"
    *   **Resultado (WIP): Muy bajo (ej: 20%).** Como cambió el dato más importante (el número), el WIP cae drásticamente porque la información útil no sobrevivió.

---

---

## 5. Implementación Técnica Sugerida

Para obtener todo lo anterior en tu código, puedes usar:

```python
import jiwer

# Creamos una transformación para limpiar el texto automáticamente
transformacion = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.RemoveWhiteSpace(replace_by_space=True),
    jiwer.RemoveMultipleSpaces(),
    jiwer.Strip(),
])

# Calculamos todas las medidas con el texto limpio
medidas = jiwer.compute_measures(
    referencia, 
    hipotesis, 
    truth_transform=transformacion, 
    hypothesis_transform=transformacion
)

print(f"WER Real: {medidas['wer']:.2%}")
```

---

## 7. Nota Crítica: El Desafío de la Puntuación (Vosk vs. Whisper)

Un factor que puede "engañar" a tus métricas en el semillero es cómo cada modelo maneja la puntuación:

### El problema
*   **Vosk:** Es un modelo de reconocimiento fonético puro. Entrega texto "crudo" (ej: `el sistema funciona bien`). No pone puntos, comas ni mayúsculas.
*   **Whisper:** Es un modelo de lenguaje completo. Entrega texto formateado (ej: `El sistema funciona bien.`).

### Impacto en JiWER
Si usas una **Referencia** con puntuación:
1.  **Whisper** tendrá un WER bajo porque sus puntos coincidirán con la referencia.
2.  **Vosk** tendrá un WER alto porque JiWER contará cada punto faltante como un error, aunque Vosk haya entendido perfectamente todas las palabras.

### Recomendación para la Investigación
Para que la comparativa en tu script `juez.py` sea científica y justa, debes elegir uno de estos dos caminos:
1.  **Normalización total (Recomendado):** Eliminar todos los signos de puntuación y pasar todo a minúsculas en AMBOS modelos antes de evaluar. Así mides la capacidad de "escucha" y no la de "escritura".
2.  **Post-procesamiento:** Usar herramientas como **Recasepunc** para añadirle puntuación a Vosk antes de compararlo con Whisper.

> **Regla de oro:** Nunca compares un modelo que puntúa contra uno que no lo hace sin normalizar los textos primero, o estarás favoreciendo injustamente a Whisper.

---

## 8. Proyección: Calidad de Texto para Chatbots (Adultos Mayores)

Al diseñar un chatbot que interactúa con adultos mayores, el paso intermedio (Voz a Texto) debe entregar un contenido con características específicas para que la IA (el cerebro) pueda responder con empatía y precisión.

### Los 5 Pilares de Calidad:

1.  **Coherencia Estructural:** El uso de puntuación básica es vital para el contexto. Una coma mal puesta puede cambiar el sentido de una frase de salud o una petición de ayuda.
2.  **Limpieza de Disfluencias:** Es fundamental eliminar muletillas (*"ehhh"*, *"este..."*) y tartamudeos comunes al pensar la idea, para que la IA no reciba "ruido" innecesario.
3.  **Normalización Semántica:** El texto debe ser gramaticalmente coherente. Los errores de homófonos (palabras que suenan igual pero se escriben distinto) pueden confundir el razonamiento de la IA.
4.  **Segmentación de Intenciones:** Dado que los adultos mayores pueden hacer pausas largas, el sistema debe ser capaz de agrupar frases relacionadas en un solo bloque de texto antes de enviarlo a la IA.
5.  **Marcadores Emocionales:** Preservar signos de interrogación o exclamación ayuda a la IA a detectar el tono (preocupación, alegría, urgencia), permitiendo una respuesta mucho más humana y cercana.

> **Conclusión:** No basta con transcribir palabras; hay que transcribir **ideas estructuradas**.

---

## 9. Pendientes: Optimización de Velocidad en Whisper

Para mejorar la respuesta del chatbot (especialmente para adultos mayores que esperan una interacción fluida), se plantean las siguientes mejoras de rendimiento:

*   [ ] **Migración a `faster-whisper`:** Reemplazar la librería oficial de OpenAI por la versión optimizada en C++. Esto podría reducir el tiempo de transcripción a la mitad o menos.
*   [ ] **Pruebas con modelo `tiny`:** Evaluar si la pérdida de precisión del modelo más pequeño es aceptable a cambio de la ganancia en velocidad (ideal para respuestas cortas).
*   [ ] **Implementar Cuantización (int8):** Configurar el modelo para que trabaje con menor precisión numérica (8-bit) para acelerar el procesamiento en CPU sin requerir una tarjeta de video (GPU).
*   [ ] **Segmentación Silenciosa (VAD):** Optimizar el detector de actividad de voz para que envíe el audio a Whisper apenas el usuario deje de hablar, eliminando esperas innecesarias al final de la frase.

> **Nota:** Se descarta el uso de CUDA por limitaciones de hardware actual, enfocando la optimización exclusivamente en **CPU**.

---

## 10. Pendientes: Mejoras Funcionales en Vosk

Dado que Vosk es el motor más rápido, se propone potenciarlo con módulos externos para suplir sus carencias de "entendimiento":

*   [ ] **Capa NLU de Intenciones (El "Puente"):** Implementar un clasificador ligero (usando `spaCy` o `Scikit-learn`) que analice el texto de Vosk para detectar si el usuario está pidiendo ayuda, saludando o haciendo una pregunta antes de enviar todo a la IA principal.
*   [ ] **Identificación de Locutor (¿Quién habla?):** Integrar el modelo de biometría de voz de Vosk (`vosk-model-spk`). 
    *   **Meta:** Que el sistema pueda decir "El que habla es Juan" solo analizando el timbre y frecuencia de la voz.
    *   **Paso a Paso de Implementación:**
        1.  **Registro (Enrolamiento):** Grabar una muestra de voz de los usuarios (ej: Juan y María) y generar su "huella digital" (un vector de 128 números).
        2.  **Extracción en Vivo:** Durante la charla, el motor extrae el vector de la voz actual en tiempo real.
        3.  **Comparación Matemática:** Calcular la **Distancia Coseno** entre el vector actual y los guardados. El que tenga la distancia más pequeña es el locutor identificado.
        4.  **Acción:** Enviar el nombre del usuario identificado junto con el texto a la IA para personalizar la respuesta.

    > **Nota Técnica sobre los 128 datos:** Vosk genera este vector numérico (embedding) automáticamente mediante su modelo de locutor. No se requieren librerías externas pesadas para la extracción; solo se utiliza una librería matemática básica (como `numpy`) para realizar la comparación de la distancia coseno en milisegundos.
*   [ ] **Post-procesamiento de Puntuación:** Evaluar la integración de **Recasepunc** para darle formato al texto de Vosk y que no llegue como una "sopa de palabras" a la IA.
*   [ ] **Diarización de Locutores (Múltiples Hablantes):** Implementar una lógica para detectar cambios de turno en la conversación. 
    *   **Objetivo:** Evitar que el sistema se pierda cuando dos personas hablan seguido. Se requiere ajustar la sensibilidad del silencio para cerrar frases rápidamente e identificar al nuevo locutor sin mezclar las huellas de voz.
