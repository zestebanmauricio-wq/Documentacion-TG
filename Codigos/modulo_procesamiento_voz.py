import sys
print("\n[!] Cargando motores de Inteligencia Artificial y Audio... (Esto puede tardar unos segundos, por favor espera)", flush=True)

import numpy as np
import librosa
import soundfile as sf
import os
import warnings

class ProcesadorVAD:
    """
    Módulo para aplicar conceptos de envolvente acústica (ADSR) 
    como Puertas de Ruido (Noise Gate) y Detección de Actividad de Voz (VAD).
    Destinado a limpiar el audio ANTES de enviarlo a Vosk o Whisper.
    """
    
    @staticmethod
    def limpiar_silencios_archivo(ruta_audio, top_db=30):
        """
        Lee un archivo de audio y utiliza lógica de VAD basada en envolvente.
        Detecta el 'Attack' y el 'Release' de la voz según el umbral (top_db)
        y recorta todos los silencios intermedios, iniciales y finales.
        """
        # Creacion automatica e inferencia de rutas
        script_dir = os.path.dirname(os.path.abspath(__file__))
        destino_dir = os.path.join(script_dir, "audios procesados")
        os.makedirs(destino_dir, exist_ok=True) # Crea la carpeta si no existe
        
        nombre_base, ext = os.path.splitext(os.path.basename(ruta_audio))
        # Asegurar extension de salida wav compatible
        ruta_salida = os.path.join(destino_dir, nombre_base + "_limpio.wav")
        
        print(f"\n[Procesador VAD] Analizando envolvente de volumen en '{os.path.basename(ruta_audio)}'...")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Cargamos transformando estandarizadamente a 16kHz
            audio_data, sr = librosa.load(ruta_audio, sr=16000)
        
        # `librosa.effects.split` identifica los intervalos donde HAY sonido activo 
        intervalos_sonido = librosa.effects.split(audio_data, top_db=top_db)
        
        if len(intervalos_sonido) == 0:
            print("[Procesador VAD] No se detectó voz clara. Retornando audio original.")
            return ruta_audio
            
        # `librosa.effects.split` identifica los intervalos donde HAY sonido activo 
        intervalos_sonido = librosa.effects.split(audio_data, top_db=top_db)
        
        if len(intervalos_sonido) == 0:
            print("[Procesador VAD] No se detectó voz clara. Retornando audio original.")
            return ruta_audio
            
        # Unimos solo los segmentos útiles (Descartamos la basura)
        audio_limpio = np.concatenate([audio_data[inicio:fin] for inicio, fin in intervalos_sonido])
        
        # Guardamos el audio optimizado de forma determinista para STT
        sf.write(ruta_salida, audio_limpio, sr, subtype='PCM_16')
        
        # Calcular cuánto le estamos ahorrando a Whisper/Vosk
        ahorro = np.clip(100 - (len(audio_limpio) / len(audio_data) * 100), 0, 100)
        print(f" -> Silencios muertos eliminados.")
        print(f" -> Ahorro de tiempo de cómputo para STT: {ahorro:.1f}%")
        print(f" -> Guardado exitosamente en: 'audios procesados/{os.path.basename(ruta_salida)}'")
        
        return ruta_salida

    @staticmethod
    def noise_gate_live(chunk_audio, umbral_amplitud=0.01):
        """
        Actúa como un Noise Gate rápido para audios en tiempo real.
        Comprueba la envolvente de la señal en este pequeño fragmento (chunk).
        """
        if chunk_audio.dtype == np.int16:
            analisis = chunk_audio.astype(np.float32) / 32768.0
        else:
            analisis = chunk_audio
            
        pico_maximo = np.max(np.abs(analisis))
        
        if pico_maximo < umbral_amplitud:
            return np.zeros_like(chunk_audio)
        else:
            return chunk_audio

# ================================
# INTERFAZ TERMINAL (CLI)
# ================================
def menu():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audios_dir = os.path.join(script_dir, "audios")
    destino_dir = os.path.join(script_dir, "audios procesados")
    
    # Crear la carpeta de salvado si falta apenas corremos el script
    os.makedirs(destino_dir, exist_ok=True)
    
    while True:
        print("\n" + "="*50)
        print("   HERRAMIENTA DE LIMPIEZA DE VOZ (VAD) ")
        print("="*50)
        print("1. Procesar y limpiar un archivo específico")
        print("2. Procesamiento y limpieza MASIVA (toda la carpeta)")
        print("3. Salir")
        
        opc = input("\nSeleccione una opción (1-3): ")
        
        if opc in ['1', '2']:
            if not os.path.exists(audios_dir):
                print(f"\n[!] Advertencia: La carpeta de origen '{audios_dir}' no existe.")
                continue
                
            archivos = [f for f in os.listdir(audios_dir) if f.lower().endswith(('.wav', '.mp3', '.flac', '.ogg'))]
            
            if not archivos:
                print(f"\n[!] No hay archivos de audio encontrados en la carpeta 'audios'.")
                continue
                
            if opc == '1':
                print("\nArchivos disponibles para procesar:")
                for i, arch in enumerate(archivos):
                    print(f" {i+1}) {arch}")
                
                try:
                    idx = int(input(f"\nSeleccione un archivo (1-{len(archivos)}): ")) - 1
                    if idx < 0 or idx >= len(archivos):
                        print("Número fuera de rango.")
                        continue
                    
                    archivo_seleccionado = os.path.join(audios_dir, archivos[idx])
                    ProcesadorVAD.limpiar_silencios_archivo(archivo_seleccionado)
                except ValueError:
                    print("Entrada inválida.")
                    
            elif opc == '2':
                print(f"\n[!] Iniciando procesamiento masivo de {len(archivos)} audios...")
                for arch in archivos:
                    ruta = os.path.join(audios_dir, arch)
                    try:
                        ProcesadorVAD.limpiar_silencios_archivo(ruta)
                    except Exception as e:
                        print(f" [Error] Falló el procesamiento de {arch}: {e}")
                        
                print(f"\n[!] ¡Operación de limpieza masiva completada con éxito!")
                print(f"Puedes ver todos los audios en la carpeta '{destino_dir}'")
                
        elif opc == '3':
            print("Cerrando el limpiador de audios...")
            break
        else:
            print("Opción inválida. Digite 1, 2 o 3.")

if __name__ == "__main__":
    menu()
