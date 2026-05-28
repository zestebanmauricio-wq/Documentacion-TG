import os
import wave
import json
import vosk

class VoskHelper:
    def __init__(self, model_path="model"):
        """
        Inicializa el modelo de Vosk asegurando que exista la ruta.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"La carpeta del modelo Vosk '{model_path}' no existe.")
        print(f"[VoskHelper] Cargando modelo desde '{model_path}'...")
        self.model = vosk.Model(model_path)
        print("[VoskHelper] Modelo cargado.")

    def preparar_audio_wav(self, ruta_audio):
        """
        Vosk requiere específicamente audios en formato PCM 16-bit, mono.
        Esta función abre el archivo wave y hace validaciones básicas.
        """
        wf = wave.open(ruta_audio, "rb")
        
        # Validaciones para Vosk
        if wf.getnchannels() != 1:
            print("[Advertencia VoskHelper] El audio no es Mono. Vosk prefiere audios de 1 canal.")
        if wf.getsampwidth() != 2:
            print("[Advertencia VoskHelper] El audio no es de 16-bit (2 bytes).")
        if wf.getcomptype() != "NONE":
            print("[Advertencia VoskHelper] El audio parece estar comprimido, Vosk espera PCM sin pérdida.")
            
        return wf

    def transcribir_archivo(self, ruta_audio):
        """
        Abre el archivo, prepara los frames como los necesita Vosk y transcribe.
        """
        wf = self.preparar_audio_wav(ruta_audio)
        rec = vosk.KaldiRecognizer(self.model, wf.getframerate())
        textos = []
        
        while True:
            # Vosk consume el audio por fragmentos (chunks)
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get('text'):
                    textos.append(result['text'])
                    
        final = json.loads(rec.FinalResult())
        if final.get('text'):
            textos.append(final['text'])
            
        wf.close()
        return " ".join(textos).strip()

    def transcribir_bytes(self, audio_bytes, framerate=16000):
        """
        Transcribe audio en tiempo real proveniente de un micrófono o flujo de bytes.
        Vosk consume directamente los bytes en formato int16 PCM.
        """
        rec = vosk.KaldiRecognizer(self.model, framerate)
        rec.AcceptWaveform(audio_bytes)
        final = json.loads(rec.FinalResult())
        return final.get('text', "")
