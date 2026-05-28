import whisper
import librosa
import numpy as np
import warnings

# Ignorar advertencias de FP16 en CPU si son usuales en el equipo
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

class WhisperHelper:
    def __init__(self, model_name="base", device="cpu"):
        """
        Inicializa modelo de Whisper pasándole el tamaño (tiny, base, small) y el dispostivo.
        """
        print(f"[WhisperHelper] Cargando modelo '{model_name}' en '{device}'...")
        self.model = whisper.load_model(model_name, device=device)
        print("[WhisperHelper] Modelo cargado.")

    def preparar_audio_archivo(self, ruta_audio):
        """
        Whisper espera un array de Numpy de formato float32 con valores entre -1.0 y 1.0, 
        y con un sample rate estricto de 16000 Hz.
        `librosa.load(..., sr=16000)` hace exactamente esto y evita usar ffmpeg externo.
        """
        audio_array, _ = librosa.load(ruta_audio, sr=16000)
        return audio_array

    def preparar_audio_bytes(self, frames_bytes):
        """
        Convierte una captura de micrófono (PCM int16, en bytes) a la entrada de Whisper.
        Whisper requiere float32 normalizado.
        """
        audio_np = np.frombuffer(frames_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return audio_np

    def transcribir(self, input_data, language="es", es_archivo=False):
        """
        Toma una entrada (ya sea archivo o array normalizado) y la transcribe.
        """
        if es_archivo:
            # Si le pasamos la ruta, nosotros mismos gestionamos cómo se carga sin FFmpeg.
            audio = self.preparar_audio_archivo(input_data)
        else:
            # Asumimos que input_data ya viene correctamente en array float32
            audio = input_data
            
        result = self.model.transcribe(audio, language=language, fp16=False)
        return result["text"].strip()
