import os
import jiwer
import pyaudio
import keyboard
import time
import wave
import warnings
import re

def normalizar_texto(texto):
    """Convierte a minúsculas, elimina signos de puntuación y espacios extra para mejorar precisión."""
    if not texto: return ""
    texto = str(texto).lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    return " ".join(texto.split())

from modulo_vosk import VoskHelper
from modulos_wisper import WhisperHelper
from Modulo_wab import ConvertidorWab
from modulo_reportes import GeneradorReporte
from modulo_procesamiento_voz import ProcesadorVAD

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# --- CONFIGURACIÓN ---
MODEL_VOSK_PATH = "model"
MODEL_WHISPER_NAME = "base"
TEMP_WAV = "temp_comparacion.wav"
AUDIOS_FOLDER = "audios"

# Crear carpeta de audios si no existe
if not os.path.exists(AUDIOS_FOLDER):
    os.makedirs(AUDIOS_FOLDER)

FRASES_PRESET = [
    "el sistema de procesamiento de lenguaje natural funciona correctamente en mi computadora local",
    "hoy es lunes seis de abril y estoy probando modelos de transcripcion automatica",
    "tres tristes tigres tragaban trigo en un trigal"
]

def grabar_audio():
    p = pyaudio.PyAudio()
    rate = 16000
    chunk = 1024
    
    print("\n" + "="*50)
    print("      GRABACIÓN PARA COMPARAR")
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
                print("\nGrabación finalizada.")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(TEMP_WAV, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)) 
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return TEMP_WAV
    except Exception as e:
        print(f"\n[ERROR] Fallo con el micrófono: {e}")
        return None

def menu_frases():
    print("\n--- MENÚ DE FRASES PREESTABLECIDAS ---")
    print("1. El sistema de procesamiento de lenguaje natural...")
    print("2. Hoy es lunes seis de abril...")
    print("3. Tres tristes tigres...")
    print("4. Escribir frase personalizada")
    
    opc = input("\nElige una opción: ")
    
    if opc == "1": return FRASES_PRESET[0]
    if opc == "2": return FRASES_PRESET[1]
    if opc == "3": return FRASES_PRESET[2]
    if opc == "4": return input("Escribe tu frase:\n> ").lower().strip()
    return None

def menu_seleccion_referencia(nombre_base_audio):
    """Permite al usuario elegir qué texto usar como referencia para la evaluación"""
    while True:
        print(f"\nPASO 2: Seleccionar texto de referencia para el audio seleccionado")
        print("-" * 65)
        
        # 1. Sugerencia por nombre (Comportamiento anterior mejorado)
        ruta_sugerida = os.path.join(AUDIOS_FOLDER, nombre_base_audio + ".txt")
        tiene_sugerencia = os.path.exists(ruta_sugerida)
        
        if tiene_sugerencia:
            print(f"1. [RECOMENDADO] Usar archivo detectado: '{nombre_base_audio}.txt'")
        else:
            print(f"1. Buscar archivo automático (No se encontró '{nombre_base_audio}.txt')")
        
        print("2. Listar todos los archivos .txt en la carpeta 'audios'")
        print("3. Usar una de las frases rápidas (Presets)")
        print("4. Escribir el texto manualmente ahora mismo")
        
        opc = input("\nElige cómo indicar la referencia (1-4): ")
        
        if opc == "1":
            if tiene_sugerencia:
                with open(ruta_sugerida, "r", encoding="utf-8") as f:
                    return f.read().lower().strip()
            else:
                print(f"\n[!] El archivo '{ruta_sugerida}' no existe. Por favor, elige otra opción.")
        
        elif opc == "2":
            archivos_txt = sorted([f for f in os.listdir(AUDIOS_FOLDER) if f.lower().endswith(".txt") and f.lower() != "readme.txt"])
            if not archivos_txt:
                print("\n[!] No hay archivos .txt en la carpeta 'audios'.")
                continue
            
            print("\nArchivos de texto disponibles:")
            for i, f_txt in enumerate(archivos_txt, 1):
                print(f"{i}. {f_txt}")
            
            try:
                idx = int(input("\nElige el número del archivo .txt: ")) - 1
                if 0 <= idx < len(archivos_txt):
                    with open(os.path.join(AUDIOS_FOLDER, archivos_txt[idx]), "r", encoding="utf-8") as f:
                        return f.read().lower().strip()
            except ValueError:
                print("Error: Ingresa un número válido.")
        
        elif opc == "3":
            ref = menu_frases()
            if ref: return ref
            
        elif opc == "4":
            return input("\nEscribe el texto de referencia exactamente como se dijo:\n> ").lower().strip()
        
        else:
            print("Opción inválida.")

def seleccionar_archivo_audio():
    """Muestra los audios de la carpeta y pregunta por el texto de referencia"""
    print("\n¿De qué carpeta quieres el audio?")
    print("1. 'audios' (Normales)")
    print("2. 'audios procesados' (Limpios y optimizados)")
    folder_opc = input("Elige una opción (1-2): ")
    
    target_folder = AUDIOS_FOLDER if folder_opc == "1" else "audios procesados"
    
    if not os.path.exists(target_folder):
        print(f"\n[!] La carpeta '{target_folder}' no existe.")
        return None, None

    extensiones_validas = ('.wav', '.mp3', '.m4a', '.ogg', '.flac', '.aac')
    archivos = sorted([f for f in os.listdir(target_folder) if f.lower().endswith(extensiones_validas) and "_convertido.wav" not in f])
    
    if not archivos:
        print(f"\n[!] No hay archivos de audio aceptables en la carpeta '{target_folder}'.")
        return None, None

    print(f"\nArchivos en '{target_folder}':")
    for i, archivo in enumerate(archivos, 1):
        print(f"{i}. {archivo}")
        
    try:
        idx = int(input("\nElige el número del audio: ")) - 1
        if 0 <= idx < len(archivos):
            nombre_archivo = archivos[idx]
            ruta_audio = os.path.join(target_folder, nombre_archivo)
            
            # Limpiamos el nombre para sugerir el TXT (ej: "audio_limpio.wav" -> "audio")
            nombre_base = os.path.splitext(nombre_archivo)[0].replace("_limpio", "")
            
            print(f"\n[OK] Audio seleccionado: {nombre_archivo}")
            
            # NUEVO: Preguntar qué texto usar
            referencia = menu_seleccion_referencia(nombre_base)
            
            if not referencia:
                print("[!] No se seleccionó una referencia. Abortando.")
                return None, None
                
            return ruta_audio, referencia
        else:
            print("Opción inválida.")
            return None, None
    except ValueError:
        print("Error: Pon un número válido.")
        return None, None

def calcular_y_mostrar_resultados(ruta_audio, referencia, vosk_motor, whisper_motor):
    referencia = normalizar_texto(referencia)
    print("\n" + "-"*50)
    print("TRANSCRIBIENDO... (esto tardará unos segundos)")
    print("-" * 50)
    
    # Medir VOSK
    inicio_v = time.time()
    texto_vosk = normalizar_texto(vosk_motor.transcribir_archivo(ruta_audio))
    tiempo_v = time.time() - inicio_v
    print(f"VOSK OK ({tiempo_v:.2f}s).")
    
    # Medir WHISPER
    inicio_w = time.time()
    texto_whisper = normalizar_texto(whisper_motor.transcribir(ruta_audio, es_archivo=True))
    tiempo_w = time.time() - inicio_w
    print(f"WHISPER OK ({tiempo_w:.2f}s).")

    # Resultados Analizados (Cálculo del WER)
    error_v = jiwer.wer(referencia, texto_vosk)
    error_w = jiwer.wer(referencia, texto_whisper)

    print("\n" + "="*95)
    print(f"{'MODELO':<15} | {'TIEMPO (s)':<12} | {'WER (%)':<12} | {'TRANSCRIPCIÓN'}")
    print("-" * 95)
    print(f"{'VOSK':<15} | {tiempo_v:<12.2f}s | {error_v*100:<12.2f}% | {texto_vosk}")
    print(f"{'WHISPER':<15} | {tiempo_w:<12.2f}s | {error_w*100:<12.2f}% | {texto_whisper}")
    print("=" * 95)
    print(f"\nReferencia original: '{referencia}'")
    
    if error_w < error_v:
        ganador = "WHISPER"
        print(f"\n 🏆 GANADOR EN PRECISIÓN: WHISPER")
    elif error_v < error_w:
        ganador = "VOSK"
        print(f"\n 🏆 GANADOR EN PRECISIÓN: VOSK")
    else:
        ganador = "EMPATE TÉCNICO"
        print("\n Empate técnico en precisión.")
        
    # --- LLAMADA AL GENERACIÓN DEL REPORTE MD ---
    while True:
        resp = input("\n¿Deseas generar el reporte completo de esta prueba? (s/n): ").strip().lower()
        if resp in ['s', 'n']:
            break
        print("Por favor, ingresa 's' para sí o 'n' para no.")
        
    try:
        import sys
        reportes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Reportes"))
        if reportes_dir not in sys.path:
            sys.path.append(reportes_dir)
        from modulo_visualizacion import plot_audio_file_static
        
        if resp == 's':
            nombre = input("Ingresa un nombre para el reporte (deja en blanco para usar el nombre por defecto): ").strip()
            print("\n[!] Generando análisis visual...")
            ruta_img = plot_audio_file_static(ruta_audio, "all", save_report=True, report_name=nombre)
            GeneradorReporte.crear_reporte(referencia, texto_vosk, texto_whisper, error_v, error_w, ganador, nombre, ruta_img, tiempo_v, tiempo_w)
        else:
            print("\n[!] Abriendo visualización gráfica. (Cierra la ventana gráfica para volver al menú)")
            plot_audio_file_static(ruta_audio, "all", save_report=False)
            print("\nReporte omitido.")
            
    except Exception as e:
        print(f"\n[ERROR] No se pudo cargar el visualizador: {e}")
        if resp == 's':
            GeneradorReporte.crear_reporte(referencia, texto_vosk, texto_whisper, error_v, error_w, ganador, getattr(locals(), 'nombre', ''), "", tiempo_v, tiempo_w)

def comparar_stt():
    if not os.path.exists(MODEL_VOSK_PATH):
        print(f"\n[ERROR] No se encontró la carpeta '{MODEL_VOSK_PATH}'.")
        return

    print("\nIniciando Motores de Inteligencia Artificial...")
    vosk_motor = VoskHelper(MODEL_VOSK_PATH)
    whisper_motor = WhisperHelper(MODEL_WHISPER_NAME)

    while True:
        print("\n" + "="*50)
        print("      VOSK VS WHISPER (MENÚ PRINCIPAL)")
        print("="*50)
        print("1. Grabar audio con micrófono y evaluar")
        print("2. Cargar audios locales (Carpeta 'audios')")
        print("3. Comparar visualmente 2 audios (Módulo visualizador)")
        print("0. Salir")
        
        opc = input("\nElige una opción: ")
        
        if opc == "1":
            referencia = menu_frases()
            if not referencia: continue
            referencia = normalizar_texto(referencia)
            ruta_temp = grabar_audio()
            if not ruta_temp: continue
            
            # --- AGREGAR LIMPIEZA VAD ---
            from modulo_procesamiento_voz import ProcesadorVAD
            inicio_vad = time.time()
            ruta_limpia = ProcesadorVAD.limpiar_silencios_archivo(ruta_temp)
            tiempo_vad = time.time() - inicio_vad
            
            # --- Transcribir Bruto (Audio 1) ---
            print("\n" + "-"*50)
            print("TRANSCRIBIENDO AUDIO ORIGINAL...")
            print("-" * 50)
            st_v1 = time.time(); t_v1 = normalizar_texto(vosk_motor.transcribir_archivo(ruta_temp)); tt_stt1_v = time.time() - st_v1
            st_w1 = time.time(); t_w1 = normalizar_texto(whisper_motor.transcribir(ruta_temp, es_archivo=True)); tt_stt1_w = time.time() - st_w1
            err_v1 = jiwer.wer(referencia, t_v1)
            err_w1 = jiwer.wer(referencia, t_w1)
            
            # --- Transcribir Limpio (Audio 2) ---
            print("\n" + "-"*50)
            print("TRANSCRIBIENDO AUDIO PROCESADO (VAD)...")
            print("-" * 50)
            st_v2 = time.time(); t_v2 = normalizar_texto(vosk_motor.transcribir_archivo(ruta_limpia)); tt_stt2_v = time.time() - st_v2
            st_w2 = time.time(); t_w2 = normalizar_texto(whisper_motor.transcribir(ruta_limpia, es_archivo=True)); tt_stt2_w = time.time() - st_w2
            err_v2 = jiwer.wer(referencia, t_v2)
            err_w2 = jiwer.wer(referencia, t_w2)
            
            print("\n" + "="*80)
            print(f"RESUMEN DE TIEMPOS:")
            print(f"Limpieza VAD: {tiempo_vad:.2f}s")
            print(f"Audio 1 (Obs): Vosk {tt_stt1_v:.2f}s | Whisper {tt_stt1_w:.2f}s")
            print(f"Audio 2 (Lim): Vosk {tt_stt2_v:.2f}s | Whisper {tt_stt2_w:.2f}s")
            print("="*80)
            
            try:
                import sys
                reportes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Reportes"))
                if reportes_dir not in sys.path:
                    sys.path.append(reportes_dir)
                from modulo_visualizacion import plot_two_audios_compare
                
                print("\n¿Qué deseas hacer a continuación?")
                print("1. Terminar aquí (Ver solo el error WER en pantalla)")
                print("2. Generar el REPORTE COMPLETO VS (Gráficas visuales + Archivo .MD)")
                while True:
                    resp = input("Selecciona una opción (1-2): ").strip()
                    if resp in ['1', '2']: break
                
                if resp == '2':
                    nombre_rep = input("Ingresa un nombre para el reporte (Ej: 'Prueba_En_Vivo_1'): ").strip()
                    print("\n[!] Abriendo comparativa visual lado a lado. Cierra la ventana gráfica para guardar el reporte...")
                    ruta_img_vs = plot_two_audios_compare(ruta_temp, ruta_limpia, save_report=True, report_name=nombre_rep, auto_show=True)
                    GeneradorReporte.crear_reporte_completo_vs(ruta_temp, ruta_limpia, referencia, t_v1, t_w1, err_v1, err_w1, t_v2, t_w2, err_v2, err_w2, ruta_img_vs, nombre_rep, tiempo_vad, tt_stt1_v, tt_stt1_w, tt_stt2_v, tt_stt2_w)
                else:
                    print("\nAnalítica gráfica y reporte visual omitidos.")
            except Exception as e:
                print(f"[ERROR] No se pudo generar el VS Automático: {e}")
                
            # Limpiar archivos temporales
            if os.path.exists(ruta_temp): os.remove(ruta_temp)
            # El procesador VAD tira el archivo en "audios procesados/temp_comparacion_limpio.wav"
            if os.path.exists(ruta_limpia): os.remove(ruta_limpia)
            
        elif opc == "2":
            ruta_audio, _ref = seleccionar_archivo_audio()
            if ruta_audio and _ref:
                # AQUÍ USAMOS TU NUEVO MÓDULO WAB
                ruta_optimizada = ConvertidorWab.asegurar_wav(ruta_audio)
                
                if ruta_optimizada:
                    calcular_y_mostrar_resultados(ruta_optimizada, _ref, vosk_motor, whisper_motor)
                    
                    # Opcional: Eliminar el audio convertido luego de usarlo
                    if "_convertido.wav" in ruta_optimizada and os.path.exists(ruta_optimizada):
                        os.remove(ruta_optimizada)
                else:
                    print("[!] No se pudo continuar con la evaluación debido a un error en el archivo de audio.")
                    
        elif opc == "3":
            print("\n--- SELECCIÓN DEL PRIMER AUDIO (Ej: Original) ---")
            ruta_audio1, ref1 = seleccionar_archivo_audio()
            if not ruta_audio1: continue
            ref1 = normalizar_texto(ref1)
            
            print("\n--- SELECCIÓN DEL SEGUNDO AUDIO (Ej: Procesado) ---")
            ruta_audio2, ref2 = seleccionar_archivo_audio()
            if not ruta_audio2: continue
            ref2 = normalizar_texto(ref2)
            
            # Aseguramos que sea wav para vosk y whisper
            ruta_audio1_opt = ConvertidorWab.asegurar_wav(ruta_audio1)
            
            # --- Transcribir Audio 1 ---
            print("\n" + "-"*50)
            print(f"TRANSCRIBIENDO AUDIO 1: {os.path.basename(ruta_audio1)}")
            print("-" * 50)
            st1_v = time.time(); t_v1 = normalizar_texto(vosk_motor.transcribir_archivo(ruta_audio1_opt)); tt1_v = time.time() - st1_v
            st1_w = time.time(); t_w1 = normalizar_texto(whisper_motor.transcribir(ruta_audio1_opt, es_archivo=True)); tt1_w = time.time() - st1_w
            err_v1 = jiwer.wer(ref1, t_v1)
            err_w1 = jiwer.wer(ref1, t_w1)
            
            # Aseguramos que sea wav para vosk y whisper
            ruta_audio2_opt = ConvertidorWab.asegurar_wav(ruta_audio2)
            
            # --- Transcribir Audio 2 ---
            print("\n" + "-"*50)
            print(f"TRANSCRIBIENDO AUDIO 2: {os.path.basename(ruta_audio2)}")
            print("-" * 50)
            st2_v = time.time(); t_v2 = normalizar_texto(vosk_motor.transcribir_archivo(ruta_audio2_opt)); tt2_v = time.time() - st2_v
            st2_w = time.time(); t_w2 = normalizar_texto(whisper_motor.transcribir(ruta_audio2_opt, es_archivo=True)); tt2_w = time.time() - st2_w
            err_v2 = jiwer.wer(ref2, t_v2)
            err_w2 = jiwer.wer(ref2, t_w2)
            
            try:
                import sys
                reportes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "Reportes"))
                if reportes_dir not in sys.path:
                    sys.path.append(reportes_dir)
                from modulo_visualizacion import plot_two_audios_compare
                
                while True:
                    resp = input("\n¿Deseas generar el reporte COMPLETO (WER + Gráficas VS)? (s/n): ").strip().lower()
                    if resp in ['s', 'n']: break
                    print("Ingresa 's' para sí o 'n' para no.")
                
                if resp == 's':
                    nombre_rep = input("Ingresa un nombre para el reporte (deja en blanco para usar defecto): ").strip()
                    print("\n[!] Abriendo comparativa visual lado a lado. Cierra la ventana para continuar calculando el reporte...")
                    ruta_img_vs = plot_two_audios_compare(ruta_audio1, ruta_audio2, save_report=True, report_name=nombre_rep, auto_show=True)
                    GeneradorReporte.crear_reporte_completo_vs(ruta_audio1, ruta_audio2, ref1, t_v1, t_w1, err_v1, err_w1, t_v2, t_w2, err_v2, err_w2, ruta_img_vs, nombre_rep, 0, tt1_v, tt1_w, tt2_v, tt2_w)
                else:
                    print("\n[!] Abriendo comparativa visual lado a lado. Cierra la ventana para volver al menú...")
                    plot_two_audios_compare(ruta_audio1, ruta_audio2, save_report=False, auto_show=True)
                    print("\nReporte omitido.")
                    
                # Limpiar
                if "_convertido.wav" in ruta_audio1_opt and os.path.exists(ruta_audio1_opt): os.remove(ruta_audio1_opt)
                if "_convertido.wav" in ruta_audio2_opt and os.path.exists(ruta_audio2_opt): os.remove(ruta_audio2_opt)
                
            except Exception as e:
                print(f"\n[ERROR] No se pudo cargar el visualizador o generar reporte: {e}")
        
        elif opc == "0":
            print("Saliendo del evaluador...")
            break
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    try:
        comparar_stt()
    except Exception as e:
        print(f"\nOcurrió algo al ejecutar: {e}")
