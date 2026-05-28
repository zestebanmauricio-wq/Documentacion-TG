import os
import librosa
import soundfile as sf
import warnings

class ConvertidorWab:
    @staticmethod
    def asegurar_wav(ruta_audio):
        """
        Toma cualquier archivo de audio (MP3, FLAC, OGG, WAV), lo lee y lo estandariza.
        Obliga al audio a estar exactamente en 16000 Hz, 1 Canal (Mono), y formato PCM 16-bits.
        (Esto es necesario porque Vosk arroja error si el WAV no tiene estas características exactas).
        """
        nombre_base, ext = os.path.splitext(ruta_audio)
        ruta_salida = nombre_base + "_convertido.wav"
        
        # Si ya es el temporal que produce el propio micrófono, no lo procesamos porque ya viene listo.
        if "temp_comparacion" in ruta_audio:
            return ruta_audio

        print(f"\n[Modulo WAB] Optimizando '{os.path.basename(ruta_audio)}'...")
        print("[Modulo WAB] Convirtiendo a formato estándar (16kHz, Mono, PCM 16-bit)...")
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Librosa transforma lo que sea a array a 16kHz en Mono
                audio_data, sr = librosa.load(ruta_audio, sr=16000, mono=True)
            
            # Soundfile lo inyecta a un archivo WAV nativo
            sf.write(ruta_salida, audio_data, sr, subtype='PCM_16')
            
            print(f"[Modulo WAB] Listo! Archivo guardado como '{os.path.basename(ruta_salida)}'.")
            return ruta_salida
            
        except Exception as e:
            print(f"\n[!] ERROR CRÍTICO: No se pudo procesar el audio '{os.path.basename(ruta_audio)}'.")
            print(f"    Detalle técnico: {e}")
            print("    TIP: Si el archivo es .aac o .mp3, asegúrate de tener FFmpeg instalado en tu sistema.")
            return None
