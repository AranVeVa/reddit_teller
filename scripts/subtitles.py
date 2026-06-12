import whisper
import re
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SUBS_DIR, FONT_PATH
from scripts import termui as ui


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
        chunk_words = [w["word"] for w in chunk]
        
        # Group into lines of at most 3 words
        lines = []
        for j in range(0, len(chunk_words), 3):
            lines.append(" ".join(chunk_words[j : j + 3]))
        
        cards.append({
            "text":  "\n".join(lines),
            "start": chunk[0]["start"],
            "end":   chunk[-1]["end"],
        })

    return cards


def generate_srt(audio_path: Path, words_per_card: int = 3) -> Path:
    audio_path = Path(audio_path)
    ui.info(f"Transcribiendo {audio_path.name}...")

    model    = whisper.load_model("base")
    result   = model.transcribe(str(audio_path), word_timestamps=True)
    segments = result["segments"]

    cards      = _word_level_segments(segments, words_per_card)
    srt_path   = SUBS_DIR / f"{audio_path.stem}.srt"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, card in enumerate(cards, 1):
            f.write(f"{i}\n{_fmt_ts(card['start'])} --> {_fmt_ts(card['end'])}\n{card['text']}\n\n")

    ui.success(f"SRT generado: {srt_path}  ({len(cards)} tarjetas)")
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

    return [(to_sec(s), to_sec(e), t.strip()) for s, e, t in entries]


def burn_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    *,
    position_y: float = 0.65,
) -> Path:
    video_path  = Path(video_path)
    output_path = Path(output_path)

    video     = VideoFileClip(str(video_path))
    subtitles = _parse_srt(srt_path)
    clips     = [video]

    SUBTITLE_W = int(video.w * 0.9)

    for start, end, text in subtitles:
        duration = end - start

        txt = TextClip(
            text=text,
            font=str(FONT_PATH),
            font_size=int(video.w * 0.075),
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(SUBTITLE_W, 200),
            text_align="center",
        )
        y_top = int(video.h * position_y)
        y_top = max(0, min(y_top, max(0, video.h - txt.h)))
        txt = txt.with_position(("center", y_top)).with_start(start).with_duration(duration)
        clips.append(txt)

    final = CompositeVideoClip(clips)
    final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", fps=video.fps)
    ui.success(f"Video con subtítulos: {output_path}")
    return output_path