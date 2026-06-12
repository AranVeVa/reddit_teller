from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx import Crop, Resize
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import VIDEOS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, FONT_PATH
from scripts import termui as ui
from scripts.subtitles import _parse_srt


def _crop_to_vertical(clip):
    """Recorta y escala el clip a VIDEO_WIDTH x VIDEO_HEIGHT (default 1080x1920, 9:16)."""
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
    src_ratio    = clip.w / clip.h

    if src_ratio > target_ratio:
        # Video más ancho que 9:16 → recortar los lados
        new_w = int(clip.h * target_ratio)
        x1    = (clip.w - new_w) // 2
        clip  = Crop(x1=x1, x2=x1 + new_w).apply(clip)
    else:
        # Video más alto que 9:16 → recortar arriba/abajo
        new_h = int(clip.w / target_ratio)
        y1    = (clip.h - new_h) // 2
        clip  = Crop(y1=y1, y2=y1 + new_h).apply(clip)

    return Resize((VIDEO_WIDTH, VIDEO_HEIGHT)).apply(clip)


def create_video(
    audio_path: Path,
    background_video: Path,
    output_name: str,
    start_second: int = 0,
    srt_path: Path | None = None,
) -> Path:
    """
    Crea el video base (sin subtítulos):
      - Recorta el fondo a 9:16
      - Ajusta la duración al audio
      - Pega el audio
    Devuelve la ruta del video generado.
    """
    audio_path       = Path(audio_path)
    background_video = Path(background_video)
    # If subtitles requested, generate a subtitled filename so the
    # render is produced in a single pass.
    if srt_path:
        output_path = VIDEOS_DIR / f"{output_name}_subtitled.mp4"
    else:
        output_path = VIDEOS_DIR / f"{output_name}.mp4"

    try:
        audio = AudioFileClip(str(audio_path))
        video = VideoFileClip(str(background_video))

        # Recortar a partir del segundo indicado
        video = video.subclipped(start_second, start_second + audio.duration)

        # Crop y escala a 9:16
        video = _crop_to_vertical(video)

        # Asignar audio
        video = video.with_audio(audio)

        clips = [video]

        # If subtitles provided, parse and append text clips
        if srt_path:
            subtitles = _parse_srt(srt_path)
            SUBTITLE_W = int(video.w * 0.9)
            for start, end, text in subtitles:
                duration = end - start
                txt = TextClip(
                    text=text,
                    font=str(FONT_PATH),
                    font_size=int(video.w * 0.066),
                    color="white",
                    stroke_color="black",
                    stroke_width=3,
                    method="caption",
                    size=(SUBTITLE_W, 120),
                )
                y_top = int(video.h * 0.65)
                y_top = max(0, min(y_top, max(0, video.h - txt.h)))
                txt = txt.with_position(("center", y_top)).with_start(start).with_duration(duration)
                clips.append(txt)

            final = CompositeVideoClip(clips)
            final.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=video.fps,
                bitrate="500k",
                ffmpeg_params=["-crf", "28"],
            )
            ui.success(f"Video con subtítulos: {output_path}")
            return output_path

        # No subtitles: simple write
        video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            bitrate="500k",
            ffmpeg_params=["-crf", "28"],
        )
        ui.success(f"Video base guardado: {output_path}")
        return output_path

    except FileNotFoundError as e:
        ui.error(f"Archivo no encontrado: {e}")
    except Exception as e:
        ui.error(f"Error creando video: {e}")

    return None