"""Genera y mezcla efectos de sonido para la animación de la tarjeta de Reddit."""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "Sfx"
SFX_LAND = ASSETS_DIR / "card_land.wav"
SFX_EXIT = ASSETS_DIR / "card_exit.wav"

SAMPLE_RATE = 44100
LAND_VOLUME = 0.30
EXIT_VOLUME = 0.17


def _write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = b"".join(
        struct.pack("<h", max(-32767, min(32767, int(s * 32767))))
        for s in samples
    )
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)


def _generate_land_thud(duration: float = 0.32) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    rng = random.Random(7)
    phase = 0.0
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 95.0 * math.exp(-t * 14.0)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        tone = math.sin(phase) * math.exp(-t * 20.0)
        click = rng.gauss(0.0, 1.0) * math.exp(-t * 45.0) * 0.12
        out.append(tone * 0.75 + click)
    return out


def _generate_exit_whoosh(duration: float = 0.38) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    rng = random.Random(19)
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        sweep = (0.25 + 0.75 * (i / max(n - 1, 1))) ** 1.4
        env = (math.sin(math.pi * t / duration) ** 0.6) * math.exp(-t * 3.5)
        out.append(rng.gauss(0.0, 1.0) * sweep * env * 0.32)
    return out


def ensure_card_sfx() -> None:
    """Crea los WAV de la tarjeta si aún no existen."""
    if not SFX_LAND.exists():
        _write_wav(SFX_LAND, _generate_land_thud())
    if not SFX_EXIT.exists():
        _write_wav(SFX_EXIT, _generate_exit_whoosh())


def build_audio_with_card_sfx(narration, events: list[tuple[float, str]]):
    """Mezcla la narración con thud/whoosh en los instantes de la animación."""
    from moviepy import AudioFileClip, CompositeAudioClip

    if not events:
        return narration

    ensure_card_sfx()
    tracks: list[AudioFileClip] = [narration]

    for t, kind in events:
        path = SFX_LAND if kind == "land" else SFX_EXIT
        if not path.exists():
            continue
        volume = LAND_VOLUME if kind == "land" else EXIT_VOLUME
        sfx = (
            AudioFileClip(str(path))
            .with_volume_scaled(volume)
            .with_start(max(0.0, t))
        )
        tracks.append(sfx)

    if len(tracks) == 1:
        return narration

    return CompositeAudioClip(tracks).with_duration(narration.duration)
