import requests
import sys
import itertools
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ELEVENLABS_API_KEYS, ELEVENLABS_VOICE_ID, AUDIOS_DIR, ELEVENLABS_SPEED
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
    # Clean input text: strip whitespace and remove unexpected control characters
    cleaned_text = texto.strip().replace("\r", "").replace("\n", " ")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    payload = {
        "text": cleaned_text,
        # Updated to a free‑tier compatible model
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "speed": min(1.2, max(0.7, ELEVENLABS_SPEED)),
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


def _split_text_into_chunks(text: str, max_chars: int = 9000) -> list[str]:
    """
    Splits text into chunks of at most `max_chars` length.
    Tries to split at sentence boundaries (.!? followed by space) or whitespace.
    """
    if len(text) <= max_chars:
        return [text]

    # Split by '.', '!', '?' followed by a space or end of string
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_len = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # If a single sentence is somehow longer than max_chars, split it by words
        if len(sentence) > max_chars:
            words = sentence.split(" ")
            for word in words:
                if current_len + len(word) + 1 > max_chars:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_len = len(word)
                else:
                    current_chunk.append(word)
                    current_len += len(word) + 1
        else:
            if current_len + len(sentence) + 1 > max_chars:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_len = len(sentence)
            else:
                current_chunk.append(sentence)
                current_len += len(sentence) + 1
                
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks


def archivo_a_audio(txt_path: Path) -> Path | None:
    """Wrapper: lee un .txt y lo convierte a audio.
    Si supera los 9000 caracteres, lo divide en partes,
    las genera individualmente por ElevenLabs, y las une al final.
    """
    txt_path = Path(txt_path)
    if not txt_path.exists():
        ui.error(f"Archivo no encontrado: {txt_path}")
        return None

    raw_text = txt_path.read_text(encoding="utf-8")
    cleaned = raw_text.strip().replace("\r", "").replace("\n", " ")
    nombre = txt_path.stem

    chunks = _split_text_into_chunks(cleaned, max_chars=9000)

    if len(chunks) == 1:
        return text_to_audio(chunks[0], nombre)

    ui.info(f"El texto es muy largo ({len(cleaned)} caracteres). Se dividirá en {len(chunks)} partes para ElevenLabs.")

    part_paths = []
    for idx, chunk in enumerate(chunks, 1):
        ui.info(f"Generando audio para la parte {idx}/{len(chunks)} ({len(chunk)} caracteres)...")
        part_name = f"{nombre}_part{idx}"
        part_path = text_to_audio(chunk, part_name)
        if not part_path:
            ui.error(f"Fallo al generar la parte {idx}. Abortando.")
            # Clean up generated parts so far
            for p in part_paths:
                if p.exists():
                    p.unlink()
            return None
        part_paths.append(part_path)

    # Combine the parts into a single audio file
    ui.info("Combinando partes de audio...")
    from moviepy import AudioFileClip
    from moviepy.audio.AudioClip import concatenate_audioclips

    try:
        clips = [AudioFileClip(str(p)) for p in part_paths]
        final_clip = concatenate_audioclips(clips)

        output_path = AUDIOS_DIR / f"{nombre}.mp3"
        final_clip.write_audiofile(
            str(output_path),
            bitrate="320k",
            logger=None
        )

        # Close clips to release files
        for clip in clips:
            clip.close()
        final_clip.close()

        # Clean up part files
        for p in part_paths:
            if p.exists():
                p.unlink()

        ui.success(f"Audio final combinado guardado: {output_path}")
        return output_path

    except Exception as e:
        ui.error(f"Error combinando archivos de audio: {e}")
        # Clean up part files in case of error
        for p in part_paths:
            if p.exists():
                p.unlink()
        return None