import os
from datetime import datetime

class GeneradorReporte:
    @staticmethod
    def crear_reporte(referencia, texto_vosk, texto_whisper, error_vosk, error_whisper, ganador, nombre_reporte="", ruta_img="", tiempo_v=0, tiempo_w=0):
        """
        Crea un archivo Markdown (.md) enviando tiempos y métricas de error.
        """
        carpeta = "Reportes"
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if nombre_reporte.strip():
            nombre_limpio = nombre_reporte.strip()
            if not nombre_limpio.endswith('.md'):
                nombre_limpio += '.md'
            ruta_reporte = os.path.join(carpeta, nombre_limpio)
        else:
            ruta_reporte = os.path.join(carpeta, f"Reporte_STT_{timestamp}.md")
        
        # Redondeamos porcentajes
        ev_porc = round(error_vosk * 100, 2)
        ew_porc = round(error_whisper * 100, 2)
        
        # Gráfica de barras usando código Mermaid (Soportado por GitHub y VSCode)
        # Algunos visores rompen el bloque si tiene decimales, así que usamos enteros para graficar
        ev_int = int(round(error_vosk * 100))
        ew_int = int(round(error_whisper * 100))
        
        grafica_mermaid = f"""```mermaid
%%{{init: {{ 'theme': 'base', 'themeVariables': {{ 'xyChart': {{ 'plotColorPalette': '#FFb000' }} }} }} }}%%
xychart-beta
    title "Margen de Error (WER) - ¡Menor es Mejor!"
    x-axis ["Vosk", "Whisper"]
    y-axis "Error %" 0 --> 100
    bar [{ev_int}, {ew_int}]
```"""

        # Tabla comparativa mejorada con tiempo
        tabla_markdown = f"""| Modelo | Tiempo | Referencia | Transcripción Obtenida | Error (WER %) |
| :---: | :---: | --- | --- | :---: |
| **Vosk** | {tiempo_v:.2f}s | {referencia} | {texto_vosk} | **{ev_porc}%** |
| **Whisper** | {tiempo_w:.2f}s | {referencia} | {texto_whisper} | **{ew_porc}%** |"""

        import urllib.parse
        img_name = os.path.basename(ruta_img) if ruta_img else ""
        img_encoded = urllib.parse.quote(img_name) if img_name else ""
        bloque_img = f"## 🖼️ Análisis Visual (Frecuencias y Forma de Onda)\n![Análisis Visual]({img_encoded})\n\n---" if ruta_img else ""

        # Ensamble del documento completo
        contenido_md = f"""# Evaluación de Modelos Speech-to-Text (STT) 🤖🎙️
**Fecha de evaluación:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
**Modelo Ganador (Menor margen de error):** 🏆 **{ganador}**

---

{bloque_img}

## 📊 Gráfica de Desempeño
La métrica utilizada se conoce como **Word Error Rate (WER)**. Representa el nivel de equivocación. Entre menor sea la barra, mejor fue el modelo transcribiendo el audio.

{grafica_mermaid}

---

## 📝 Resultados Detallados
Comparativa de precisión entre lo que la persona dijo realmente y lo que el modelo "escuchó".

{tabla_markdown}

---
*Reporte generado automáticamente por Juez.*
"""

        with open(ruta_reporte, "w", encoding="utf-8") as f:
            f.write(contenido_md)
            
        print(f"[OK] Reporte Markdown generado en: {ruta_reporte}")
        return ruta_reporte

    @staticmethod
    def crear_reporte_completo_vs(ruta_audio1, ruta_audio2, ref, txt_v1, txt_w1, err_v1, err_w1, txt_v2, txt_w2, err_v2, err_w2, ruta_img_vs, nombre_rep="", t_vad=0, t_stt1_v=0, t_stt1_w=0, t_stt2_v=0, t_stt2_w=0):
        """
        Crea un reporte MD exhaustivo con tiempos de procesamiento y transcripción.
        """
        carpeta = "Reportes"
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ruta_reporte = os.path.join(carpeta, f"{nombre_rep or 'Reporte_VS'}_{timestamp}.md")
        
        a1_name = os.path.basename(ruta_audio1)
        a2_name = os.path.basename(ruta_audio2)
        
        import urllib.parse
        img_name = os.path.basename(ruta_img_vs) if ruta_img_vs else ""
        img_encoded = urllib.parse.quote(img_name) if img_name else ""
        
        contenido_md = f"""# 🏆 Reporte DEFINITIVO: Evaluación STT y Visualización VS 🏆
**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## ⏱️ Análisis de Tiempos (Rendimiento)
| Fase | Detalle | Tiempo (s) |
| :--- | :--- | :---: |
| **Limpieza / VAD** | {a2_name} | **{t_vad:.2f}s** |
| **STT Audio 1** | Vosk | {t_stt1_v:.2f}s |
| **STT Audio 1** | Whisper | {t_stt1_w:.2f}s |
| **STT Audio 2** | Vosk | {t_stt2_v:.2f}s |
| **STT Audio 2** | Whisper | {t_stt2_w:.2f}s |

---

## 🖼️ Análisis Visual: {a1_name} vs {a2_name}
![Comparativa Visual_Audios]({img_encoded})

---

## 🗣️ Análisis de Transcripción (WER)
**Referencia:** "{ref}"

### 🔹 Audio 1: `{a1_name}`
| Modelo | Texto | Error (WER %) | Tiempo |
| :---: | --- | :---: | :---: |
| **Vosk** | {txt_v1} | **{err_v1*100:.2f}%** | {t_stt1_v:.2f}s |
| **Whisper**| {txt_w1} | **{err_w1*100:.2f}%** | {t_stt1_w:.2f}s |

### 🔹 Audio 2: `{a2_name}`
| Modelo | Texto | Error (WER %) | Tiempo |
| :---: | --- | :---: | :---: |
| **Vosk** | {txt_v2} | **{err_v2*100:.2f}%** | {t_stt2_v:.2f}s |
| **Whisper**| {txt_w2} | **{err_w2*100:.2f}%** | {t_stt2_w:.2f}s |

---
*Reporte integral generado automáticamente por Juez.*
"""
        with open(ruta_reporte, "w", encoding="utf-8") as f:
            f.write(contenido_md)
        print(f"\n[OK] Reporte VS generado: {ruta_reporte}")
        return ruta_reporte
