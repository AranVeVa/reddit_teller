#!/usr/bin/env python3
"""
pipeline.py — Funciones programáticas puras para cada paso del pipeline de reddit_teller.
Diseñado para ser consumido por la API local o por main.py (sin pedir input()).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from config import (
    STORIES_DIR, AUDIOS_DIR, MIXED_DIR, SUBS_DIR, SCENES_DIR, VIDEOS_DIR,
    BACKGROUND_AUDIO, BACKGROUND_VIDEO, VIDEO_WIDTH, VIDEO_HEIGHT
)
from scripts.reddit import obtener_historias, _save_used_id, guardar_historias
from scripts.voice import archivo_a_audio
from scripts.audio_mixer import mix_audio
from scripts.subtitles import generate_srt
from scripts.scene_generator import generate_scenes, plan_scenes, render_scene_images, regenerate_single_scene, find_subreddit_for_id
from scripts.scene_video import build_scene_clip
from scripts.video import create_video
from scripts import termui as ui


def step_search_stories(
    subreddit: str,
    limit: int = 10,
    min_chars: int = 300,
    max_chars: int = 1500,
    orden: str = "hot"
) -> list[dict]:
    """Obtiene candidatos de Reddit que cumplen filtros."""
    ui.info(f"Buscando historias en r/{subreddit} (orden: {orden}, min: {min_chars}c, max: {max_chars}c)...")
    candidatos = obtener_historias(
        subreddit=subreddit,
        limite=max(50, limit * 10),
        min_chars=min_chars,
        max_chars=max_chars,
        orden=orden,
    )
    return candidatos[:limit]


def step_reject_story(post_id: str, title: str = "", subreddit: str = "", is_vertical: bool = True) -> None:
    """Marca un ID como usado/rechazado."""
    _save_used_id(post_id, title=title, subreddit=subreddit, is_vertical=is_vertical)
    ui.warn(f"Historia {post_id} rechazada y registrada en used_ids.txt")


def step_save_accepted_stories(historias: list[dict], subreddit: str, is_vertical: bool = True) -> dict:
    """Guarda individualmente y en conjunto las historias aceptadas/editadas."""
    sub_dir = STORIES_DIR / subreddit
    sub_dir.mkdir(parents=True, exist_ok=True)

    for h in historias:
        fpath = sub_dir / f"{subreddit}_{h['id']}.txt"
        fpath.write_text(f"{h['title']}\n\n{h['content']}\n", encoding="utf-8")

    combined_file = guardar_historias(historias, subreddit, is_vertical=is_vertical)
    return {
        "subreddit": subreddit,
        "combined_file": str(combined_file),
        "story_ids": [h["id"] for h in historias],
        "count": len(historias),
    }


def step_generate_voice(historias: list[dict], subreddit: str) -> dict:
    """
    Sintetiza la narración de cada historia con ElevenLabs, concatena audios con pausas
    y calcula story_offsets.
    """
    from moviepy import AudioFileClip
    from moviepy.audio.AudioClip import concatenate_audioclips

    story_audios = []
    story_durations = []
    sub_story_dir = STORIES_DIR / subreddit
    sub_story_dir.mkdir(parents=True, exist_ok=True)

    for idx, h in enumerate(historias, 1):
        ui.info(f"Generando voz ElevenLabs ({idx}/{len(historias)}): {h['title']}...")
        temp_txt = sub_story_dir / f"temp_{h['id']}.txt"
        temp_txt.write_text(f"{h['title']}\n{h['content']}\n", encoding="utf-8")

        audio_file = archivo_a_audio(temp_txt)
        temp_txt.unlink(missing_ok=True)

        if not audio_file or not audio_file.exists():
            raise RuntimeError(f"Fallo al generar voz para historia {h['id']}")

        story_audios.append(audio_file)
        clip = AudioFileClip(str(audio_file))
        story_durations.append(clip.duration)
        clip.close()

    PAUSE_DURATION = 2.2
    CARD_PRE_DELAY = 1.2
    clips = []
    story_offsets = []
    current_time = 0.0

    # Crear tono de silencio si no existe
    silence_path = AUDIOS_DIR / f"silence_{PAUSE_DURATION}.mp3"
    if not silence_path.exists():
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(PAUSE_DURATION), str(silence_path)
        ]
        subprocess.run(cmd, capture_output=True)

    for idx, (path, duration) in enumerate(zip(story_audios, story_durations)):
        story_clip = AudioFileClip(str(path))
        if idx == 0:
            story_offsets.append(0.0)
            clips.append(story_clip)
            current_time += duration
        else:
            silent_clip = AudioFileClip(str(silence_path))
            clips.append(silent_clip)
            card_start = current_time + (PAUSE_DURATION - CARD_PRE_DELAY)
            story_offsets.append(card_start)
            current_time += PAUSE_DURATION
            clips.append(story_clip)
            current_time += duration

    final_audio = concatenate_audioclips(clips)
    first_id = historias[0]["id"]
    combined_name = f"{subreddit}_{first_id}.mp3"

    audio_sub_dir = AUDIOS_DIR / subreddit
    audio_sub_dir.mkdir(parents=True, exist_ok=True)
    out_audio_path = audio_sub_dir / combined_name

    final_audio.write_audiofile(str(out_audio_path), bitrate="320k", logger=None)

    for c in clips:
        c.close()
    final_audio.close()

    for p in story_audios:
        p.unlink(missing_ok=True)

    ui.success(f"Audio narrado guardado en: {out_audio_path}")
    return {
        "audio_path": str(out_audio_path),
        "duration": current_time,
        "story_offsets": story_offsets,
    }


def step_mix_audio(narration_path: str, background_path: str = None) -> str:
    """Mezcla narración de voz con pista ambiental."""
    narr_path = Path(narration_path)
    bg_path = Path(background_path) if background_path else BACKGROUND_AUDIO

    ui.info("Mezclando narración con audio ambiental...")
    mixed_file = mix_audio(narr_path, bg_path)
    if not mixed_file or not mixed_file.exists():
        raise RuntimeError("Fallo al mezclar audio")

    subreddit = narr_path.parent.name if narr_path.parent != AUDIOS_DIR else "mixed"
    mixed_sub_dir = MIXED_DIR / subreddit
    mixed_sub_dir.mkdir(parents=True, exist_ok=True)

    dest_path = mixed_sub_dir / mixed_file.name
    if mixed_file != dest_path:
        mixed_file.rename(dest_path)

    ui.success(f"Audio mezclado guardado en: {dest_path}")
    return str(dest_path)


def step_generate_subtitles(
    audio_path: str,
    words_per_card: int = 3,
    is_vertical: bool = True,
    language: str = None
) -> str:
    """Genera subtítulos .srt con Whisper."""
    aud_path = Path(audio_path)
    srt_path = generate_srt(aud_path, words_per_card=words_per_card, is_vertical=is_vertical, language=language)

    subreddit = aud_path.parent.name
    subs_sub_dir = SUBS_DIR / subreddit
    subs_sub_dir.mkdir(parents=True, exist_ok=True)

    dest_srt = subs_sub_dir / srt_path.name
    if srt_path != dest_srt:
        srt_path.rename(dest_srt)

    ui.success(f"Subtítulos SRT guardados en: {dest_srt}")
    return str(dest_srt)


def step_plan_scenes(story_id: str, model: str = "gpt-image-1") -> dict:
    """Crea el desglose de escenas (scenes.json) con GPT-4o sin generar aún las imágenes."""
    return plan_scenes(story_id, model=model)


def step_render_scenes(story_id: str, model: str = "gpt-image-1") -> str:
    """Genera las imágenes PNG descritas en scenes.json."""
    out_dir = render_scene_images(story_id, model=model)
    if not out_dir:
        raise RuntimeError("Fallo al generar imágenes de escenas")
    return str(out_dir)


def step_regenerate_scene(story_id: str, scene_number: int, prompt: str = None, model: str = "gpt-image-1") -> str:
    """Regenera una sola escena."""
    img_path = regenerate_single_scene(story_id, scene_number, prompt=prompt, model=model)
    if not img_path:
        raise RuntimeError(f"Fallo al regenerar escena {scene_number}")
    return str(img_path)


def step_render_video(
    mixed_audio_path: str,
    subreddit: str,
    story_id: str,
    historias: list[dict],
    story_offsets: list[float],
    use_scenes: bool = False,
    background_video_path: str = None,
    start_second: int = 0,
    srt_path: str = None,
    dark_mode: bool = False,
) -> str:
    """Ensambla el video final con MoviePy."""
    mixed_path = Path(mixed_audio_path)
    srt_p = Path(srt_path) if srt_path else None

    if use_scenes:
        ui.info("Construyendo composición de escenas IA (Ken Burns + Dissolve)...")
        bg_clip = build_scene_clip(story_id)
        if not bg_clip:
            raise RuntimeError("Fallo al construir clip de escenas IA")
        background = bg_clip
        start_sec = 0
    else:
        background = Path(background_video_path) if background_video_path else BACKGROUND_VIDEO
        start_sec = start_second

    out_video_path = create_video(
        audio_path=mixed_path,
        background_video=background,
        output_name=subreddit,
        start_second=start_sec,
        srt_path=srt_p,
        story_id=story_id,
        historias=historias,
        story_offsets=story_offsets,
        dark_mode=dark_mode,
    )

    if not out_video_path or not out_video_path.exists():
        raise RuntimeError("Fallo al crear video final")

    ui.success(f"Video final renderizado con éxito en: {out_video_path}")
    return str(out_video_path)
