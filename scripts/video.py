from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip
from moviepy.video.fx import Crop, Resize, FadeIn, FadeOut
import math
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
    story_id: str | None = None,
    *,
    fast_mode: bool = False,  # set True for speed‑optimized encoding
    historias: list[dict] | None = None,
    story_offsets: list[float] | None = None,
    dark_mode: bool = False,  # set True to use dark template
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
    sub_dir = VIDEOS_DIR / output_name
    sub_dir.mkdir(parents=True, exist_ok=True)
    base_name = output_name
    if story_id:
        base_name = f"{output_name}_{story_id}"
    if srt_path:
        output_path = sub_dir / f"{base_name}_subtitled.mp4"
    else:
        output_path = sub_dir / f"{base_name}.mp4"

    temp_cards = []
    try:
        audio = AudioFileClip(str(audio_path))
        video = VideoFileClip(str(background_video))

        # Recortar a partir del segundo indicado
        video = video.subclipped(start_second, start_second + audio.duration)

        # Crop y escala a 9:16
        video = _crop_to_vertical(video)

        # Fast‑mode tweaks (applied before adding audio)
        if fast_mode:
            # Reduce resolution (e.g., 30% of original) to speed up processing
            video = Resize(0.3).apply(video)
            # Lower frame‑rate for testing; adjust as needed
            video = video.with_fps(12)


        # Asignar audio
        video = video.with_audio(audio)

        clips = [video]

        is_vertical = video.w < video.h

        # ── Visual Layout Config ───────────────────────────────────────────
        if is_vertical:
            card_w_est = int(video.w * 0.72)
            TOP_MARGIN = int(video.h * 0.33)   # 33% from top for vertical
            card_h_est = int(card_w_est / 1.775)
            card_bottom = TOP_MARGIN + card_h_est
            
            font_size  = int(video.w * 0.075)
            stroke_width = 2
            box_height = 200
            # Set sub_y below card_bottom with a small gap (15px) to avoid overlay in vertical
            sub_y = card_bottom + 15
        else:
            card_w_est = int(video.w * 0.34)
            TOP_MARGIN = int(video.h * 0.33)   # Lowered from 0.28 to 0.33 for horizontal
            card_h_est = int(card_w_est / 1.775)
            card_bottom = TOP_MARGIN + card_h_est
            
            font_size  = int(video.h * 0.055)
            stroke_width = 2
            box_height = 180
            # Set sub_y below card_bottom with a larger gap (45px) in horizontal
            sub_y = card_bottom + 45

        # Generate and overlay Reddit title cards for each story
        if historias and story_offsets:
            from scripts.reddit_card import generate_reddit_card
            y_pos = TOP_MARGIN
            
            for idx, h in enumerate(historias):
                t_start = story_offsets[idx]
                if t_start >= audio.duration:
                    break
                    
                temp_card_path = output_path.parent / f"temp_card_{h['id']}.png"
                generate_reddit_card(
                    subreddit=output_name,
                    title=h["title"],
                    score=h["score"],
                    video_w=video.w,
                    video_h=video.h,
                    output_path=temp_card_path,
                    dark_mode=dark_mode
                )
                temp_cards.append(temp_card_path)
                
                card_dur = min(7.0, audio.duration - t_start)
                if card_dur > 1.0:
                    card_clip = ImageClip(str(temp_card_path)).with_duration(card_dur)

                    # ── Animated entry / exit ──────────────────────────────────
                    SLIDE_IN  = 0.55   # seconds to slide in
                    SLIDE_OUT = 0.45   # seconds to slide out
                    card_h    = card_clip.h
                    target_y  = y_pos
                    # Slide offset: move 55% of card height upward from rest position.
                    # Stays on-screen so MoviePy never composites a zero-height slice.
                    slide_offset = int(card_h * 0.55)
                    start_y = max(0, target_y - slide_offset)

                    def _make_card_position(dur, ty, sy, sin, sout):
                        """Factory that captures loop vars by value (avoids closure bugs)."""
                        def _pos(t):
                            if t < sin:
                                p = 1 - (1 - t / sin) ** 3           # ease-out cubic
                                y = sy + (ty - sy) * p
                            elif t > dur - sout:
                                p = ((t - (dur - sout)) / sout) ** 3  # ease-in cubic
                                y = ty + (sy - ty) * p
                            else:
                                y = ty
                            return ("center", int(y))
                        return _pos

                    card_position = _make_card_position(
                        card_dur, target_y, start_y, SLIDE_IN, SLIDE_OUT
                    )

                    # Fade accompanies slide: appears from 0→1 opacity as it descends,
                    # disappears 1→0 as it rises back up.
                    card_clip = FadeIn(SLIDE_IN).apply(card_clip)
                    card_clip = FadeOut(SLIDE_OUT).apply(card_clip)
                    card_clip = card_clip.with_position(card_position).with_start(t_start)
                    clips.append(card_clip)

        # If subtitles provided, parse and append text clips
        if srt_path:
            subtitles = _parse_srt(srt_path)
            SUBTITLE_W = int(video.w * 0.9)

            for start, end, text in subtitles:
                duration = end - start
                txt = TextClip(
                    text=text,
                    font=str(FONT_PATH),
                    font_size=font_size,
                    color="white",
                    stroke_color="black",
                    stroke_width=stroke_width,
                    method="caption",
                    size=(SUBTITLE_W, box_height),
                    text_align="center",
                )
                y_top = max(0, min(sub_y, max(0, video.h - txt.h)))
                txt = txt.with_position(("center", y_top)).with_start(start).with_duration(duration)
                clips.append(txt)

            final = CompositeVideoClip(clips)
            final.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=video.fps,
                bitrate="8000k",
                ffmpeg_params=["-crf", "20"] + (["-preset", "ultrafast"] if fast_mode else []),
            )

            return output_path

        # No subtitles: simple write
        video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            ffmpeg_params=["-crf", "20"] + (["-preset", "ultrafast"] if fast_mode else []),
        )
        ui.success(f"Video base guardado: {output_path}")
        return output_path

    except FileNotFoundError as e:
        ui.error(f"Archivo no encontrado: {e}")
    except Exception as e:
        ui.error(f"Error creando video: {e}")
    finally:
        for tc in temp_cards:
            try:
                tc.unlink(missing_ok=True)
            except Exception:
                pass

    return None