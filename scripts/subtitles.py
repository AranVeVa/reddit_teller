import whisper
import re
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUBS_DIR, FONT_PATH


# ─── SRT generation ───────────────────────────────────────────────────────────

def _fmt_ts(seconds: float) -> str:
    ms  = int((seconds % 1) * 1000)
    s   = int(seconds) % 60
    m   = int(seconds) // 60 % 60
    h   = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _word_level_segments(whisper_segments: list[dict], words_per_card: int = 3) -> list[dict]:
    """
    Toma los segmentos de Whisper y los agrupa en tarjetas de `words_per_card` palabras.
    Si Whisper devuelve word-timestamps los usa; si no, distribuye uniformemente.
    """
    all_words = []

    for seg in whisper_segments:
        # Whisper con word_timestamps=True incluye seg["words"]
        if "words" in seg:
            all_words.extend(seg["words"])
        else:
            # Fallback: distribuir palabras en el tiempo del segmento
            words  = seg["text"].strip().split()
            dur    = (seg["end"] - seg["start"]) / max(len(words), 1)
            for j, w in enumerate(words):
                all_words.append({
                    "word":  w,
                    "start": seg["start"] + j * dur,
                    "end":   seg["start"] + (j + 1) * dur,
                })

    cards = []
    for i in range(0, len(all_words), words_per_card):
        chunk = all_words[i : i + words_per_card]
        cards.append({
            "text":  " ".join(w["word"] for w in chunk),
            "start": chunk[0]["start"],
            "end":   chunk[-1]["end"],
        })

    return cards


def generate_srt(audio_path: Path, words_per_card: int = 3) -> Path:
    """
    Transcribe el audio con Whisper y genera un SRT word-by-word.
    Devuelve la ruta del archivo .srt generado.
    """
    audio_path = Path(audio_path)
    print(f"🎙️  Transcribiendo {audio_path.name}…")

    model    = whisper.load_model("base")
    result   = model.transcribe(str(audio_path), word_timestamps=True)
    segments = result["segments"]

    cards      = _word_level_segments(segments, words_per_card)
    srt_path   = SUBS_DIR / f"{audio_path.stem}.srt"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, card in enumerate(cards, 1):
            f.write(f"{i}\n{_fmt_ts(card['start'])} --> {_fmt_ts(card['end'])}\n{card['text']}\n\n")

    print(f"✅ SRT generado: {srt_path}  ({len(cards)} tarjetas)")
    return srt_path


# ─── Subtitle burning ─────────────────────────────────────────────────────────

def _parse_srt(srt_path: Path) -> list[tuple[float, float, str]]:
    content = Path(srt_path).read_text(encoding="utf-8")
    entries = re.findall(
        r"\d+\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\n|\Z)",
        content, re.DOTALL
    )

    def to_sec(ts):
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

    return [(to_sec(s), to_sec(e), t.replace("\n", " ")) for s, e, t in entries]


def burn_subtitles(video_path: Path, srt_path: Path, output_path: Path, *, highlight: bool = False, active_word_color: str = "yellow", position_y: float = 0.65, words_per_card: int = 3, animate: bool = False) -> Path:
    """
    Quema los subtítulos del SRT sobre el video.
    Devuelve la ruta del video final.
    """
    video_path  = Path(video_path)
    output_path = Path(output_path)

    video     = VideoFileClip(str(video_path))
    subtitles = _parse_srt(srt_path)
    clips     = [video]

    for start, end, text in subtitles:
        duration = end - start
        if not highlight:
            txt = TextClip(
                text=text,
                font=str(FONT_PATH),
                font_size=71,
                color="white",
                stroke_color="black",
                stroke_width=3,
                method="label",
            )
            # Compute pixel Y and clamp so the subtitle doesn't go off-screen
            y_top = int(video.h * position_y) - (txt.h // 2)
            y_top = max(0, min(y_top, max(0, video.h - txt.h)))
            if not animate:
                txt = txt.with_position(("center", y_top)).with_start(start).with_duration(duration)
            else:
                anim_offset = 10
                anim_dur = min(0.15, max(0.05, duration * 0.2))
                posfunc = lambda t, s=start, y=y_top, d=anim_dur, o=anim_offset: ("center", y - int(max(0, min((t - s) / d, 1)) * o))
                txt = txt.with_position(posfunc).with_start(start).with_duration(duration)
            clips.append(txt)
        else:
            # Highlight mode: render each word as its own TextClip and highlight
            # the "active" word (middle word) in `active_word_color` while the
            # others stay white. NOTE: true word-by-word highlighting requires
            # per-word timestamps and rendering each word at its own timings.
            # Here we implement a simplified visual: for each subtitle card
            # (usually up to `words_per_card` words) we color the center word
            # to make it visually active for the whole card duration.
            words = text.split()
            try:
                word_clips = []
                for i, w in enumerate(words):
                    color = active_word_color if i == (len(words) // 2) else "white"
                    wc = TextClip(
                        text=w,
                        font=str(FONT_PATH),
                        font_size=71,
                        color=color,
                        stroke_color="black",
                        stroke_width=3,
                        method="label",
                    )
                    word_clips.append(wc)

                total_w = sum(c.w for c in word_clips)
                max_h = max((c.h for c in word_clips), default=0)
                x0 = (video.w - total_w) // 2
                y_center = int(video.h * position_y)

                # Compute top Y and clamp to keep words fully visible
                y_top = y_center - (max_h // 2)
                y_top = max(0, min(y_top, max(0, video.h - max_h)))

                offset = 0
                anim_offset = 10
                anim_dur = min(0.15, max(0.05, duration * 0.2))
                for wc in word_clips:
                    xv = x0 + offset
                    if not animate:
                        pos = (xv, y_top)
                        wc = wc.with_position(pos).with_start(start).with_duration(duration)
                    else:
                        posfunc = (lambda xv, s=start, y=y_top, d=anim_dur, o=anim_offset: (lambda t: (xv, y - int(max(0, min((t - s) / d, 1)) * o))))(xv, start, y_top, anim_dur, anim_offset)
                        wc = wc.with_position(posfunc).with_start(start).with_duration(duration)
                    clips.append(wc)
                    offset += wc.w
            except Exception:
                # Fallback to plain single-line subtitle if something fails
                txt = (
                    TextClip(
                        text=text,
                        font=str(FONT_PATH),
                        font_size=72,
                        color="white",
                        stroke_color="black",
                        stroke_width=3,
                        method="label",
                    )
                    .with_position(("center", position_y), relative=True)
                    .with_start(start)
                    .with_duration(duration)
                )
                clips.append(txt)

    final = CompositeVideoClip(clips)
    final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", fps=video.fps)
    print(f"✅ Video con subtítulos: {output_path}")
    return output_path