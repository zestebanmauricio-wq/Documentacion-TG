import whisper
import os
import warnings
import librosa
import soundfile as sf
import numpy as np
import pyaudio
import keyboard
import time
import json

# Ignorar advertencias de FP16 en CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# --- CONFIGURACIN ---
AUDIOS_FOLDER = "audios"

# Crear carpeta de audios si no existe
if not os.path.exists(AUDIOS_FOLDER):
    os.makedirs(AUDIOS_FOLDER)

print("\n[Whisper] Cargando modelo 'base' en CPU (esto puede tardar unos segundos)...")
# Cargamos el modelo 'base' que es mucho más preciso que el 'tiny'
model = whisper.load_model("base", device="cpu")

def transcribir_microfono_whisper():
    """Opcin 1: Graba audio del micrfono y luego lo transcribe con Whisper"""
    p = pyaudio.PyAudio()
    rate = 16000
    chunk = 1024
    
    print("\n" + "="*50)
    print(" MODO MICRFONO - WHISPER")
    print("="*50)
    print("Presiona ESPACIO para comenzar a grabar...")
    keyboard.wait('space')
    
    print("\nGrabando... (Presiona ESPACIO para detener)...")
    time.sleep(0.5)

    frames = []
    
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate,
                        input=True, frames_per_buffer=chunk)
        
        while True:
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
            
            if keyboard.is_pressed('space'):
                print("\n\nGrabacin finalizada.")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Convertir bytes a array de numpy (float32) para Whisper
        print("[Whisper] Procesando y transcribiendo...")
        audio_bytes = b''.join(frames)
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Transcripcin
        result = model.transcribe(audio_np, language="es", fp16=False)
        mostrar_final(result["text"])

    except Exception as e:
        print(f"\n[ERROR] Fallo con el micrfono: {e}")

def transcribir_archivo_whisper(ruta_audio):
    """Opcin 2: Transcribe un archivo de la carpeta audios"""
    if not os.path.exists(ruta_audio):
        print(f"\n[ERROR] No se encuentra el archivo: {ruta_audio}")
        return
    
    try:
        print(f"\n[Info] Cargando archivo: {os.path.basename(ruta_audio)}")
        # Whisper requiere 16000Hz. Cargamos con librosa para evitar fallos de FFmpeg.
        audio_array, sr = librosa.load(ruta_audio, sr=16000)
        
        print(f"[Whisper] Procesando...")
        result = model.transcribe(audio_array, language="es", fp16=False)
        mostrar_final(result["text"])
        
    except Exception as e:
        print(f"\n[ERROR] Fallo al procesar el archivo: {e}")

def menu_archivos():
    print("\n¿De qué carpeta quieres el audio?")
    print("1. 'audios' (Normales)")
    print("2. 'audios procesados' (Limpios y optimizados)")
    folder_opc = input("Elige una opción (1-2): ")
    
    target_folder = AUDIOS_FOLDER if folder_opc == "1" else "audios procesados"
    
    if not os.path.exists(target_folder):
        print(f"\nLa carpeta '{target_folder}' no existe.")
        return

    archivos = [f for f in os.listdir(target_folder) if f.endswith((".wav", ".mp3", ".m4a", ".flac"))]
    
    if not archivos:
        print(f"\nNo hay audios en '{target_folder}'. Pon algunos archivos ahí primero.")
        return

    print(f"\nArchivos en '{target_folder}':")
    for i, archivo in enumerate(archivos, 1):
        print(f"{i}. {archivo}")
    
    try:
        idx = int(input("\nElige el número del archivo: ")) - 1
        if 0 <= idx < len(archivos):
            ruta = os.path.join(target_folder, archivos[idx])
            transcribir_archivo_whisper(ruta)
        else:
            print("Opción inválida.")
    except ValueError:
        print("Error: Pon un número válido.")

def mostrar_final(texto):
    if texto:
        print("\n" + "="*50)
        print(" TRANSCRIPCIN COMPLETA (WHISPER):")
        print("="*50)
        print(texto.strip())
        print("="*50)
    else:
        print("\nNo se pudo obtener ninguna transcripcin.")

if __name__ == "__main__":
    while True:
        print("\n" + "="*50)
        print("       TRANSCRIPTOR WHISPER PRO")
        print("="*50)
        print("1. Utilizar MICRFONO (Grabacin -> Transcripcin)")
        print("2. Utilizar AUDIOS (Carpeta 'audios')")
        print("0. Salir")
        
        opcion = input("\nElige una opcin: ")
        
        if opcion == "1":
            transcribir_microfono_whisper()
        elif opcion == "2":
            menu_archivos()
        elif opcion == "0":
            print("Hasta luego!")
            break
        else:
            print("Opcin no vlida.")
