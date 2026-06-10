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
    narration_path  = Path(narration_path)
    background_path = Path(background_path)
    output          = MIXED_DIR / f"mixed_{narration_path.name}"

    # Filtro ffmpeg:
    # [1:a] = background → bajar volumen y recortar a duración de narración
    # amix  = mezclar ambos streams
    filter_complex = (
        f"[1:a]volume={BACKGROUND_VOLUME_DB}dB[bg];"
        f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]"
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