# Reporte de Actualización: VOSK_PRUEBA.py y el Problema de Diarización

## 1. ¿Qué mejoras implementamos en Vosk?
En nuestra sesión, actualizamos el script `VOSK_PRUEBA.py` para añadirle "memoria" y capacidad de reportes automáticos, mejorando la visualización de los datos. 
* **Historial en memoria:** Añadimos una lista que guarda internamente toda la conversación, los textos y los porcentajes de confianza mientras el modo chatbot está activo.
* **Reporte Automático (Mermaid):** Al presionar `Ctrl+C` para detener la grabación, el sistema procesa el historial acumulado y genera automáticamente un archivo `.md` en la carpeta `Reportes/`.
* **Gráficos Visuales:** Este reporte incluye un diagrama de secuencia (Mermaid) mostrando quién le habló al sistema, y una tabla de transcripción con el porcentaje de certeza de identidad de la huella vocal.

## 2. El Problema Encontrado: Habla Fluida sin Pausas
Al probar el código en un entorno real de debate o charla fluida, descubrimos una limitación técnica conocida en el Procesamiento de Lenguaje Natural (PLN) como la dificultad de **Diarización de Locutores Continuos en Tiempo Real**.

**¿Qué ocurría?**
Si la "Persona 1" y la "Persona 2" hablaban en una conversación muy fluida, interrumpiéndose o sin dejar espacios de silencio (pausas) entre ellos, el sistema fallaba en la identificación biométrica y marcaba al locutor como `DESCONOCIDO` (con una similitud drásticamente menor al 65%).

**Causa Técnica (Limitación Interna de Vosk)**
El modelo `SpkModel` de Vosk funciona procesando bloques de audio completos delimitados estrictamente por silencios (cuando la función interna `AcceptWaveform()` devuelve `True`). 
1. Si no hay un silencio evidente, Vosk sigue acumulando el audio de ambas personas en un solo bloque continuo.
2. Al detectar finalmente la pausa, extrae las características acústicas y forma un único X-vector de 128 dimensiones.
3. **El problema matemático:** Si dos personas hablaron en ese mismo bloque, el vector resultante es un promedio matemático de las dos voces.
4. Al comparar este vector "mezclado" contra las huellas guardadas en memoria, la distancia coseno no coincide ni con la Persona 1 ni con la Persona 2, lo que causa que falle el reconocimiento.

Debido a que Vosk genera su vector a nivel de frase y no a nivel de milisegundo o palabra, concluimos que **Vosk no es apto para diarización de múltiples locutores en tiempo real sin espacios de silencio marcados**.
