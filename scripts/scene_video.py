#!/usr/bin/env python3
"""
scene_video.py — Genera un video a partir de las imágenes de escenas.

Efectos:
  - Ken Burns (zoom 100% → 115%) en cada imagen
  - Dissolve (cross-fade 0.5s) entre clips
  - Fade-out (1.5s) al final del último clip
  - El último clip recibe +3 segundos extra

Audio:
  Busca automáticamente el audio mezclado por story_id.

Salida:
  outputs/scenes/<story_id>/<story_id>_scenes.mp4

Uso:
  python scripts/scene_video.py 1tw1yr8
"""
import sys
import json
import numpy as np
import argparse
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from moviepy import VideoClip, CompositeVideoClip, AudioFileClip
from moviepy.video.fx import FadeIn, FadeOut

from config import SCENES_DIR, MIXED_DIR, VIDEO_WIDTH, VIDEO_HEIGHT
from scripts import termui as ui


# ── Configuración ───────────────────────────────────────────────────────────
TRANSITION_DURATION = 1.5   # duración del dissolve entre clips (segundos)
LAST_EXTRA_SECONDS  = 3.0   # segundos extra al final del último clip
FADEOUT_DURATION    = 3.5   # duración del fade-out final
OUTPUT_FPS          = 24
ZOOM_START          = 1.0   # zoom inicial (100%)
ZOOM_END            = 1.15  # zoom final   (115%)


# ── Ken Burns ───────────────────────────────────────────────────────────────
def make_ken_burns_clip(
    img_path: Path,
    duration: float,
    w: int,
    h: int,
    zoom_start: float = ZOOM_START,
    zoom_end: float = ZOOM_END,
) -> VideoClip:
    """
    Crea un VideoClip a partir de una imagen estática con efecto Ken Burns.
    Hace zoom de zoom_start a zoom_end de manera lineal durante toda la duración.
    """
    img = Image.open(img_path).convert("RGB")

    # El canvas debe ser lo suficientemente grande para acomodar el zoom máximo.
    # A zoom_end, el viewport visible es (w, h), así que el canvas es w*zoom_end × h*zoom_end.
    canvas_w = int(w * zoom_end) + 4  # +4 por margen de redondeo
    canvas_h = int(h * zoom_end) + 4
    img = img.resize((canvas_w, canvas_h), Image.LANCZOS)
    img_array = np.array(img)

    def make_frame(t: float) -> np.ndarray:
        # Progreso lineal de 0 a 1 a lo largo del clip
        progress = min(t / duration, 1.0) if duration > 0 else 0.0
        zoom = zoom_start + (zoom_end - zoom_start) * progress

        # Viewport en el espacio del canvas:
        # Cuando zoom=zoom_start (1.0) → vp es canvas completo (ancho) → muestra todo
        # Cuando zoom=zoom_end (1.15)  → vp es más pequeño      → muestra menos → zoom in
        vp_w = int(w * zoom_end / zoom)
        vp_h = int(h * zoom_end / zoom)

        # Recorte centrado
        x0 = max(0, (canvas_w - vp_w) // 2)
        y0 = max(0, (canvas_h - vp_h) // 2)
        x1 = min(canvas_w, x0 + vp_w)
        y1 = min(canvas_h, y0 + vp_h)

        cropped = img_array[y0:y1, x0:x1]

        # Escalar el viewport de vuelta al tamaño de salida
        frame = np.array(
            Image.fromarray(cropped).resize((w, h), Image.BILINEAR)
        )
        return frame

    return VideoClip(make_frame, duration=duration).with_fps(OUTPUT_FPS)


# ── Audio: buscar por story_id ───────────────────────────────────────────────
def find_audio(story_id: str, subreddit: str) -> Path | None:
    """
    Busca el archivo de audio mezclado en las ubicaciones posibles.
    """
    candidates = [
        MIXED_DIR / subreddit / f"mixed_{subreddit}_{story_id}.mp3",
        MIXED_DIR / f"mixed_{subreddit}_{story_id}.mp3",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


# ── Main ─────────────────────────────────────────────────────────────────────
def build_scene_clip(story_id: str) -> "CompositeVideoClip | None":
    """
    Construye y devuelve el clip compuesto de escenas (sin audio, sin render).
    Listo para ser usado directamente como fondo en create_video().
    Las transiciones dissolve (FadeIn) se solapan hacia atrás para que el inicio
    de cada escena coincida exactamente con su marca de tiempo en la narración.
    """
    scenes_dir  = SCENES_DIR / story_id
    scenes_json = scenes_dir / "scenes.json"

    if not scenes_json.exists():
        ui.error(f"No se encontró scenes.json en {scenes_dir}")
        ui.info(f"Ejecuta primero: python scripts/scene_generator.py {story_id}")
        return None

    with open(scenes_json, encoding="utf-8") as f:
        plan = json.load(f)

    scenes    = plan["scenes"]
    subreddit = plan["subreddit"]
    ui.success(f"Plan cargado: {len(scenes)} escenas | r/{subreddit} | {plan['total_duration']:.1f}s")

    # Construir clips con Ken Burns y transiciones alineadas
    ui.info("Aplicando efecto Ken Burns...")
    all_clips = []

    for i, scene in enumerate(scenes):
        n        = scene["scene_number"]
        t_start  = float(scene["time_start"])
        t_end    = float(scene["time_end"])
        base_dur = t_end - t_start

        # Si no es la primera escena, empezamos TRANSITION_DURATION segundos antes
        # para que se desvanezca (FadeIn) sobre la escena anterior.
        if i > 0:
            start_time = t_start - TRANSITION_DURATION
            clip_dur   = base_dur + TRANSITION_DURATION
        else:
            start_time = t_start
            clip_dur   = base_dur

        # Añadir segundos extra al final de la última escena
        if i == len(scenes) - 1:
            clip_dur += LAST_EXTRA_SECONDS

        img_path = scenes_dir / f"scene_{n:02d}.png"
        if not img_path.exists():
            ui.error(f"Imagen no encontrada: {img_path.name}")
            return None

        ui.info(
            f"  Escena {n}: {img_path.name} "
            f"[{t_start:.1f}s–{t_end:.1f}s] "
            f"start={start_time:.1f}s, dur={clip_dur:.1f}s"
        )

        clip = make_ken_burns_clip(img_path, clip_dur, VIDEO_WIDTH, VIDEO_HEIGHT)

        # Aplicar transiciones
        if i > 0:
            clip = FadeIn(TRANSITION_DURATION).apply(clip)

        if i == len(scenes) - 1:
            clip = FadeOut(FADEOUT_DURATION).apply(clip)

        clip = clip.with_start(start_time)
        all_clips.append(clip)

    # Duración total real del video (incluyendo el tiempo extra del final)
    total_duration = float(scenes[-1]["time_end"]) + LAST_EXTRA_SECONDS
    ui.info(f"Duración total del fondo: {total_duration:.1f}s")

    final = CompositeVideoClip(all_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    final = final.with_duration(total_duration).with_fps(OUTPUT_FPS)
    return final


def generate_scene_video(story_id: str) -> Path | None:
    """
    Uso standalone: construye el clip de escenas, le agrega el audio
    mezclado y lo renderiza a un archivo mp4.
    """
    scenes_dir  = SCENES_DIR / story_id
    scenes_json = scenes_dir / "scenes.json"
    if not scenes_json.exists():
        ui.error(f"No se encontró scenes.json en {scenes_dir}")
        return None
    with open(scenes_json, encoding="utf-8") as f:
        plan = json.load(f)
    subreddit = plan["subreddit"]

    # Buscar audio
    audio_path = find_audio(story_id, subreddit)
    if audio_path:
        ui.success(f"Audio: {audio_path.name}")
    else:
        ui.warn("No se encontró audio. El video se generará sin sonido.")

    # Construir clip
    final = build_scene_clip(story_id)
    if final is None:
        return None

    # Agregar audio
    if audio_path:
        audio = AudioFileClip(str(audio_path))
        if audio.duration > final.duration:
            audio = audio.subclipped(0, final.duration)
        final = final.with_audio(audio)

    # Renderizar
    output_path = scenes_dir / f"{story_id}_scenes.mp4"
    ui.info(f"Renderizando → {output_path}...")
    print()

    final.write_videofile(
        str(output_path),
        fps=OUTPUT_FPS,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-crf", "20"],
        logger="bar",
    )

    print()
    ui.success(f"Video guardado: {output_path}")
    return output_path


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Genera video con Ken Burns + dissolve a partir de imágenes de escenas."
    )
    parser.add_argument("story_id", help="ID de la historia (ej: 1tw1yr8)")
    args = parser.parse_args()

    result = generate_scene_video(args.story_id)
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
