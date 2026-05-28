# 📝 Informe Técnico de Sesión: Evaluación STT y Diarización Híbrida

**Proyecto:** Mi-proyecto (STT & PLN)
**Investigador:** Esteban Mauricio
**Hardware:** i3, 8GB RAM.

---

## 1. 🔍 Hipótesis de Evaluación: El Problema de Jiwer

### La Hipótesis
Durante la sesión, se planteó la hipótesis de que las pruebas de precisión iniciales estaban arrojando resultados "falsos negativos". La teoría era que **Jiwer no estaba evaluando únicamente la capacidad de transcripción de palabras**, sino que estaba penalizando a los modelos por diferencias de formato (puntuación y mayúsculas) que no afectan la comprensión del mensaje.

### ¿Cómo juzga Jiwer? (Lógica WER)
Jiwer utiliza la métrica **WER (Word Error Rate)** basada en la distancia de edición de Levenshtein:
*   **Sustituciones (S):** Palabra cambiada (ej. "Hola," vs "Hola").
*   **Eliminaciones (D):** Palabra faltante.
*   **Inserciones (I):** Palabra extra agregada.

**El sesgo detectado:** Si la referencia dice `"hola,"` y el modelo entrega `"hola"`, Jiwer marca un error de sustitución. Esto hacía que Whisper (que puntúa muy bien) pareciera menos preciso que Vosk injustamente.

### Estandarización
Para validar la hipótesis, creamos una función de normalización:
1.  **Minusculización:** `texto.lower()`.
2.  **Limpieza de Puntuación:** Uso de `re.sub(r'[^\w\s]', '', texto)` para eliminar comas, puntos y signos.
3.  **Resultado:** Los resultados de precisión se volvieron reales, confirmando que la puntuación era el factor que alteraba las métricas.

---

## 2. 🧬 Análisis: VOSK_PRUEBA.py

### ¿Qué hace?
Es un sistema de **Biometría de Voz en Tiempo Real**. Identifica quién está hablando mientras ocurre la grabación y genera reportes visuales automáticos.

### ¿Por qué lo creamos?
Necesitábamos una forma de registrar "huellas vocales" únicas para cada usuario y validar si Vosk podía diferenciar locutores en vivo. Evolucionó de una prueba simple a una herramienta de auditoría con gráficos Mermaid.

### ¿Cómo funciona? (Análisis por Bloques)
1.  **Carga de Modelos:** Inicializa el modelo de lenguaje y el `SpkModel` (modelo de locutor).
2.  **Registro de Voz:** Captura audio, extrae un vector de 128 dimensiones y lo guarda en un `.json`.
3.  **Comparación Biométrica:** Utiliza la **Distancia Coseno** para comparar el audio actual con los JSON guardados.
4.  **Generador de Reportes:** Al finalizar con `Ctrl+C`, procesa el historial y crea un diagrama `sequenceDiagram` de Mermaid.

### Código Fuente:
```python
# (Extracto del bucle principal de identificación)
while True:
    data = stream.read(4000)
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        if res.get("text"):
            if "spk" in res:
                vector_actual = np.array(res["spk"])
                # Lógica de comparación contra voces_guardadas/
                # ... (ver archivo completo en Codigos/VOSK_PRUEBA.py)
```

---

## 🚀 3. Análisis: WHISPER_PRUEBA.py

### ¿Qué hace?
Es un sistema de **Diarización Híbrida Biométrica**. Toma una conversación fluida (donde la gente se interrumpe) y la separa frase por frase asignando el nombre de quien habló.

### ¿Por qué lo creamos?
Vosk tiene una limitación: si dos personas hablan sin hacer pausas, sus voces se "mezclan" en un solo vector y el sistema arroja "Desconocido". Creamos este script para usar la **precisión temporal de Whisper** y la **identificación de Vosk**, logrando separar voces incluso en charlas rápidas.

### ¿Cómo funciona? (Análisis por Bloques)
1.  **Grabación Offline:** Graba toda la charla de una vez para no estresar el i3.
2.  **Segmentación (Whisper):** Whisper detecta los tiempos exactos (segundos) de cada frase.
3.  **Recorte Quirúrgico (Librosa):** Se "recorta" el audio de cada segmento detectado por Whisper.
4.  **Identificación Cruzada:** Ese recorte se pasa por el modelo de Vosk para saber a quién pertenece esa huella específica.
5.  **Reporte de Diarización:** Genera un diagrama Mermaid con marcas de tiempo (ej. `[1.2s] Esteban -> Sistema: Hola`).

### Código Fuente:
```python
# (Lógica de Diarización Híbrida)
audio_array, _ = librosa.load(ruta_audio, sr=16000)
resultado = whisper_model.transcribe(audio_array, fp16=False)
for seg in resultado["segments"]:
    # Recorte y paso por SpkModel de Vosk para identificación por nombre
    vector_segmento = obtener_vector_vosk(ruta_audio, seg['start'], seg['end'], ...)
```

---

## 📁 Documentación de Respaldo
Para entender la matemática y arquitectura detrás de estos códigos, consultar:
*   `explicacion/vosk_diarizacion.md`
*   `explicacion/whisper_prueba.md`

---
*Informe consolidado para el Semillero de Investigación.*
