# Explicación Detallada: `modulo_vosk.py` 🎙️

### El Rol de la Clase `VoskHelper` 🛠️

La clase `VoskHelper` no es solo un conjunto de funciones; es un **Wrapper (Envoltorio)** diseñado para abstraer la complejidad del motor Kaldi (el núcleo de Vosk). Su objetivo primordial es simplificar la interacción entre el hardware de audio y el procesamiento matemático de redes neuronales.

#### ¿Por qué usar un "Helper"?
1.  **Encapsulamiento**: Aisla los detalles técnicos (como el manejo de buffers de audio y la conversión de JSON) del resto de la aplicación.
2.  **Gestión de Recursos**: Asegura que el modelo acústico (que es pesado) se cargue **una sola vez** en memoria, optimizando el rendimiento.
3.  **Estandarización**: Garantiza que cualquier audio procesado cumpla estrictamente con los requisitos del motor (Mono, PCM 16-bit), evitando errores en tiempo de ejecución.

En resumen, actúa como un traductor entre el mundo del audio digital y el texto procesable por el sistema.

#### 💡 Un ejemplo para entenderlo mejor:
Piensa en `VoskHelper` como un **Interprete en un restaurante extranjero**:
*   **Vosk** es el Chef que solo habla un idioma técnico muy complejo.
*   **El Audio** es el pedido del cliente (lo que el usuario dijo).
*   **VoskHelper** es el mesero que:
    1. Revisa que el pedido se entienda bien antes de llevarlo a la cocina (Validación).
    2. Le traduce al Chef exactamente lo que tiene que preparar (Abstracción).
    3. Cuando el Chef termina, el mesero te trae el plato limpio y listo para comer, sin que tú tengas que entrar a la cocina a pelear con ollas y sartenes (JSON a Texto).

---


### Arquitectura de Modelos en Vosk 🌍

Vosk segmenta sus modelos principalmente en dos categorías para adaptarse a diferentes entornos de hardware:

#### 1. Tipos de Arquitectura General
| Categoría | Tamaño | RAM Req. | Uso Óptimo                                           | Vocabulario                         |
| :-------- | :----- | :------- | :--------------------------------------------------- | :---------------------------------- |
| **Small** | ~50 MB | ~300 MB  | Móviles, Raspberry Pi, aplicaciones en tiempo real.  | Dinámico (Configurable en runtime). |
| **Big**   | 1-2 GB | 4-16 GB  | Servidores, transcripción de alta precisión (Batch). | Estático (Alta fidelidad).          |

#### 2. Ecosistema para Español
Si se requiere escalar en precisión o funcionalidad, estas son las alternativas oficiales:

*   **`vosk-model-small-es-0.42`**: Evolución del modelo actual con mejoras acústicas manteniendo la ligereza.
*   **`vosk-model-es-0.42`**: El modelo "Big". Ideal para procesar audios grabados donde la precisión es crítica.
*   **`vosk-model-spk-0.4`**: Modelo especializado en **Identificación de Locutores** (quién habla).

---

### Implementación Actual: `vosk-model-small-es` 🧠

Para este proyecto, hemos seleccionado el modelo **Small** por su eficiencia en entornos locales. A continuación, se detallan sus especificaciones técnicas:

| Categoría                 | Atributo Técnico         | Descripción Detallada                                                                   |
| :------------------------ | :----------------------- | :-------------------------------------------------------------------------------------- |
| **Características**       | **Arquitectura Offline** | Inferencia local (Edge Computing) que garantiza privacidad y operabilidad sin internet. |
|                           | **Licenciamiento**       | Distribución bajo Apache 2.0. Código abierto y gratuito.                                |
|                           | **Huella de Memoria**    | Tamaño reducido (~40-50 MB), minimizando el impacto en RAM.                             |
| **Ventajas (Pros)**       | **Eficiencia**           | Optimizado para CPU, no requiere GPU.                                                   |
|                           | **Baja Latencia (RTF)**  | Respuesta casi en tiempo real para comandos sonoros.                                    |
| **Desventajas (Contras)** | **Precisión (WER)**      | Tasa de error mayor frente a modelos "Big".                                             |
|                           | **Susceptibilidad**      | Sensible al ruido de fondo y solapamiento de voces.                                     |
|                           | **Restricción Léxica**   | Menor eficacia ante terminologías técnicas muy específicas.                             |

---



### Conceptos Clave: ¿Qué es JSON? 📦

A lo largo del código verás que usamos mucho la librería `json`. **JSON** (JavaScript Object Notation) es simplemente un formato para guardar e intercambiar información de forma organizada. 

Piensa en JSON como una **ficha técnica** o un **formulario**: 
En lugar de recibir un mensaje desordenado, recibimos algo como esto:
```json
{
  "text": "hola como estas",
  "confianza": 0.98,
  "duracion": 2.5
}
```
**¿Por qué es importante en Vosk?**
Vosk no nos entrega solo el texto; nos entrega un "paquete" (un string de JSON) con mucha información extra. Usamos la función `json.loads()` para "abrir el paquete" y sacar solo el pedazo de texto que nos interesa.

---

### Bloque 1: Importaciones e Inicialización (`__init__`)
Este bloque se encarga de cargar el "cerebro" de la IA en la memoria RAM para que esté listo para escuchar.

```python
import os
import wave
import json
import vosk

class VoskHelper:
    def __init__(self, model_path="model"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"La carpeta del modelo Vosk '{model_path}' no existe.")
        print(f"[VoskHelper] Cargando modelo desde '{model_path}'...")
        self.model = vosk.Model(model_path)
        print("[VoskHelper] Modelo cargado.")
```

*   **¿Qué hace?**: Verifica que la carpeta del modelo exista. Si todo está bien, crea el objeto `self.model`.
*   **Importancia**: Cargar el modelo es la parte más pesada; al hacerlo en el `__init__`, solo se hace una vez al inicio del programa.

### Librerías Utilizadas 📚

Para la correcta ejecución de los procesos de transcripción, el sistema utiliza las siguientes dependencias:

1.  **`os` (Operating System)**: Proporciona una interfaz para interactuar con el sistema operativo. Se emplea para validar la existencia física del modelo antes de iniciar la carga.
    *   *Ejemplo*: Es como "tocar la puerta" de la carpeta del modelo para verificar que realmente está ahí.
2.  **`wave`**: Librería especializada en la gestión de archivos de audio `.wav`. Permite acceder a las cabeceras para verificar canales, tasa de muestreo y codificación.
    *   *Ejemplo*: Es quien nos avisa: "Oye, este audio es estéreo, pero yo necesito que sea Mono", leyendo la "etiqueta" interna del archivo.
3.  **`json` (JavaScript Object Notation)**: Utilizada para la deserialización de datos. Convierte las cadenas de texto estructuradas de Vosk en diccionarios de Python.
    *   *Ejemplo*: Transforma un paquete de datos complejo como `{"text": "hola"}` en algo que podamos imprimir simplemente como `hola`.
4.  **`vosk`**: Núcleo del motor de reconocimiento de voz. Implementa algoritmos y redes neuronales para la conversión de audio a texto.
    *   *Ejemplo*: Es el experto que escucha los milisegundos de audio y decide que ese sonido corresponde a la palabra "computadora".

### Bloque 2: Validación del Audio (`preparar_audio_wav`) 🌊

Este bloque funciona como un **"Control de Calidad"** antes de que el audio llegue a la IA.

```python
    def preparar_audio_wav(self, ruta_audio):
        wf = wave.open(ruta_audio, "rb")
        
        # Validaciones para Vosk
        if wf.getnchannels() != 1:
            print("[Advertencia VoskHelper] El audio no es Mono...")
        if wf.getsampwidth() != 2:
            print("[Advertencia VoskHelper] El audio no es de 16-bit...")
        if wf.getcomptype() != "NONE":
            print("[Advertencia VoskHelper] El audio parece estar comprimido...")
            
        return wf
```

#### ¿Qué es `wave` realmente?
`wave` es la herramienta que nos permite "leer las tripas" de un archivo de audio sin tener que escucharlo. Nos permite ver su configuración técnica antes de procesarlo.

#### Entendiendo las validaciones (los `if`):
Aquí es donde revisamos que el audio sea apto para la IA:

1.  **`wf.getnchannels() != 1`**: Verifica el número de canales de audio. 
    *   **Valores comunes**: `1` significa **Mono** (un solo canal) y `2` significa **Estéreo** (izquierdo y derecho). Vosk requiere `1` porque solo procesa una señal a la vez.
2.  **`wf.getsampwidth() != 2`**: Controla el ancho de muestra o "profundidad de bits". 
    *   **Valores comunes**: `1` (8 bits, baja calidad), `2` (**16 bits**, estándar CD/Vosk), `3` (24 bits) o `4` (32 bits, alta fidelidad).
3.  **`wf.getcomptype() != "NONE"`**: Detecta el tipo de compresión del archivo. 
    *   **Valores comunes**: `"NONE"` significa **PCM** (audio puro sin comprimir). Otros valores como `"ULAW"` o `"ALAW"` indican formatos comprimidos antiguos que el motor no puede leer directamente.

#### 💡 Analogía del Control de Calidad:
Imagina que Vosk es un **escáner de documentos**:
*   `getnchannels` revisa que no metas dos hojas pegadas (Estéreo).
*   `getsampwidth` revisa que la tinta sea lo suficientemente oscura para leerse (16-bit).
*   `getcomptype` revisa que la hoja no venga arrugada o doblada (Compresión).

---


### Bloque 3: El Motor de Transcripción (`transcribir_archivo`) ⚙️

```python
    def transcribir_archivo(self, ruta_audio):
        wf = self.preparar_audio_wav(ruta_audio)
        rec = vosk.KaldiRecognizer(self.model, wf.getframerate())
        textos = []
        
        while True:
            data = wf.readframes(4000) # Lee trozos de 4000 frames
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
```

Aquí es donde ocurre la conversión real de sonido a texto. Para no saturar la computadora, el proceso se hace por "pedazos".

#### El paso a paso del código:

1.  **`KaldiRecognizer(self.model, wf.getframerate())`**: Es el objeto que hace el trabajo pesado. Necesita dos cosas: el "cerebro" (el modelo que cargamos) y la "velocidad" del audio (el framerate) para saber qué tan rápido debe escuchar.
2.  **`wf.readframes(4000)`**: No podemos darle todo el audio de golpe a la IA porque se saturaría. Por eso leemos el archivo en trozos.
    *   **¿Qué es un frame? (La analogía del cine)**: Imagina que el audio es una **película**. Una película no es más que una tira de muchas **fotos (frames)** puestas una detrás de otra. 
        *   Si la frecuencia es de **16,000 Hz**, significa que en cada segundo de audio hay **16,000 fotos de sonido**.
        *   Entonces, `readframes(4000)` es como si cortaras un pedazo de esa película que mide exactamente **4,000 fotos**. 
        *   Haciendo la cuenta (`4000 / 16000`), ese "pedazo de cinta" dura **0.25 segundos**.
    *   **¿Por qué usamos 4,000?**: Es una cuestión de equilibrio (Buffer). 
        *   Si el número fuera muy pequeño (ej. 100), la computadora se cansaría de procesar tantos pedidos por segundo. 
        *   Si fuera muy grande (ej. 50,000), tendríamos que esperar muchos segundos de silencio para que la IA empezara a escribir, perdiendo el efecto de "tiempo real". 
        *   **4,000** es el punto ideal: es ligero para el procesador y lo suficientemente rápido para que la transcripción parezca instantánea.
    *   Los frames son la "distancia" o cantidad de información de sonido que recorremos en el tiempo.
3.  **`if len(data) == 0: break`**: Es el detector de "fin de pista". Comprueba si el trozo de audio que acabamos de intentar leer está vacío; si ya no queda nada, dejamos de procesar y cerramos el ciclo.
4.  **`rec.AcceptWaveform(data)`**: Es la función que "mastica" el audio. Devuelve `True` solamente cuando detecta un silencio o el final de una frase clara.
5.  **`rec.Result()` y `rec.FinalResult()`**: 
    *   `Result()` se usa mientras el audio se está reproduciendo para obtener frases terminadas. 
    *   `FinalResult()` es como "limpiar el plato"; se asegura de capturar las últimas palabras que se dijeron justo antes de que el archivo se apagara.
6.  **`" ".join(textos)`**: Como fuimos guardando frases sueltas en una lista, al final las pegamos todas con un espacio para formar un párrafo completo.

#### 💡 Analogía del Traductor de Conferencias:
Imagina que hay un traductor escuchando un discurso largo:
*   **`readframes`**: Es el traductor escuchando 3 o 4 palabras.
*   **`AcceptWaveform`**: Es el traductor esperando a que el orador tome aire o haga una pausa.
*   **`Result`**: Es cuando el traductor aprovecha esa pausa para escribir rápidamente la frase en su libreta.
*   **`FinalResult`**: Es lo que el traductor escribe al final del discurso, incluso si el orador no terminó la última frase.
*   **`join`**: Es cuando te entrega la libreta con todo el discurso escrito de corrido.

---


### Bloque 4: Transcripción de Bytes en Vivo (`transcribir_bytes`) 🎤

Este bloque es la versión "rápida" y directa. Se usa cuando el audio ya está dentro de la memoria de la computadora (por ejemplo, viniendo directamente de un micrófono) y no necesitamos leer un archivo del disco duro.

```python
    def transcribir_bytes(self, audio_bytes, framerate=16000):
        rec = vosk.KaldiRecognizer(self.model, framerate)
        rec.AcceptWaveform(audio_bytes)
        final = json.loads(rec.FinalResult())
        return final.get('text', "")
```

#### ¿En qué se diferencia del Bloque 3?
Mientras que el bloque anterior lee un archivo poco a poco, este recibe una "ráfaga" de información binaria (bytes) y la procesa de un solo golpe. Es ideal para aplicaciones de respuesta instantánea.

#### El paso a paso del código:
1.  **`audio_bytes`**: Es el parámetro que recibe los datos puros. Aquí no hay nombres de archivos, solo la información binaria del sonido.
2.  **`rec.AcceptWaveform(audio_bytes)`**: Le entregamos la ráfaga completa de sonido al motor para que la analice en ese mismo instante.
3.  **`json.loads(rec.FinalResult())`**: Como es un proceso de "un solo disparo", pedimos el resultado final de inmediato.
4.  **`return final.get('text', "")`**: Extraemos el texto del paquete JSON. Si por alguna razón no se entendió nada, devolvemos un texto vacío (`""`) para que el programa no falle.

#### 💡 Analogía del Walkie-Talkie:
*   **Bloque 3** (el de antes) era como recibir una **carta por correo**: tienes que abrir el sobre, leer hoja por hoja y luego contar de qué trataba.
*   **Bloque 4** es como hablar por un **Walkie-Talkie**: recibes el audio directamente en el aire, lo escuchas en el momento y respondes de inmediato. No hay papeles ni sobres de por medio; es una comunicación directa.

---

# Explicación Detallada: `modulos_wisper.py` 🤖

Este archivo contiene la clase `WhisperHelper`. Whisper es un modelo de reconocimiento de voz desarrollado por OpenAI. A diferencia de Vosk, que usa modelos estadísticos más tradicionales, Whisper utiliza una red neuronal transformer masiva entrenada con miles de horas de audio de internet.

### Arquitectura de Modelos en Whisper 🌍

Whisper ofrece varios tamaños de modelo. A mayor tamaño, más precisión, pero también requiere más potencia de cómputo (especialmente una tarjeta gráfica o GPU).

| Modelo                | Parámetros | Velocidad Relativa | Memoria RAM Requerida |
| :-------------------- | :--------- | :----------------- | :-------------------- |
| **Tiny**              | 39 M       | ~32x               | ~1 GB                 |
| **Base** (Usado aquí) | 74 M       | ~16x               | ~1 GB                 |
| **Small**             | 244 M      | ~6x                | ~2 GB                 |
| **Medium**            | 769 M      | ~2x                | ~5 GB                 |
| **Large**             | 1550 M     | 1x                 | ~10 GB                |

*Nota: En este proyecto usamos la versión **Base**, ya que ofrece un equilibrio perfecto entre velocidad y precisión para funcionar en una computadora normal sin necesidad de una tarjeta de video potente.*

---

#### Librerías Utilizadas:

*   **`whisper`**: Es la biblioteca de OpenAI que contiene la red neuronal procesadora de voz. Sin ella no habría transcripción inteligente.
*   **`librosa`**: Es el "laboratorio" de audio. Se usa para cargar los archivos y asegurarse de que tengan los 16,000 Hz que pide la IA.
*   **`numpy`**: Se utiliza para realizar cálculos matemáticos complejos sobre el sonido (como la normalización).
    *   *Ejemplo*: Si el volumen del audio es muy bajo, Numpy lo "estira" matemáticamente para que sea más claro.

---

### Bloque 1: Importaciones e Inicialización (`__init__`)
En esta parte cargamos el "cerebro" de la IA en la memoria.

```python
import whisper
import librosa
import numpy as np

class WhisperHelper:
    def __init__(self, model_name="base", device="cpu"):
        # Carga el modelo específico (base, tiny, etc.)
        self.model = whisper.load_model(model_name, device=device)
```

#### El paso a paso del código:
1.  **`whisper.load_model(model_name)`**: Enciende el cerebro de Whisper. A diferencia de Vosk, este modelo se descarga y se carga con un nombre (como "base", "small" o "medium") que indica qué tan inteligente (y pesado) será.

---

### Bloque 2: Preparación del Audio (`preparar_audio_archivo`)
Whisper es muy exigente con el formato del sonido y aquí lo arreglamos.

```python
    def preparar_audio_archivo(self, ruta_audio):
        # Whisper exige 16000Hz y formato float32
        audio_array, _ = librosa.load(ruta_audio, sr=16000)
        return audio_array

    def preparar_audio_bytes(self, frames_bytes):
        # Convierte los bytes del micrófono a números decimales (float32)
        audio_np = np.frombuffer(frames_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return audio_np
```

#### El paso a paso del código:
1.  **`librosa.load(ruta_audio, sr=16000)`**: Es el "preparador" del audio. Whisper necesita que el sonido sea exactamente de 16,000 Hz. Librosa se encarga de peinar y preparar el sonido para que la IA no se confunda.
2.  **`np.frombuffer(...) / 32768.0`**: Es una operación de **normalización**. Convierte los números del audio en decimales entre -1 y 1. El número `32768` es el límite de los audios de 16 bits; al dividir por él, "escalamos" el sonido a la medida exacta que pide la IA.

---

### Bloque 3: El Motor de Transcripción (`transcribir`)
Aquí se realiza el análisis final para obtener el texto.

```python
    def transcribir(self, input_data, language="es", es_archivo=False):
        if es_archivo:
            audio = self.preparar_audio_archivo(input_data)
        else:
            audio = input_data
            
        # Realiza la transcripción final
        result = self.model.transcribe(audio, language=language, fp16=False)
        return result["text"].strip()
```

#### 💡 Analogía del Erudito de Biblioteca:
Si Vosk era un traductor rápido de oficina, **Whisper es un erudito de biblioteca**. 
*   **Vosk** traduce palabra por palabra muy rápido.
*   **Whisper** se toma su tiempo para leer toda la frase, entender el contexto y luego darte una respuesta más elegante. Por eso Whisper necesita que le "limpien" el audio primero (con Librosa) antes de empezar a leer.

---

# Explicación Detallada: `juez.py` ⚖️

Este es el cerebro central del proyecto. No solo transcribe, sino que gestiona el hardware, interactúa con el usuario y genera los reportes finales.

---

#### Librerías Utilizadas:

*   **`pyaudio`**: El controlador maestro del micrófono.
*   **`jiwer`**: La calculadora científica para medir la precisión (WER).
*   **`keyboard`**: El sensor táctil para detectar la tecla Espacio.
*   **`wave`**: El bibliotecario que guarda los archivos `.wav`.
*   **`Modulo_wab` y `modulo_reportes`**: Herramientas personalizadas para limpiar el audio y crear el informe final.

---

### Bloque 1: Importaciones e Inicialización
Aquí el Juez se prepara y define sus reglas básicas.

```python
import os
import jiwer
import pyaudio
import keyboard
import time
import wave
import warnings

from modulo_vosk import VoskHelper
from modulos_wisper import WhisperHelper
from Modulo_wab import ConvertidorWab
from modulo_reportes import GeneradorReporte

# Ignoramos avisos técnicos irrelevantes
warnings.filterwarnings("ignore")

# Configuración de los modelos
MODEL_VOSK_PATH = "model"
MODEL_WHISPER_NAME = "base"
TEMP_WAV = "temp_comparacion.wav"
AUDIOS_FOLDER = "audios"
```

#### El paso a paso del código:
1.  **Imports**: Traemos tanto las librerías estándar como los "Expertos" que creamos antes (`VoskHelper` y `WhisperHelper`).
2.  **Configuración**: Definimos dónde está el cerebro de Vosk (`model`) y qué versión de Whisper usaremos (`base`).
3.  **TEMP_WAV**: Es el nombre del archivo "borrador" donde se guardará lo que grabes por el micrófono.

---

### Bloque 2: Captura de Audio Directa (`grabar_audio`)
La función que da vida al micrófono.

```python
def grabar_audio():
    p = pyaudio.PyAudio()
    rate = 16000
    chunk = 1024
    
    print("Presiona ESPACIO para comenzar a grabar...")
    keyboard.wait('space')
    
    print("Grabando...")
    frames = []
    
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate,
                    input=True, frames_per_buffer=chunk)
    
    while True:
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(data)
        if keyboard.is_pressed('space'): # Detiene al presionar de nuevo
            break
            
    # Guardado del archivo .wav
    wf = wave.open(TEMP_WAV, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)) 
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    return TEMP_WAV
```

#### El paso a paso del código:
1.  **`keyboard.wait('space')`**: El programa se queda congelado hasta que tú decidas empezar.
2.  **El bucle `while`**: Mientras el archivo se está grabando, la computadora no hace nada más que escuchar y guardar datos en la lista `frames`.
3.  **`pyaudio.paInt16`**: Asegura que el sonido sea compatible con la inteligencia artificial (Mono y de 16 bits).

---

### Bloque 3: Menú de Frases y Referencias (`menu_frases`)
Aquí el Juez define qué es lo que intentamos decir para tener una base de comparación.

```python
FRASES_PRESET = [
    "el sistema de procesamiento de lenguaje natural funciona correctamente en mi computadora local",
    "hoy es lunes seis de abril y estoy probando modelos de transcripcion automatica",
    "tres tristes tigres tragaban trigo en un trigal"
]

def menu_frases():
    print("\nPASO 1: Elegir frase de referencia")
    print("-" * 35)
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
```

#### El paso a paso del código:
1.  **`FRASES_PRESET`**: Es una lista de "frases maestras". Sirven como la referencia perfecta para calcular qué tanto se equivoca la IA.
2.  **`opc == "4"`**: Permite flexibilidad, dejando que el usuario escriba cualquier cosa en el momento.

---

### Bloque 4: Selector de Archivos Inteligente (`seleccionar_archivo_audio`)
Esta función busca audios guardados y, lo más importante, busca automáticamente su transcripción correcta.

```python
def seleccionar_archivo_audio():
    print("\n¿De qué carpeta quieres el audio?")
    print("1. 'audios' (Normales)")
    print("2. 'audios procesados' (Limpios y optimizados)")
    folder_opc = input("Elige una opción (1-2): ")
    
    target_folder = AUDIOS_FOLDER if folder_opc == "1" else "audios procesados"
    
    # Busca archivos con extensiones de audio válidas
    extensiones_validas = ('.wav', '.mp3', '.m4a', '.ogg', '.flac')
    archivos = sorted([f for f in os.listdir(target_folder) if f.lower().endswith(extensiones_validas)])
    
    for i, archivo in enumerate(archivos, 1):
        print(f"{i}. {archivo}")
        
    idx = int(input("\nElige el número del archivo: ")) - 1
    nombre_archivo = archivos[idx]
    ruta_audio = os.path.join(target_folder, nombre_archivo)
    
    # Búsqueda automática del archivo .txt asociado
    nombre_base = os.path.splitext(nombre_archivo)[0].replace("_limpio", "")
    ruta_txt = os.path.join(AUDIOS_FOLDER, nombre_base + ".txt")
    
    with open(ruta_txt, "r", encoding="utf-8") as f:
        referencia = f.read().lower().strip()
        
    return ruta_audio, referencia
```

#### El paso a paso del código:
1.  **`target_folder`**: Filtra entre los audios "crudos" y los que ya pasaron por un proceso de limpieza.
2.  **`nombre_base`**: Es un truco inteligente. Si el audio se llama `grabacion1.wav`, el Juez sabe que debe buscar un archivo llamado `grabacion1.txt` para leer la referencia.

---

### Bloque 5: Evaluación y Resultados (`calcular_y_mostrar_resultados`)
Aquí se procesa el audio simultáneamente y se generan las estadísticas.

```python
def calcular_y_mostrar_resultados(ruta_audio, referencia, vosk_motor, whisper_motor):
    print("TRANSCRIBIENDO...")
    
    # Llamada a los expertos
    texto_vosk = vosk_motor.transcribir_archivo(ruta_audio).lower()
    texto_whisper = whisper_motor.transcribir(ruta_audio, es_archivo=True).lower()

    # Cálculo del WER (Error)
    error_v = jiwer.wer(referencia, texto_vosk)
    error_w = jiwer.wer(referencia, texto_whisper)

    # Lógica de Ganador
    if error_w < error_v: ganador = "WHISPER"
    elif error_v < error_w: ganador = "VOSK"
    else: ganador = "EMPATE TÉCNICO"
        
    # Creación del reporte gráfico final
    GeneradorReporte.crear_reporte(referencia, texto_vosk, texto_whisper, error_v, error_w, ganador)
```

---

### Bloque 6: El Menú Principal (`comparar_stt`)
Es la base sobre la que corre todo el programa.

```python
def comparar_stt():
    # Inicialización de modelos
    vosk_motor = VoskHelper(MODEL_VOSK_PATH)
    whisper_motor = WhisperHelper(MODEL_WHISPER_NAME)

    while True:
        print("\n1. Grabar audio con micrófono")
        print("2. Cargar audios locales")
        print("0. Salir")
        opc = input("\nElige una opción: ")
        
        if opc == "1":
            referencia = menu_frases()
            ruta_temp = grabar_audio()
            calcular_y_mostrar_resultados(ruta_temp, referencia, vosk_motor, whisper_motor)
            
        elif opc == "2":
            ruta_audio, _ref = seleccionar_archivo_audio()
            if ruta_audio:
                ruta_optimizada = ConvertidorWab.asegurar_wav(ruta_audio)
                calcular_y_mostrar_resultados(ruta_optimizada, _ref, vosk_motor, whisper_motor)
```

#### 💡 Analogía del Juez de Boxeo:
Imagina que estás en un ring:
*   **El Micrófono** (Bloque 2) es el que suena la campana para iniciar la pelea.
*   **Vosk y Whisper** (Bloque 4) son los dos boxeadores que compiten por ver quién transcribe mejor.
*   **`juez.py`** es el árbitro que está en el medio: cronometra cuánto dura la grabación, gestiona los turnos (Bloque 5), observa los golpes (errores) con su regla matemática (Bloque 4) y al final levanta la mano del ganador entregando un reporte de la pelea.

---

