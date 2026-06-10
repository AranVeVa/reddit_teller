import requests
import sys
import itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ELEVENLABS_API_KEYS, ELEVENLABS_VOICE_ID, AUDIOS_DIR
from scripts import termui as ui

# Ciclo infinito sobre las keys → rota automáticamente
_key_cycle = itertools.cycle(ELEVENLABS_API_KEYS)


def _next_key() -> str:
    return next(_key_cycle)


def text_to_audio(texto: str, nombre: str) -> Path | None:
    """
    Convierte `texto` a MP3 usando ElevenLabs.
    `nombre` define el nombre del archivo de salida (sin extensión).
    Rota las API keys automáticamente si hay varias.
    Devuelve la ruta del archivo generado, o None si falla.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    payload = {
        "text": texto,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
        },
    }

    intentos = len(ELEVENLABS_API_KEYS) or 1

    for _ in range(intentos):
        api_key = _next_key()
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
        except requests.exceptions.RequestException as e:
            ui.error(f"Error de conexión: {e}")
            continue

        if resp.status_code == 200:
            output = AUDIOS_DIR / f"{nombre}.mp3"
            output.write_bytes(resp.content)
            ui.success(f"Audio guardado: {output}")
            return output

        elif resp.status_code in (401, 429):
            ui.warn(f"ElevenLabs respondió {resp.status_code}")
            ui.info(resp.text[:500])
            continue

        else:
            ui.error(f"Error ElevenLabs {resp.status_code}: {resp.text[:200]}")
            return None

    ui.error("Todas las API keys fallaron.")
    return None


def archivo_a_audio(txt_path: Path) -> Path | None:
    """Wrapper: lee un .txt y lo convierte a audio."""
    txt_path = Path(txt_path)
    if not txt_path.exists():
        ui.error(f"Archivo no encontrado: {txt_path}")
        return None

    texto = txt_path.read_text(encoding="utf-8")
    nombre = txt_path.stem
    return text_to_audio(texto, nombre)