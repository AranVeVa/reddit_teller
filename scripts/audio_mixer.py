import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MIXED_DIR, BACKGROUND_VOLUME_DB
from scripts import termui as ui


def mix_audio(narration_path: Path, background_path: Path) -> Path | None:
    """
    Mezcla la narración con el audio de fondo usando ffmpeg directamente.
    - El fondo se baja BACKGROUND_VOLUME_DB (ej: -18 dB)
    - El resultado dura lo mismo que la narración
    """
    from moviepy import AudioFileClip

    narration_path  = Path(narration_path)
    background_path = Path(background_path)
    output          = MIXED_DIR / f"mixed_{narration_path.name}"

    try:
        clip = AudioFileClip(str(narration_path))
        duration = clip.duration
        clip.close()
    except Exception as e:
        ui.error(f"Error al obtener la duración de la narración: {e}")
        return None

    # Filtro ffmpeg:
    # [0:a] = narration → añadir 3 segundos de silencio al final
    # [1:a] = background → bajar volumen y aplicar fade-out durante los 3 segundos extra
    # amix  = mezclar ambos streams hasta que termine el primero (narración + 3s de silencio)
    fade_dur = 3.0
    filter_complex = (
        f"[0:a]apad=pad_dur={fade_dur}[narr_pad];"
        f"[1:a]volume={BACKGROUND_VOLUME_DB}dB,afade=t=out:st={duration}:d={fade_dur}[bg_fade];"
        f"[narr_pad][bg_fade]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(narration_path),
        "-i", str(background_path),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            ui.error(f"Error ffmpeg:\n{result.stderr[-500:]}")
            return None
        ui.success(f"Audio mezclado: {output}")
        return output
    except FileNotFoundError:
        ui.error("ffmpeg no encontrado. Instálalo con: sudo apt install ffmpeg")
        return None