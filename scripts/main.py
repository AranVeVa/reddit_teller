#!/usr/bin/env python3
"""
reddit_teller — pipeline principal
Uso: python scripts/main.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BACKGROUND_AUDIO, BACKGROUND_VIDEO, AUDIOS_DIR, MIXED_DIR, SUBS_DIR, SCENES_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, STORIES_DIR, OPENAI_API_KEY
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


def get_silent_audio_path(duration: float) -> Path:
    path = AUDIOS_DIR / f"silence_{duration}.mp3"
    if not path.exists():
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            str(path)
        ]
        subprocess.run(cmd, capture_output=True)
    return path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="reddit_teller 2.0 — automatic pipeline")
    parser.add_argument("--subreddit", "-s", help="URL o nombre del subreddit")
    parser.add_argument("--limit", "-l", type=int, help="Número de historias a incluir")
    parser.add_argument("--duration", "-d", choices=["1", "2", "3", "4", "5"], help="Preset de duración")
    parser.add_argument("--min-secs", type=int, help="Duración mínima en segundos (para opción personalizada)")
    parser.add_argument("--max-secs", type=int, help="Duración máxima en segundos (para opción personalizada)")
    parser.add_argument("--order", "-o", choices=["hot", "new", "top"], help="Orden de los posts")
    parser.add_argument("--scenes", action="store_true", default=None, help="Usar escenas generadas por IA")
    parser.add_argument("--no-scenes", action="store_false", dest="scenes", help="Usar video de fondo clásico")
    parser.add_argument("--subs", action="store_true", default=None, help="Agregar subtítulos quemados")
    parser.add_argument("--no-subs", action="store_false", dest="subs", help="No agregar subtítulos")
    parser.add_argument("--words-per-card", "-w", type=int, help="Palabras por tarjeta de subtítulo")
    parser.add_argument("--dark-mode", action="store_true", default=None, help="Usar Reddit card en modo oscuro")
    parser.add_argument("--light-mode", action="store_false", dest="dark_mode", help="Usar Reddit card en modo claro")
    parser.add_argument("--start-sec", type=int, help="Segundo de inicio para el video clásico")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-aprobar todas las confirmaciones")
    args = parser.parse_args()

    ui.header("reddit_teller 2.0")

    def confirm(prompt_text: str) -> bool:
        if args.yes:
            return True
        return ask(prompt_text)

    # 1. Subreddit
    if args.subreddit:
        url = args.subreddit
    else:
        url = input(f"\n{ui.prompt_str('URL o nombre del subreddit: ')}").strip()
    subreddit = url.split("/r/")[-1].strip("/").split("/")[0] if "/r/" in url else url

    # 2. Límite
    if args.limit is not None:
        limite = args.limit
    else:
        limite = ask_int("¿Cuántas historias incluir en el video?", 1)

    # 3. Duración
    if args.duration:
        opcion = args.duration
        label, segs = DURACION_PRESETS[opcion]
        if segs == -1:
            min_segs = args.min_secs if args.min_secs is not None else ask_int("Duración mínima por historia (segundos)", 30)
            max_segs = args.max_secs if args.max_secs is not None else ask_int("Duración máxima por historia (segundos)", 120)
            min_chars = min_segs * CHARS_PER_SECOND
            max_chars = max_segs * CHARS_PER_SECOND
        else:
            min_chars = int(segs * CHARS_PER_SECOND * 0.7)
            max_chars = int(segs * CHARS_PER_SECOND * 1.5)
        ui.success(f"{label}: buscando historias de {min_chars}–{max_chars} caracteres")
    else:
        min_chars, max_chars = elegir_duracion()

    # 4. Orden
    if args.order:
        orden = args.order
    else:
        orden = input(f"\n{ui.prompt_str('Orden de posts [hot/new/top] (hot): ')}").strip() or "hot"

    ui.info(f"Obteniendo candidatos de r/{subreddit}...")
    # Buscamos un pool más grande para permitir rechazos del usuario
    candidatos = obtener_historias(
        subreddit,
        limite=max(50, limite * 10),
        min_chars=min_chars,
        max_chars=max_chars,
        orden=orden,
    )

    if not candidatos:
        ui.error("No se encontraron historias con esos parámetros.")
        ui.info("Intenta ampliar la duración o cambiar el orden (hot/new/top).")
        return

    from scripts.reddit import _save_used_id

    historias_aceptadas = []
    subreddit_story_dir = STORIES_DIR / subreddit
    subreddit_story_dir.mkdir(parents=True, exist_ok=True)

    for c_idx, h in enumerate(candidatos):
        if len(historias_aceptadas) >= limite:
            break

        ui.header(f"Candidato {c_idx+1}/{len(candidatos)} (Aceptados: {len(historias_aceptadas)}/{limite})")
        ui.info(f"Título: {h['title']}")
        ui.info(f"Score: {h['score']} | Caracteres: {len(h['content'])}")
        preview = h["content"]
        ui.info(f"Preview:\n{preview}")
        print()

        if args.yes:
            opcion = "s"
        else:
            opcion = input(f"{ui.prompt_str('¿Deseas continuar con esta historia? [s/n/q] (s): ')}").strip().lower() or "s"

        if opcion == "q":
            ui.info("Proceso terminado por el usuario.")
            return
        elif opcion == "n":
            ui.warn(f"Historia {h['id']} rechazada y marcada como usada.")
            is_vertical = VIDEO_WIDTH < VIDEO_HEIGHT
            _save_used_id(h["id"], title=h["title"], subreddit=subreddit, is_vertical=is_vertical)
            continue

        # Opción "s"
        story_file = subreddit_story_dir / f"{subreddit}_{h['id']}.txt"
        story_file.write_text(f"{h['title']}\n\n{h['content']}\n", encoding="utf-8")
        
        if not args.yes:
            ui.success(f"Historia guardada en: {story_file}")
            ui.info("Abre el archivo anterior, edítalo como desees y guárdalo.")
            input(f"\n{ui.prompt_str('Presiona ENTER cuando hayas terminado de editar para continuar... ')}")
            
            # Recargar los cambios hechos por el usuario
            try:
                content_edited = story_file.read_text(encoding="utf-8")
                lines = content_edited.splitlines()
                if lines:
                    h['title'] = lines[0].strip()
                    content_lines = lines[1:]
                    while content_lines and not content_lines[0].strip():
                        content_lines.pop(0)
                    h['content'] = "\n".join(content_lines).strip()
                ui.success("Historia editada cargada correctamente.")
            except Exception as e:
                ui.error(f"Error al leer la edición ({e}). Se usará la versión original.")

        historias_aceptadas.append(h)

    if len(historias_aceptadas) < limite:
        ui.warn(f"Solo se aceptaron {len(historias_aceptadas)} de las {limite} historias solicitadas.")
        if not historias_aceptadas:
            ui.error("No se aceptó ninguna historia. Saliendo.")
            return
        if not confirm("¿Deseas continuar con las historias aceptadas?"):
            return

    historias = historias_aceptadas

    # Mostrar las historias aceptadas definitivas
    mostrar_historias(historias)

    total_chars = sum(len(h["content"]) for h in historias)
    total_segs  = total_chars / CHARS_PER_SECOND
    minutos     = int(total_segs // 60)
    segundos    = int(total_segs % 60)
    ui.info(f"Duración estimada del video: {minutos}m {segundos}s")

    # Guardar las historias aceptadas (y editadas) en el archivo combinado para referencia
    is_vertical = VIDEO_WIDTH < VIDEO_HEIGHT
    archivo_txt = guardar_historias(historias, subreddit, is_vertical=is_vertical)

    if not confirm("¿Continuar con la generación de audio (ElevenLabs)?"):
        ui.info("Proceso terminado.")
        return

    from moviepy import AudioFileClip
    from moviepy.audio.AudioClip import concatenate_audioclips

    story_audios = []
    story_durations = []

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
        story_durations.append(duration)

    ui.info("Combinando audios de las historias...")
    try:
        PAUSE_DURATION = 2.2
        CARD_PRE_DELAY = 1.2  # Card appears 1.2 seconds before the narration starts
        
        clips = []
        story_offsets = []
        current_time = 0.0
        
        silent_path = get_silent_audio_path(PAUSE_DURATION)
        
        for idx, (path, duration) in enumerate(zip(story_audios, story_durations)):
            story_clip = AudioFileClip(str(path))
            
            if idx == 0:
                story_offsets.append(0.0)
                clips.append(story_clip)
                current_time += duration
            else:
                silent_clip = AudioFileClip(str(silent_path))
                clips.append(silent_clip)
                
                # Next card starts sliding in 1.0s after silence begins (1.2s before narration)
                card_start = current_time + (PAUSE_DURATION - CARD_PRE_DELAY)
                story_offsets.append(card_start)
                
                current_time += PAUSE_DURATION
                
                clips.append(story_clip)
                current_time += duration

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

    if not confirm("¿Continuar con la mezcla de audio?"):
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

    if not confirm("¿Continuar con la creación del video?"):
        ui.info("Proceso terminado.")
        return

    # ── Elegir tipo de fondo ────────────────────────────────────────────────
    story_id  = historias[0]["id"]
    use_scenes = False

    if args.scenes is not None:
        use_scenes = args.scenes
    elif OPENAI_API_KEY:
        ui.info("\n¿Qué fondo quieres usar?")
        print()
        print("  [1] Video de fondo clásico")
        print("  [2] Escenas AI generadas (gpt-image-1 + Ken Burns)")
        bg_choice = input("\nElige [1/2]: ").strip()
        use_scenes = (bg_choice == "2")
    else:
        ui.warn("OPENAI_API_KEY no encontrada — usando video de fondo clásico.")

    # ── Opción A: escenas AI ────────────────────────────────────────────────
    if use_scenes:
        from scripts.scene_generator import generate_scenes
        from scripts.scene_video import build_scene_clip

        # 1. Necesitamos el SRT primero para poder analizar la historia
        ui.info("\nGenerando subtítulos (necesarios para el análisis de escenas)...")
        if args.words_per_card is not None:
            words_per_card = args.words_per_card
        else:
            words_per_card = ask_int("¿Palabras por tarjeta de subtítulo?", 6)
        is_vertical = VIDEO_WIDTH < VIDEO_HEIGHT
        srt_path = generate_srt(audio_path, words_per_card=words_per_card, is_vertical=is_vertical)
        subs_sub_dir = SUBS_DIR / subreddit
        subs_sub_dir.mkdir(parents=True, exist_ok=True)
        srt_new_path = subs_sub_dir / srt_path.name
        srt_path.rename(srt_new_path)
        srt_path = srt_new_path

        # 2. Generar imágenes de escenas
        ui.info("\nGenerando imágenes de escenas con GPT-4o + gpt-image-1...")
        scenes_dir = generate_scenes(story_id)
        if not scenes_dir:
            ui.error("Falló la generación de escenas. Saliendo.")
            return

        # 3. Construir clip de escenas en memoria (sin render intermedio)
        ui.info("\nConstruyendo clip de escenas (Ken Burns + dissolve)...")
        scene_clip = build_scene_clip(story_id)
        if not scene_clip:
            ui.error("Falló la construcción del clip de escenas. Saliendo.")
            return

        background = scene_clip   # VideoClip — create_video() lo acepta directamente
        start_sec  = 0

        if args.subs is not None:
            add_subs = args.subs
        else:
            add_subs = ask("¿Agregar subtítulos al video?")
        if not add_subs:
            srt_path = None

    # ── Opción B: video clásico ─────────────────────────────────────────────
    else:
        if args.start_sec is not None:
            start_sec = args.start_sec
        else:
            start_sec = ask_int("¿Desde qué segundo del video de fondo empezar?", 0)

        if args.subs is not None:
            add_subs = args.subs
        else:
            add_subs = ask("¿Agregar subtítulos al video?")
        srt_path = None
        if add_subs:
            if args.words_per_card is not None:
                words_per_card = args.words_per_card
            else:
                words_per_card = ask_int("¿Palabras por tarjeta de subtítulo?", 3)
            is_vertical = VIDEO_WIDTH < VIDEO_HEIGHT
            srt_path = generate_srt(audio_path, words_per_card=words_per_card, is_vertical=is_vertical)
            subs_sub_dir = SUBS_DIR / subreddit
            subs_sub_dir.mkdir(parents=True, exist_ok=True)
            srt_new_path = subs_sub_dir / srt_path.name
            srt_path.rename(srt_new_path)
            srt_path = srt_new_path

        background = BACKGROUND_VIDEO

    # ── Dark mode ───────────────────────────────────────────────────────────
    if args.dark_mode is not None:
        dark_mode = args.dark_mode
    else:
        dark_mode = ask("¿Usar la tarjeta de Reddit en modo oscuro (dark mode)?")

    # ── Render final ────────────────────────────────────────────────────────
    video_path = create_video(
        mixed_path,
        background,
        subreddit,
        start_second=start_sec,
        srt_path=srt_path,
        story_id=story_id,
        historias=historias,
        story_offsets=story_offsets,
        dark_mode=dark_mode,
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