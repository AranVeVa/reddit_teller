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
    all_words = []

    for seg in whisper_segments:
        if "words" in seg:
            all_words.extend(seg["words"])
        else:
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


def burn_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    *,
    highlight: bool = False,
    active_word_color: str = "yellow",
    position_y: float = 0.65,
    words_per_card: int = 3,
    animate: bool = False,
) -> Path:
    video_path  = Path(video_path)
    output_path = Path(output_path)

    video     = VideoFileClip(str(video_path))
    subtitles = _parse_srt(srt_path)
    clips     = [video]

    # Ancho fijo para que el TextClip no corte texto
    SUBTITLE_W = int(video.w * 0.9)  # 90% del ancho del video

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
                method="caption",
                size=(SUBTITLE_W, 120),  # ancho fijo, alto automático
            )
            y_top = int(video.h * position_y)
            y_top = max(0, min(y_top, max(0, video.h - txt.h)))

            if not animate:
                txt = txt.with_position(("center", y_top)).with_start(start).with_duration(duration)
            else:
                anim_dur = min(0.15, max(0.05, duration * 0.2))
                posfunc = lambda t, s=start, y=y_top, d=anim_dur: (
                    "center",
                    y - int(max(0, min((t - s) / d, 1)) * 10)
                )
                txt = txt.with_position(posfunc).with_start(start).with_duration(duration)

            clips.append(txt)

        else:
            # Highlight por palabra: cada palabra tiene su propio clip y timing
            words = text.split()
            word_duration = duration / max(len(words), 1)

            try:
                word_clips = []
                for i, w in enumerate(words):
                    word_start = start + i * word_duration
                    word_end   = word_start + word_duration

                    # Renderizar todas las palabras en blanco en cada tarjeta
                    # pero la palabra activa (i) en color destacado
                    row_clips = []
                    for j, ww in enumerate(words):
                        color = active_word_color if j == i else "white"
                        wc = TextClip(
                            text=ww,
                            font=str(FONT_PATH),
                            font_size=71,
                            color=color,
                            stroke_color="black",
                            stroke_width=3,
                            method="caption",
                            size=(SUBTITLE_W // max(len(words), 1), None),
                        )
                        row_clips.append(wc)

                    total_w  = sum(c.w for c in row_clips)
                    max_h    = max(c.h for c in row_clips)
                    x0       = (video.w - total_w) // 2
                    y_top    = int(video.h * position_y) - (max_h // 2)
                    y_top    = max(0, min(y_top, max(0, video.h - max_h)))

                    offset = 0
                    for wc in row_clips:
                        xv = x0 + offset
                        if not animate:
                            wc = wc.with_position((xv, y_top)).with_start(word_start).with_duration(word_duration)
                        else:
                            anim_dur = min(0.15, max(0.05, word_duration * 0.2))
                            posfunc = (lambda xv=xv, y=y_top, s=word_start, d=anim_dur: (
                                lambda t: (xv, y - int(max(0, min((t - s) / d, 1)) * 10))
                            ))()
                            wc = wc.with_position(posfunc).with_start(word_start).with_duration(word_duration)
                        clips.append(wc)
                        offset += wc.w

            except Exception as e:
                print(f"⚠️  Fallback subtitle para: {text} ({e})")
                txt = (
                    TextClip(
                        text=text,
                        font=str(FONT_PATH),
                        font_size=71,
                        color="white",
                        stroke_color="black",
                        stroke_width=3,
                        method="caption",
                        size=(SUBTITLE_W, 120),
                    )
                    .with_position(("center", int(video.h * position_y)), relative=False)
                    .with_start(start)
                    .with_duration(duration)
                )
                clips.append(txt)

    final = CompositeVideoClip(clips)
    final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", fps=video.fps)
    print(f"✅ Video con subtítulos: {output_path}")
    return output_path