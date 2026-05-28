import os
import json
import time
import wave
import numpy as np
import pyaudio
import keyboard
import whisper
import librosa
import datetime
import warnings

from vosk import Model, KaldiRecognizer, SpkModel

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_WAV = os.path.join(BASE_DIR, "audios", "temp_conversacion.wav")
REPORTES_DIR = os.path.join(BASE_DIR, "Reportes")
VOCES_FOLDER = os.path.join(BASE_DIR, "voces_guardadas")

MODEL_VOSK_PATH = os.path.join(BASE_DIR, "model")
SPK_MODEL_PATH = os.path.join(BASE_DIR, "model-spk", "vosk-model-spk-0.4")

if not os.path.exists(os.path.dirname(TEMP_WAV)):
    os.makedirs(os.path.dirname(TEMP_WAV))
if not os.path.exists(REPORTES_DIR):
    os.makedirs(REPORTES_DIR)

def calcular_distancia_coseno(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def cargar_voces_conocidas():
    voces = {}
    if not os.path.exists(VOCES_FOLDER):
        return voces
        
    for archivo in os.listdir(VOCES_FOLDER):
        if archivo.endswith(".json"):
            try:
                with open(os.path.join(VOCES_FOLDER, archivo), "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    voces[datos["nombre"]] = np.array(datos["vector"])
            except Exception as e:
                pass
    return voces

def grabar_audio(ruta_destino):
    p = pyaudio.PyAudio()
    rate = 16000
    chunk = 1024
    
    print("\n" + "="*50)
    print(" 🎙️ GRABACIÓN DE CONVERSACIÓN (Múltiples Voces)")
    print("="*50)
    print("Presiona ESPACIO para comenzar a grabar...")
    keyboard.wait('space')
    
    print("\n🔴 Grabando... (Hablen libremente, pueden interrumpirse)")
    print(">>> Presiona ESPACIO nuevamente para detener la grabación.")
    time.sleep(0.5)

    frames = []
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=chunk)
        
        while True:
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            
            if keyboard.is_pressed('space'):
                print("\n⏹️ Grabación finalizada.")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(ruta_destino, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)) 
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return True
    except Exception as e:
        print(f"\n[ERROR] Fallo con el micrófono: {e}")
        return False

def obtener_vector_vosk(ruta_audio, inicio, fin, modelo_vosk, spk_model):
    """Extrae el segmento exacto de audio y se lo pasa a Vosk para obtener su huella vocal."""
    try:
        y, sr = librosa.load(ruta_audio, sr=16000, offset=inicio, duration=(fin - inicio))
        if len(y) == 0:
            return None
            
        # Convertir float32 [-1.0, 1.0] a int16 para Vosk
        y_int16 = (y * 32767).astype(np.int16)
        audio_bytes = y_int16.tobytes()
        
        rec = KaldiRecognizer(modelo_vosk, 16000)
        rec.SetSpkModel(spk_model)
        rec.AcceptWaveform(audio_bytes)
        res = json.loads(rec.FinalResult())
        
        if "spk" in res:
            return np.array(res["spk"])
        return None
    except Exception:
        return None

def procesar_diarizacion_biometrica(ruta_audio):
    voces_conocidas = cargar_voces_conocidas()
    if not voces_conocidas:
        print("\n[!] No hay voces guardadas. Primero debes registrar una voz en VOSK_PRUEBA.py")
        return []

    print("\n" + "-"*50)
    print("🤖 PASO 1: Transcribiendo y segmentando con Whisper...")
    print("-" * 50)
    
    inicio_t = time.time()
    whisper_model = whisper.load_model("base")
    audio_array, _ = librosa.load(ruta_audio, sr=16000)
    resultado = whisper_model.transcribe(audio_array, fp16=False, language="es")
    segmentos = resultado["segments"]
    
    print(f"✅ Transcripción lista en {time.time() - inicio_t:.1f} segundos.")
    print("\n🧠 PASO 2: Comparando cada frase con las voces guardadas (Vosk)...")
    
    if not os.path.exists(MODEL_VOSK_PATH) or not os.path.exists(SPK_MODEL_PATH):
        print("\n[ERROR] Faltan los modelos de Vosk.")
        return []

    vosk_model = Model(MODEL_VOSK_PATH)
    spk_model = SpkModel(SPK_MODEL_PATH)
    
    historial = []
    
    for seg in segmentos:
        inicio = seg['start']
        fin = seg['end']
        texto = seg['text'].strip()
        
        if len(texto) < 2: 
            continue
            
        vector_segmento = obtener_vector_vosk(ruta_audio, inicio, fin, vosk_model, spk_model)
        
        quien_habla = "Desconocido"
        max_similitud = 0.0
        
        if vector_segmento is not None:
            for nombre, vector_guardado in voces_conocidas.items():
                similitud = calcular_distancia_coseno(vector_segmento, vector_guardado)
                if similitud > max_similitud:
                    max_similitud = similitud
                    quien_habla = nombre
            
            # Umbral de confianza
            if max_similitud < 0.65:
                quien_habla = "Desconocido"
        
        historial.append({
            "persona": quien_habla.upper(),
            "texto": texto,
            "inicio": inicio,
            "fin": fin,
            "confianza": max_similitud
        })
        
    return historial

def generar_reporte_mermaid(historial):
    if not historial:
        return
        
    fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_archivo = os.path.join(REPORTES_DIR, f"Whisper_Biometria_{fecha_str}.md")
    
    participantes = sorted(list(set([item["persona"] for item in historial])))
    
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write("# 🎙️ Reporte: Whisper + Vosk Biometría\n\n")
        f.write(f"**Fecha:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("## 💬 Flujo de la Conversación\n\n")
        f.write("```mermaid\n")
        f.write("sequenceDiagram\n")
        f.write("    participant SYS as Conversación\n")
        for p in participantes:
            p_id = p.replace(" ", "_")
            f.write(f'    actor {p_id} as {p}\n')
        
        f.write("\n")
        for item in historial:
            persona_id = item["persona"].replace(" ", "_")
            texto_limpio = item["texto"].replace("\\n", " ").replace(";", ",").replace('"', "'")
            if len(texto_limpio) > 50:
                texto_limpio = texto_limpio[:47] + "..."
            f.write(f'    {persona_id}->>SYS: [{item["inicio"]:.1f}s] {texto_limpio}\n')
        f.write("```\n\n")
        
        f.write("## 📝 Transcripción Detallada\n\n")
        f.write("| Tiempo | Hablante | Confianza | Texto |\n")
        f.write("| :---: | :--- | :---: | :--- |\n")
        for item in historial:
            conf_str = f'{item["confianza"]:.2%}' if item["confianza"] > 0 else "N/A"
            f.write(f'| {item["inicio"]:.1f}s - {item["fin"]:.1f}s | **{item["persona"]}** | {conf_str} | {item["texto"]} |\n')
            
    print(f"\n✅ ¡Reporte generado en:\n -> {ruta_archivo}")

def main():
    if grabar_audio(TEMP_WAV):
        historial = procesar_diarizacion_biometrica(TEMP_WAV)
        
        if historial:
            print("\n--- RESUMEN RÁPIDO ---")
            for h in historial:
                print(f"[{h['inicio']:.1f}s] {h['persona']} ({h['confianza']:.0%}): {h['texto']}")
                
            generar_reporte_mermaid(historial)
            
        if os.path.exists(TEMP_WAV):
            os.remove(TEMP_WAV)

if __name__ == "__main__":
    main()
