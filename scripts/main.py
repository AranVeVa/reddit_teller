#!/usr/bin/env python3
"""
reddit_teller — pipeline principal
Uso: python scripts/main.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BACKGROUND_AUDIO, BACKGROUND_VIDEO
from scripts.reddit      import obtener_historias, guardar_historias, mostrar_historias
from scripts.voice       import archivo_a_audio
from scripts.audio_mixer import mix_audio
from scripts.video       import create_video
from scripts.subtitles   import generate_srt, burn_subtitles
from scripts import termui as ui


CHARS_PER_SECOND = 14

DURACION_PRESETS = {
    "1": ("YouTube Shorts (~60s)",     60),
    "2": ("Video corto   (~3 min)",   180),
    "3": ("Video medio   (~5 min)",   300),
    "4": ("Video largo   (~10 min)",  600),
    "5": ("Personalizado",             -1),
}


def ask(prompt: str) -> bool:
    return input(f"\n{ui.prompt_str(prompt)} [s/n]: ").strip().lower() == "s"


def ask_int(prompt: str, default: int) -> int:
    raw = input(f"{ui.prompt_str(prompt)} [{default}]: ").strip()
    return int(raw) if raw.isdigit() else default


def elegir_duracion() -> tuple[int, int]:
    ui.info("\n¿Qué duración quieres por historia?")
    print()
    for key, (label, segs) in DURACION_PRESETS.items():
        if segs > 0:
            chars = segs * CHARS_PER_SECOND
            print(f"  [{key}] {label}  →  ~{chars} caracteres")
        else:
            print(f"  [{key}] {label}")

    opcion = input("\nElige [1-5]: ").strip()

    if opcion not in DURACION_PRESETS:
        print("Opción inválida, usando Shorts por defecto.")
        opcion = "1"

    label, segs = DURACION_PRESETS[opcion]

    if segs == -1:
        min_segs = ask_int("Duración mínima por historia (segundos)", 30)
        max_segs = ask_int("Duración máxima por historia (segundos)", 120)
        min_chars = min_segs * CHARS_PER_SECOND
        max_chars = max_segs * CHARS_PER_SECOND
    else:
        min_chars = int(segs * CHARS_PER_SECOND * 0.7)
        max_chars = int(segs * CHARS_PER_SECOND * 1.5)

    ui.success(f"{label}: buscando historias de {min_chars}–{max_chars} caracteres")
    return min_chars, max_chars


def main():
    ui.header("reddit_teller 2.0")

    # Status steps: fetch, audio, mix, video, subtitles
    status = ui.Status(5)

    url = input(f"\n{ui.prompt_str('URL o nombre del subreddit: ')}").strip()
    subreddit = url.split("/r/")[-1].strip("/").split("/")[0] if "/r/" in url else url

    limite = ask_int("¿Cuántas historias incluir en el video?", 1)

    min_chars, max_chars = elegir_duracion()

    orden = input(f"\n{ui.prompt_str('Orden de posts [hot/new/top] (hot): ')}").strip() or "hot"

    ui.info(f"Obteniendo historias de r/{subreddit}...")
    historias = obtener_historias(
        subreddit,
        limite=limite,
        min_chars=min_chars,
        max_chars=max_chars,
        orden=orden,
    )

    if not historias:
        ui.error("No se encontraron historias con esos parámetros.")
        ui.info("Intenta ampliar la duración o cambiar el orden (hot/new/top).")
        return

    mostrar_historias(historias)

    total_chars = sum(len(h["content"]) for h in historias)
    total_segs  = total_chars / CHARS_PER_SECOND
    minutos     = int(total_segs // 60)
    segundos    = int(total_segs % 60)
    ui.info(f"Duración estimada del video: {minutos}m {segundos}s")

    archivo_txt = guardar_historias(historias, subreddit)

    if not ask("¿Continuar con la generación de audio (ElevenLabs)?"):
        ui.info("Proceso terminado.")
        return

    audio_path = archivo_a_audio(archivo_txt)
    if not audio_path:
        ui.error("Error generando audio. Saliendo.")
        return
    status.update(message="Audio generado")

    if not ask("¿Continuar con la mezcla de audio?"):
        ui.info("Proceso terminado.")
        return

    mixed_path = mix_audio(audio_path, BACKGROUND_AUDIO)
    if not mixed_path:
        ui.error("Error mezclando audio. Saliendo.")
        return
    status.update(message="Audio mezclado")

    if not ask("¿Continuar con la creación del video?"):
        ui.info("Proceso terminado.")
        return

    start_sec  = ask_int("¿Desde qué segundo del video de fondo empezar?", 0)
    video_path = create_video(mixed_path, BACKGROUND_VIDEO, subreddit, start_second=start_sec)
    if not video_path:
        ui.error("Error creando video. Saliendo.")
        return
    status.update(message="Video creado")

    if not ask("¿Agregar subtítulos al video?"):
        ui.success(f"Listo. Video sin subtítulos: {video_path}")
        return

    words_per_card = ask_int("¿Palabras por tarjeta de subtítulo?", 3)
    srt_path       = generate_srt(audio_path, words_per_card=words_per_card)

    final_path = video_path.parent / f"{video_path.stem}_subtitled.mp4"
    burn_subtitles(video_path, srt_path, final_path)

    ui.success(f"Video final: {final_path}")
    status.update(message="Subtítulos añadidos")


if __name__ == "__main__":
    main()