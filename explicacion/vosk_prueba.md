# Documentación: Sistema de Biometría de Voz con Vosk

Este documento detalla el funcionamiento y la implementación del script `VOSK_PRUEBA.py`, diseñado para el registro e identificación de personas mediante la voz en tiempo real.

## 1. Concepto del Sistema
El sistema implementa una arquitectura de **Biometría de Voz** basada en modelos de aprendizaje profundo (Deep Learning). A diferencia de los sistemas de STT (Speech-to-Text) convencionales, que buscan patrones fonéticos para convertirlos en texto, este módulo se enfoca en la extracción de **características paralingüísticas** del locutor.

## 2. Fundamentos Académicos y Técnicos

### A. Arquitectura de X-vectors (Speaker Embeddings)
Vosk utiliza una técnica conocida como **X-vectors**. Se trata de una red neuronal profunda (DNN) entrenada específicamente para mapear segmentos de audio de duración variable en un espacio vectorial de dimensión fija. 
*   **Proceso:** La red neuronal analiza los coeficientes cepstrales en las frecuencias de Mel (MFCC), los formantes y la cadencia, condensando toda esa información en un punto dentro de un espacio multidimensional.

### B. ¿Por qué 128 dimensiones?
La elección de un vector de **128 dimensiones** responde a un compromiso de optimización entre precisión y costo computacional:
*   **Capacidad de Representación:** 128 dimensiones son suficientes para capturar las variaciones únicas de las cavidades resonantes (boca, nariz, garganta) de un ser humano, permitiendo diferenciar entre miles de voces distintas.
*   **Eficiencia (Real-Time):** Al ser un vector de tamaño pequeño para los estándares de IA, permite realizar miles de comparaciones por segundo utilizando operaciones de álgebra lineal básica en la CPU, lo cual es vital para un chatbot que debe responder en tiempo real.

### C. Métrica de Similitud: Distancia Coseno
En biometría de voz, no se utiliza la distancia euclidiana (la distancia física entre puntos) porque factores como el volumen de la grabación podrían alterar la magnitud del vector. En su lugar, se utiliza la **Distancia Coseno**:
*   **Lógica:** Esta métrica mide el **ángulo** entre los dos vectores en el espacio de 128D. 
*   **Ventaja:** Identifica la "orientación" de la identidad vocal. Si el ángulo es pequeño (cercano a 0 grados), el coseno es cercano a 1, lo que indica que la "huella" de la voz es la misma, independientemente de la intensidad o el ruido ambiental.
*   **Numpy:** Librería de Python especializada en **Álgebra Lineal** y cálculo matricial, necesaria para procesar los vectores de voz.

---

## 3. Flujo de Trabajo Detallado

### A. Registro (Enrolamiento)
El **Enrolamiento** es el proceso de "dar de alta" una identidad biométrica en el sistema.
1.  **Captura de Audio:** El usuario lee un texto estructurado.
2.  **Generación de Huella:** El sistema genera múltiples vectores durante la grabación.
3.  **Estabilización:** Se calcula el **promedio de los vectores** capturados. Esto elimina ruidos aleatorios y crea una "huella promedio" más fiable.
4.  **Almacenamiento:** La huella se guarda en un archivo `.json`.

### B. Identificación en Tiempo Real (Inferencia)
La **Inferencia** es cuando el modelo ya entrenado toma datos nuevos y toma una decisión.
1.  **Streaming:** Flujo de audio constante por fragmentos (chunks).
2.  **Extracción Dinámica:** Vosk genera el vector de la voz actual cada vez que detecta que se terminó una frase.
3.  **Comparación:** Se busca la menor distancia coseno contra la base de datos local.
4.  **Umbral de Confianza:** Valor límite (0.65) que decide si el sistema "se arriesga" a dar un nombre o prefiere decir "Desconocido".

---

## 4. Glosario de Términos (Para Revisión Académica)

*   **Características Paralingüísticas:** Elementos de la comunicación que no tienen que ver con el significado de las palabras, sino con *cómo* se dicen (tono, ritmo, timbre).
*   **MFCC (Mel Frequency Cepstral Coefficients):** Son representaciones del espectro de audio que imitan la forma en que el oído humano percibe el sonido. Es la "materia prima" que analiza la IA.
*   **Formantes:** Son los picos de intensidad en el espectro de una voz. Están determinados por la forma física de la boca y garganta del locutor.
*   **Embedding:** Es la representación de un objeto complejo (como una voz humana) en una lista de números. Permite que las máquinas "midan" conceptos abstractos.
*   **Espacio Vectorial:** Es un "mapa" imaginario donde cada voz es un punto. Las voces parecidas están cerca unas de otras en este mapa.
*   **X-vector:** Un tipo específico de embedding profundo que ha demostrado ser muy superior a los métodos antiguos (como los i-vectors) para identificar personas.

---

## 5. Requisitos de Instalación
Es indispensable contar con el modelo de locutor oficial de Vosk:
*   **Modelo:** `vosk-model-spk-0.4`
*   **Descarga:** [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models/)
*   **Ubicación:** Debe colocarse en `Codigos/model-spk/vosk-model-spk-0.4/`.

---

## 6. ¿Qué es el modelo que descargamos?

El modelo específico utilizado es el **`vosk-model-spk-0.4`**. Es fundamental entender que este no es un modelo de lenguaje convencional, sino un **Modelo de Locutor (Speaker Model)**.

### A. Diferencia entre STT y Reconocimiento de Locutor
*   **Modelo de Lenguaje (STT):** Entrena a la IA para entender *qué* palabras se están diciendo (ej. convertir sonido en texto).
*   **Modelo de Locutor (Biometría):** Entrena a la IA para identificar *quién* está hablando. Se enfoca en las texturas físicas del sonido.

### B. ¿Cómo funciona la "Huella Vocal"?
El modelo actúa como un extractor de características. Cuando recibe audio, no busca fonemas, sino que analiza la anatomía del tracto vocal del hablante. Convierte el audio en una lista de **128 números flotantes** (un vector de identidad).

*   **Entrada:** Onda de audio (WAV 16kHz).
*   **Proceso:** Análisis de MFCC y paso por la arquitectura de X-vectors.
*   **Salida:** Un "Speaker Embedding" (un punto matemático único en un espacio de 128 dimensiones).

---

## 7. Módulo de Visualización Biométrica

Para facilitar la interpretación de los datos y la validación del sistema, se desarrolló el script `visualizar_voces.py`. Este módulo transforma los datos abstractos del JSON en representaciones gráficas comprensibles.

### A. ¿Cómo leer las gráficas?

Al visualizar un perfil de voz (como `esteban.json`), el sistema genera dos representaciones:

1.  **Distribución de Rasgos (Barras):**
    *   Cada una de las 128 barras representa un "rasgo" específico extraído por la red neuronal.
    *   **Picos positivos/negativos:** Indican la presencia o ausencia marcada de ciertas características fonéticas (brillo de la voz, profundidad, nasalidad, etc.).
    *   **Interpretación:** Si dos personas tienen picos en los mismos índices, sus voces son muy similares.

2.  **Firma Vocal (Línea):**
    *   Es el "contorno" de tu identidad. Representa la topografía de tu voz en el espacio vectorial.
    *   **Para el profesor:** Esta firma es el resultado de procesar los **Formantes** a través de la arquitectura de **X-vectors**. Es prácticamente imposible que dos personas tengan la misma silueta exacta.

### B. Uso del Visualizador
El script permite seleccionar dinámicamente cualquier perfil guardado en la carpeta `voces_guardadas/`, lo que permite realizar comparaciones rápidas entre el adulto mayor, el cuidador y otros familiares.

---

## 8. Conclusiones y Aplicación Académica

El uso de este modelo permite que el sistema trascienda la simple transcripción. Al integrar la biometría, el proyecto alcanza un nivel de **personalización avanzada**, vital para el cuidado de adultos mayores.

1.  **Seguridad:** Identificación de personas no autorizadas en el hogar.
2.  **Contexto:** El sistema sabe si quien pide ayuda es el paciente o el cuidador.
3.  **Análisis de Datos:** Permite generar métricas sobre la frecuencia de interacción de cada participante en la sesión.

---
> **Proyección para Adultos Mayores:** Esta funcionalidad permite que el chatbot identifique automáticamente quién le habla, permitiendo respuestas personalizadas como: *"Hola abuela, ¿te gustaría escuchar tu música favorita?"*.
