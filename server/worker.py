#!/usr/bin/env python3
"""
worker.py — Subproceso aislado para ejecutar cada paso del pipeline.
Permite relectura limpia de .env, aislamiento de dependencias pesadas y emisión SSE en vivo.
"""
import sys
import os
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

# Habilitar emisión de eventos JSON en termui
os.environ["RT_EVENTS"] = "1"

from config import AUDIOS_DIR, MIXED_DIR, SUBS_DIR, SCENES_DIR
from server.projects import get_project, save_project
from scripts import pipeline
from scripts import termui as ui


def run_worker_step(project_id: str, step_name: str, args_data: dict):
    ui.info(f"Worker iniciado para proyecto {project_id} - paso '{step_name}'")
    project = get_project(project_id)
    if not project:
        ui.error(f"Proyecto {project_id} no existe")
        sys.exit(1)

    try:
        if step_name == "search_stories":
            sub = args_data.get("subreddit") or project["subreddit"]
            lim = args_data.get("limit", project.get("limit", 1))
            min_c = args_data.get("min_chars", project.get("min_chars", 300))
            max_c = args_data.get("max_chars", project.get("max_chars", 1500))
            order = args_data.get("order", project.get("order", "hot"))

            candidates = pipeline.step_search_stories(
                subreddit=sub, limit=lim, min_chars=min_c, max_chars=max_c, orden=order
            )
            project["subreddit"] = sub
            project["limit"] = lim
            project["order"] = order
            project["candidates"] = candidates
            project["current_step"] = 2
            save_project(project)
            ui.success(f"Encontradas {len(candidates)} historias candidatas")

        elif step_name == "accept_stories":
            accepted = args_data.get("accepted_stories", [])
            sub = project["subreddit"]
            res = pipeline.step_save_accepted_stories(accepted, sub, is_vertical=True)
            project["accepted_stories"] = accepted
            project["current_step"] = 3
            save_project(project)
            ui.success(f"{len(accepted)} historias aceptadas y guardadas")

        elif step_name == "generate_voice":
            accepted = project["accepted_stories"]
            sub = project["subreddit"]
            voice_res = pipeline.step_generate_voice(accepted, sub)
            project["voice_result"] = voice_res
            project["current_step"] = 4
            save_project(project)
            ui.success("Narración de voz completada con éxito")

        elif step_name == "mix_audio":
            voice_res = project.get("voice_result")
            narr_path = None
            if voice_res and isinstance(voice_res, dict) and voice_res.get("audio_path"):
                narr_path = voice_res["audio_path"]
            else:
                sub = project["subreddit"]
                accepted = project.get("accepted_stories", [])
                if accepted:
                    story_id = accepted[0]["id"]
                    possible_aud = AUDIOS_DIR / sub / f"{sub}_{story_id}.mp3"
                    if possible_aud.exists():
                        narr_path = str(possible_aud)

            if not narr_path or not Path(narr_path).exists():
                raise RuntimeError("No se encontró narración de voz. Por favor ejecuta el paso de Voz primero.")

            bg_path = args_data.get("background_audio_path")
            mixed_path = pipeline.step_mix_audio(narr_path, bg_path)
            project["mixed_result"] = {"mixed_audio_path": mixed_path}
            project["current_step"] = 5
            save_project(project)
            ui.success("Mezcla de audio completada")

        elif step_name == "generate_subtitles":
            voice_res = project.get("voice_result")
            mixed_res = project.get("mixed_result")
            narr_path = None
            if voice_res and isinstance(voice_res, dict) and voice_res.get("audio_path"):
                narr_path = voice_res["audio_path"]
            elif mixed_res and isinstance(mixed_res, dict) and mixed_res.get("mixed_audio_path"):
                narr_path = mixed_res["mixed_audio_path"]
            else:
                sub = project["subreddit"]
                accepted = project.get("accepted_stories", [])
                if accepted:
                    story_id = accepted[0]["id"]
                    possible_aud = AUDIOS_DIR / sub / f"{sub}_{story_id}.mp3"
                    if possible_aud.exists():
                        narr_path = str(possible_aud)

            if not narr_path or not Path(narr_path).exists():
                raise RuntimeError("No se encontró audio para subtitular. Genera la voz primero.")

            w_per_card = args_data.get("words_per_card", project.get("words_per_card", 3))
            lang = args_data.get("language", project.get("language"))

            srt_path = pipeline.step_generate_subtitles(
                narr_path, words_per_card=w_per_card, is_vertical=True, language=lang
            )
            project["subtitles_result"] = {"srt_path": srt_path}
            project["words_per_card"] = w_per_card
            project["language"] = lang
            project["current_step"] = 6
            save_project(project)
            ui.success("Subtítulos generados")

        elif step_name == "plan_scenes":
            accepted = project.get("accepted_stories", [])
            if not accepted:
                raise RuntimeError("No hay historias aceptadas en el proyecto")
            story_id = accepted[0]["id"]
            model = args_data.get("model", "gpt-image-1")
            plan_data = pipeline.step_plan_scenes(story_id, model=model)
            project["scenes_plan"] = plan_data
            save_project(project)
            ui.success("Plan de escenas generado")

        elif step_name == "render_scenes":
            accepted = project.get("accepted_stories", [])
            if not accepted:
                raise RuntimeError("No hay historias aceptadas en el proyecto")
            story_id = accepted[0]["id"]
            model = args_data.get("model", "gpt-image-1")
            out_dir = pipeline.step_render_scenes(story_id, model=model)
            project["scenes_rendered"] = True
            project["current_step"] = 7
            save_project(project)
            ui.success("Imágenes de escenas renderizadas")

        elif step_name == "regenerate_scene":
            accepted = project.get("accepted_stories", [])
            if not accepted:
                raise RuntimeError("No hay historias aceptadas en el proyecto")
            story_id = accepted[0]["id"]
            scene_num = args_data.get("scene_number")
            prompt = args_data.get("prompt")
            model = args_data.get("model", "gpt-image-1")
            pipeline.step_regenerate_scene(story_id, scene_num, prompt=prompt, model=model)
            ui.success(f"Escena {scene_num} regenerada")

        elif step_name == "render_video":
            sub = project["subreddit"]
            accepted = project.get("accepted_stories", [])
            if not accepted:
                raise RuntimeError("No hay historias aceptadas en el proyecto")
            story_id = accepted[0]["id"]

            # Safe audio retrieval
            mixed_res = project.get("mixed_result")
            voice_res = project.get("voice_result")

            mixed_path = None
            if mixed_res and isinstance(mixed_res, dict) and mixed_res.get("mixed_audio_path"):
                mixed_path = mixed_res["mixed_audio_path"]
            elif voice_res and isinstance(voice_res, dict) and voice_res.get("audio_path"):
                mixed_path = voice_res["audio_path"]
            else:
                # Check on disk
                possible_mixed = [
                    MIXED_DIR / sub / f"mixed_{sub}_{story_id}.mp3",
                    MIXED_DIR / sub / f"{sub}_{story_id}.mp3",
                    AUDIOS_DIR / sub / f"{sub}_{story_id}.mp3",
                ]
                for p in possible_mixed:
                    if p.exists():
                        mixed_path = str(p)
                        break

            if not mixed_path or not Path(mixed_path).exists():
                raise RuntimeError(
                    f"No se encontró archivo de audio para r/{sub} ({story_id}). Por favor ejecuta el Paso 4 (Voz & Mezcla) primero."
                )

            offsets = voice_res.get("story_offsets") if (voice_res and isinstance(voice_res, dict)) else [0.0]
            if not offsets:
                offsets = [0.0]

            use_scenes = args_data.get("use_scenes", project.get("background_type") == "scenes")

            # Check if scenes exist if use_scenes is True
            if use_scenes:
                scenes_dir = SCENES_DIR / sub / story_id
                scenes_json = scenes_dir / "scenes.json"
                if not scenes_json.exists():
                    ui.warn("No existía plan de escenas. Generando plan e imágenes ahora...")
                    pipeline.step_plan_scenes(story_id, model="gpt-image-1")
                    pipeline.step_render_scenes(story_id, model="gpt-image-1")

            bg_vid = args_data.get("background_video_path") or project.get("background_video_path")
            start_sec = args_data.get("start_second", 0)
            subs_res = project.get("subtitles_result")
            srt_path = subs_res.get("srt_path") if (subs_res and isinstance(subs_res, dict)) else None
            dark = args_data.get("dark_mode", project.get("dark_mode", True))

            video_path = pipeline.step_render_video(
                mixed_audio_path=mixed_path,
                subreddit=sub,
                story_id=story_id,
                historias=accepted,
                story_offsets=offsets,
                use_scenes=use_scenes,
                background_video_path=bg_vid,
                start_second=start_sec,
                srt_path=srt_path,
                dark_mode=dark,
            )
            project["final_video_path"] = video_path
            project["current_step"] = 7
            save_project(project)
            ui.success(f"Video final listo: {video_path}")

        else:
            raise ValueError(f"Paso desconocido: {step_name}")

    except Exception as e:
        ui.error(f"Error en paso '{step_name}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("step_name")
    parser.add_argument("--args", default="{}")
    args = parser.parse_args()

    args_data = json.loads(args.args)
    run_worker_step(args.project_id, args.step_name, args_data)


if __name__ == "__main__":
    main()
