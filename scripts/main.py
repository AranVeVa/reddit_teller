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


# ─── constantes ───────────────────────────────────────────────────────────────

# Velocidad aproximada de narración de ElevenLabs: ~14 chars/segundo
CHARS_PER_SECOND = 14

# Presets de duración: (label, segundos_por_historia)
DURACION_PRESETS = {
    "1": ("YouTube Shorts (~60s)",     60),
    "2": ("Video corto   (~3 min)",   180),
    "3": ("Video medio   (~5 min)",   300),
    "4": ("Video largo   (~10 min)",  600),
    "5": ("Personalizado",             -1),
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def ask(prompt: str) -> bool:
    return input(f"\n{prompt} [s/n]: ").strip().lower() == "s"


def ask_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw.isdigit() else default


def elegir_duracion() -> tuple[int, int]:
    """
    Le pregunta al usuario el formato deseado.
    Devuelve (min_chars, max_chars) por historia.
    """
    print("\n📐 ¿Qué duración quieres por historia?")
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
        # Personalizado
        min_segs = ask_int("Duración mínima por historia (segundos)", 30)
        max_segs = ask_int("Duración máxima por historia (segundos)", 120)
        min_chars = min_segs * CHARS_PER_SECOND
        max_chars = max_segs * CHARS_PER_SECOND
    else:
        # Margen del ±20% para no ser demasiado estricto al filtrar posts
        min_chars = int(segs * CHARS_PER_SECOND * 0.8)
        max_chars = int(segs * CHARS_PER_SECOND * 1.2)

    print(f"\n✅ {label}: buscando historias de {min_chars}–{max_chars} caracteres")
    return min_chars, max_chars


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("       reddit_teller 2.0")
    print("=" * 50)

    # 1. Subreddit
    url = input("\nURL o nombre del subreddit: ").strip()
    subreddit = url.split("/r/")[-1].strip("/").split("/")[0] if "/r/" in url else url

    # 2. Cuántas historias
    limite = ask_int("¿Cuántas historias incluir en el video?", 1)

    # 3. Duración por historia
    min_chars, max_chars = elegir_duracion()

    # 4. Orden
    orden = input("\nOrden de posts [hot/new/top] (hot): ").strip() or "hot"

    # 5. Scraping
    print(f"\n🔍 Obteniendo historias de r/{subreddit}…")
    historias = obtener_historias(
        subreddit,
        limite=limite,
        min_chars=min_chars,
        max_chars=max_chars,
        orden=orden,
    )

    if not historias:
        print("❌ No se encontraron historias con esos parámetros.")
        print(f"   Intenta ampliar la duración o cambiar el orden (hot/new/top).")
        return

    mostrar_historias(historias)

    # Duración estimada total
    total_chars = sum(len(h["content"]) for h in historias)
    total_segs  = total_chars / CHARS_PER_SECOND
    minutos     = int(total_segs // 60)
    segundos    = int(total_segs % 60)
    print(f"\n⏱️  Duración estimada del video: {minutos}m {segundos}s")

    archivo_txt = guardar_historias(historias, subreddit)

    if not ask("¿Continuar con la generación de audio (ElevenLabs)?"):
        print("👋 Proceso terminado.")
        return

    # 6. TTS
    audio_path = archivo_a_audio(archivo_txt)
    if not audio_path:
        print("❌ Error generando audio. Saliendo.")
        return

    if not ask("¿Continuar con la mezcla de audio?"):
        print("👋 Proceso terminado.")
        return

    # 7. Mezcla
    mixed_path = mix_audio(audio_path, BACKGROUND_AUDIO)
    if not mixed_path:
        print("❌ Error mezclando audio. Saliendo.")
        return

    if not ask("¿Continuar con la creación del video?"):
        print("👋 Proceso terminado.")
        return

    # 8. Video base (9:16, sin subtítulos)
    start_sec  = ask_int("¿Desde qué segundo del video de fondo empezar?", 0)
    video_path = create_video(mixed_path, BACKGROUND_VIDEO, subreddit, start_second=start_sec)
    if not video_path:
        print("❌ Error creando video. Saliendo.")
        return

    if not ask("¿Agregar subtítulos al video?"):
        print(f"\n✅ Listo. Video sin subtítulos: {video_path}")
        return

    # 9. Subtítulos word-by-word
    words_per_card = ask_int("¿Palabras por tarjeta de subtítulo?", 3)
    srt_path       = generate_srt(audio_path, words_per_card=words_per_card)

    animate_subs = ask("¿Animar subtítulos?")

    final_path = video_path.parent / f"{video_path.stem}_subtitled.mp4"
    burn_subtitles(video_path, srt_path, final_path, animate=animate_subs)

    print(f"\n🎬 ¡Listo! Video final: {final_path}")


if __name__ == "__main__":
    main()