import vosk
import sys
import os
import pyaudio
import json
import keyboard
import time
import wave

# --- CONFIGURACIN ---
MODEL_PATH = "model"
AUDIOS_FOLDER = "audios"

# Verificar si el modelo existe
if not os.path.exists(MODEL_PATH):
    print(f"\n[ERROR] No se encontr la carpeta '{MODEL_PATH}'.")
    print("Por favor, baja el modelo y ponlo en esta carpeta con ese nombre.")
    sys.exit(1)

# Asegurarse de que la carpeta de audios existe
if not os.path.exists(AUDIOS_FOLDER):
    os.makedirs(AUDIOS_FOLDER)
    print(f"\n[AVISO] Se ha creado la carpeta '{AUDIOS_FOLDER}'. Pon tus archivos .wav ah.")

model = vosk.Model(MODEL_PATH)

def mostrar_final(full_text):
    if full_text:
        print("\n" + "="*50)
        print(" TRANSCRIPCIN COMPLETA:")
        print("="*50)
        # Limpiamos posibles espacios duplicados
        limpio = " ".join(full_text).strip()
        print(limpio)
        print("="*50)
    else:
        print("\nNo se gener ninguna transcripcin.")

def transcribir_archivo(ruta_archivo):
    """Funcin interna para procesar un archivo Wav"""
    if not os.path.exists(ruta_archivo):
        print(f"Error: No existe el archivo {ruta_archivo}")
        return []

    try:
        wf = wave.open(ruta_archivo, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print(f"\n[ERROR] El archivo '{ruta_archivo}' debe ser WAV Mono PCM de 16 bits.")
            return []

        rec = vosk.KaldiRecognizer(model, wf.getframerate())
        textos = []

        print(f"\n[INFO] Procesando: {os.path.basename(ruta_archivo)}...")
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    textos.append(result['text'])
        
        # Resultado final
        final = json.loads(rec.FinalResult())
        if final.get('text'):
            textos.append(final['text'])
        
        return textos
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return []

def menu_audios():
    """Opción 2: Listar archivos en la carpeta audios y elegir uno"""
    print("\n¿De qué carpeta quieres el audio?")
    print("1. 'audios' (Normales)")
    print("2. 'audios procesados' (Limpios y optimizados)")
    folder_opc = input("Elige una opción (1-2): ")
    
    target_folder = AUDIOS_FOLDER if folder_opc == "1" else "audios procesados"
    
    if not os.path.exists(target_folder):
        print(f"\nLa carpeta '{target_folder}' no existe.")
        return

    archivos = [f for f in os.listdir(target_folder) if f.endswith(".wav")]
    
    if not archivos:
        print(f"\nNo hay archivos .wav en la carpeta '{target_folder}'.")
        return

    print(f"\nArchivos encontrados en '{target_folder}':")
    for i, archivo in enumerate(archivos, 1):
        print(f"{i}. {archivo}")
    
    try:
        idx = int(input("\nElige el número del archivo a transcribir: ")) - 1
        if 0 <= idx < len(archivos):
            ruta = os.path.join(target_folder, archivos[idx])
            resultado = transcribir_archivo(ruta)
            mostrar_final(resultado)
        else:
            print("Opción no válida.")
    except ValueError:
        print("Entrada no válida. Debes poner un número.")

def transcribir_microfono():
    """Opcin 1: Micrfono en tiempo real"""
    rec = vosk.KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, 
                        input=True, frames_per_buffer=8000)
        stream.start_stream()

        print("\n" + "="*50)
        print(" MODO MICRFONO EN VIVO")
        print("="*50)
        print("Presiona ESPACIO para comenzar...")
        keyboard.wait('space')
        
        print("\nEscuchando! Habla ahora (Presiona ESPACIO para detener)...")
        time.sleep(0.5)

        full_text = []

        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                p_text = result.get('text', '')
                if p_text:
                    print(f"\n[FINAL]: {p_text}")
                    full_text.append(p_text)
            else:
                partial = json.loads(rec.PartialResult())
                p_partial = partial.get('partial', '')
                if p_partial:
                    print(f"\r>> {p_partial}", end="")

            if keyboard.is_pressed('space'):
                print("\n\nGrabacin detenida por el usuario.")
                break
        
        stream.stop_stream()
        stream.close()
        mostrar_final(full_text)

    except Exception as e:
        print(f"\nError con el micrfono: {e}")
    finally:
        p.terminate()

if __name__ == "__main__":
    while True:
        print("\n" + "="*50)
        print("       TRANSCRIPTOR VOSK PRO")
        print("="*50)
        print("1. Utilizar MICRFONO (En vivo)")
        print("2. Utilizar AUDIOS (Carpeta 'audios')")
        print("0. Salir")
        
        opcion = input("\nElige una opcin: ")
        
        if opcion == "1":
            transcribir_microfono()
        elif opcion == "2":
            menu_audios()
        elif opcion == "0":
            print("Adis!")
            break
        else:
            print("Opcin incorrecta.")
