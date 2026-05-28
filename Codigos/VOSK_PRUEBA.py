import os
import json
import sys
import numpy as np
import pyaudio
import datetime
from vosk import Model, KaldiRecognizer, SpkModel

def generar_reporte_conversacion(historial):
    if not historial:
        print("No hubo conversación para guardar.")
        return
    
    # Usar la carpeta Reportes actual
    reportes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Reportes")
    if not os.path.exists(reportes_dir):
        os.makedirs(reportes_dir)
        
    fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_archivo = os.path.join(reportes_dir, f"Conversacion_Vosk_{fecha_str}.md")
    
    participantes = list(set([item["persona"] for item in historial]))
    
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write("# 🎙️ Reporte de Conversación y Biometría de Voz\n\n")
        f.write(f"**Fecha:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("## 💬 Flujo de la Conversación (Gráfica Mermaid)\n\n")
        f.write("```mermaid\n")
        f.write("sequenceDiagram\n")
        f.write("    participant SYS as Micrófono/Sistema\n")
        for p in participantes:
            p_id = p.replace(" ", "_")
            f.write(f'    actor {p_id} as {p}\n')
        
        f.write("\n")
        for item in historial:
            persona_id = item["persona"].replace(" ", "_")
            texto_limpio = item["texto"].replace("\n", " ").replace(";", ",").replace('"', "'")
            if len(texto_limpio) > 55:
                texto_limpio = texto_limpio[:52] + "..."
            f.write(f'    {persona_id}->>SYS: {texto_limpio}\n')
        f.write("```\n\n")
        
        f.write("## 📝 Transcripción Completa\n\n")
        f.write("| Hablante | Confianza de Identidad | Texto |\n")
        f.write("| :--- | :---: | :--- |\n")
        for item in historial:
            conf_str = f'{item["confianza"]:.2%}' if item["confianza"] > 0 else "N/A"
            f.write(f'| **{item["persona"]}** | {conf_str} | {item["texto"]} |\n')
            
    print(f"\n✅ ¡Reporte visual (Mermaid) generado con éxito en:\n -> {ruta_archivo}")

# --- CONFIGURACIÓN ---
# Usamos rutas absolutas para evitar errores de Vosk en Windows
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model")
SPK_MODEL_PATH = os.path.join(BASE_DIR, "model-spk", "vosk-model-spk-0.4")
VOCES_FOLDER = os.path.join(BASE_DIR, "voces_guardadas")

# Crear carpeta de voces si no existe
if not os.path.exists(VOCES_FOLDER):
    os.makedirs(VOCES_FOLDER)

# Texto estructurado para capturar un buen espectro de la voz
TEXTO_REGISTRO = """
El sistema de reconocimiento de voz está analizando mi timbre y frecuencia. 
Las nubes grises flotan sobre el campo verde mientras yo hablo con claridad. 
Uno, dos, tres, cuatro, cinco. Mi voz es mi identidad única.
"""

def calcular_distancia_coseno(v1, v2):
    """Calcula la similitud entre dos vectores (1.0 es idéntico)"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def cargar_voces_conocidas():
    """Carga los vectores guardados en la carpeta voces_guardadas"""
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
                print(f"Error cargando {archivo}: {e}")
    return voces

import keyboard

def registrar_voz(model, spk_model):
    print("\n" + "="*50)
    print("      PASO 1: REGISTRO DE NUEVA VOZ")
    print("="*50)
    nombre = input("¿A quién vamos a registrar? (Nombre): ").strip()
    if not nombre:
        print("Nombre inválido.")
        return
    
    print("\nPara registrarte, por favor lee el siguiente texto con voz clara:")
    print("-" * 60)
    print(TEXTO_REGISTRO.strip())
    print("-" * 60)
    print("\n>>> Presiona ENTER para empezar a grabar...")
    input()

    rec = KaldiRecognizer(model, 16000)
    rec.SetSpkModel(spk_model)
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()

    print("\n>>> GRABANDO... Lee el texto con calma.")
    print(">>> (Presiona la tecla ESPACIO para detener la grabación cuando termines)")
    
    vectores_capturados = []
    
    while True:
        data = stream.read(4000)
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            if "spk" in res:
                vectores_capturados.append(res["spk"])
        
        # Si se presiona espacio, detenemos
        if keyboard.is_pressed('space'):
            print("\n>>> Grabación finalizada por el usuario.")
            break
    
    stream.stop_stream()
    stream.close()
    p.terminate()

    if vectores_capturados:
        # Promediamos los vectores obtenidos para mayor estabilidad
        vector_final = np.mean(vectores_capturados, axis=0)
        
        ruta_archivo = os.path.join(VOCES_FOLDER, f"{nombre.lower()}.json")
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump({"nombre": nombre, "vector": vector_final.tolist()}, f)
        print(f"\n✅ ¡Perfecto! La huella de voz de '{nombre}' ha sido guardada.")
    else:
        print("\n❌ No se detectó suficiente voz. Intenta hablar más fuerte o más cerca del micro.")

def reconocer_en_vivo(model, spk_model):
    voces_conocidas = cargar_voces_conocidas()
    if not voces_conocidas:
        print("\n[!] No hay voces en la base de datos. Registra a alguien primero.")
        return

    rec = KaldiRecognizer(model, 16000)
    rec.SetSpkModel(spk_model)
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    print("\n" + "="*50)
    print("      PASO 2: MODO CHATBOT (IDENTIFICACIÓN EN VIVO)")
    print("="*50)
    print("Habla libremente. Presiona Ctrl+C para detener y generar el reporte.")

    historial_conversacion = []

    try:
        while True:
            data = stream.read(4000)
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                texto = res.get("text", "")
                
                if texto:
                    quien_habla = "Desconocido"
                    max_similitud = 0
                    
                    if "spk" in res:
                        vector_actual = np.array(res["spk"])
                        
                        # Comparación de biometría
                        for nombre, vector_guardado in voces_conocidas.items():
                            similitud = calcular_distancia_coseno(vector_actual, vector_guardado)
                            if similitud > max_similitud:
                                max_similitud = similitud
                                quien_habla = nombre
                        
                        # Umbral de seguridad (0.6 - 0.8 suele ser lo ideal)
                        if max_similitud < 0.65:
                            quien_habla = "Persona no identificada"

                    print(f"\n>>> {quien_habla.upper()} dice: \"{texto}\"")
                    print(f"    (Confianza de identidad: {max_similitud:.2%})")
                    
                    # Guardamos para el reporte final
                    historial_conversacion.append({
                        "persona": quien_habla.upper(),
                        "texto": texto,
                        "confianza": max_similitud
                    })

    except KeyboardInterrupt:
        print("\n\nCerrando el modo de escucha y generando reporte...")
        generar_reporte_conversacion(historial_conversacion)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    # Verificación de modelos
    if not os.path.exists(MODEL_PATH):
        print(f"Error: No se encuentra el modelo de lenguaje en '{MODEL_PATH}'")
        return
    if not os.path.exists(SPK_MODEL_PATH):
        print(f"Error: No se encuentra el modelo de locutor en '{SPK_MODEL_PATH}'")
        print("Descárgalo de alphacephei.com/vosk/models (vosk-model-spk-0.4)")
        return

    print("Cargando motores de IA...")
    model = Model(MODEL_PATH)
    spk_model = SpkModel(SPK_MODEL_PATH)

    while True:
        print("\n" + "—"*40)
        print("   MENÚ BIOMETRÍA DE VOZ (VOSK)")
        print("—"*40)
        print("1. Registrar una nueva persona")
        print("2. Iniciar escucha y detección de personas")
        print("0. Salir")
        
        opc = input("\nSelecciona una opción: ")
        
        if opc == "1":
            registrar_voz(model, spk_model)
        elif opc == "2":
            reconocer_en_vivo(model, spk_model)
        elif opc == "0":
            print("¡Adiós!")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()
