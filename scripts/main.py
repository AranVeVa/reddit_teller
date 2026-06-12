#!/usr/bin/env python3
"""
reddit_teller — pipeline principal
Uso: python scripts/main.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BACKGROUND_AUDIO, BACKGROUND_VIDEO, AUDIOS_DIR, MIXED_DIR, SUBS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, STORIES_DIR
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

    from moviepy import AudioFileClip
    from moviepy.audio.AudioClip import concatenate_audioclips

    story_audios = []
    story_offsets = []
    current_offset = 0.0

    subreddit_story_dir = STORIES_DIR / subreddit
    subreddit_story_dir.mkdir(parents=True, exist_ok=True)

    for idx, h in enumerate(historias, 1):
        ui.info(f"Generando audio para la historia {idx}/{len(historias)}: {h['title']}...")
        temp_story_txt = subreddit_story_dir / f"temp_{h['id']}.txt"
        temp_story_txt.write_text(f"{h['title']}\n{h['content']}\n", encoding="utf-8")
        
        story_audio_path = archivo_a_audio(temp_story_txt)
        temp_story_txt.unlink(missing_ok=True)
        
        if not story_audio_path:
            ui.error(f"Fallo al generar audio para la historia {idx}. Saliendo.")
            for p in story_audios:
                if p.exists():
                    p.unlink()
            return
            
        story_audios.append(story_audio_path)
        
        clip = AudioFileClip(str(story_audio_path))
        duration = clip.duration
        clip.close()
        
        story_offsets.append(current_offset)
        current_offset += duration

    ui.info("Combinando audios de las historias...")
    try:
        clips = [AudioFileClip(str(p)) for p in story_audios]
        final_audio = concatenate_audioclips(clips)
        
        combined_audio_name = f"{subreddit}_{historias[0]['id']}.mp3"
        temp_combined_path = AUDIOS_DIR / combined_audio_name
        final_audio.write_audiofile(str(temp_combined_path), bitrate="320k", logger=None)
        
        for c in clips:
            c.close()
        final_audio.close()
        
        for p in story_audios:
            if p.exists():
                p.unlink()
                
        audio_path = temp_combined_path
        
    except Exception as e:
        ui.error(f"Error combinando audios: {e}")
        for p in story_audios:
            if p.exists():
                p.unlink()
        return

    # Organize audio into subreddit subfolder with story ID
    audio_sub_dir = AUDIOS_DIR / subreddit
    audio_sub_dir.mkdir(parents=True, exist_ok=True)
    audio_new_path = audio_sub_dir / audio_path.name
    audio_path.rename(audio_new_path)
    audio_path = audio_new_path

    if not ask("¿Continuar con la mezcla de audio?"):
        ui.info("Proceso terminado.")
        return

    mixed_path = mix_audio(audio_path, BACKGROUND_AUDIO)
    if not mixed_path:
        ui.error("Error mezclando audio. Saliendo.")
        return
    # Organize mixed audio into subreddit subfolder with story ID
    mixed_sub_dir = MIXED_DIR / subreddit
    mixed_sub_dir.mkdir(parents=True, exist_ok=True)
    mixed_new_path = mixed_sub_dir / mixed_path.name
    mixed_path.rename(mixed_new_path)
    mixed_path = mixed_new_path

    if not ask("¿Continuar con la creación del video?"):
        ui.info("Proceso terminado.")
        return

    start_sec = ask_int("¿Desde qué segundo del video de fondo empezar?", 0)

    # Preguntar sobre subtítulos *antes* de renderizar para poder
    # quemarlos en la misma pasada y evitar renderizar dos veces.
    add_subs = ask("¿Agregar subtítulos al video?")
    srt_path = None
    if add_subs:
        words_per_card = ask_int("¿Palabras por tarjeta de subtítulo?", 3)
        is_vertical = VIDEO_WIDTH < VIDEO_HEIGHT
        srt_path = generate_srt(audio_path, words_per_card=words_per_card, is_vertical=is_vertical)
        # Organize subtitles into subreddit subfolder with story ID
        subs_sub_dir = SUBS_DIR / subreddit
        subs_sub_dir.mkdir(parents=True, exist_ok=True)
        srt_new_path = subs_sub_dir / srt_path.name
        srt_path.rename(srt_new_path)
        srt_path = srt_new_path

    # Preguntar sobre modo oscuro para la tarjeta de Reddit
    dark_mode = ask("¿Usar la tarjeta de Reddit en modo oscuro (dark mode)?")

    video_path = create_video(
        mixed_path, 
        BACKGROUND_VIDEO, 
        subreddit, 
        start_second=start_sec, 
        srt_path=srt_path, 
        story_id=historias[0]["id"],
        historias=historias,
        story_offsets=story_offsets,
        dark_mode=dark_mode
    )
    if not video_path:
        ui.error("Error creando video. Saliendo.")
        return

    if srt_path:
        ui.success(f"Video final: {video_path}")
    else:
        ui.success(f"Listo. Video sin subtítulos: {video_path}")

if __name__ == "__main__":
    main()