#!/usr/bin/env python3
"""
scene_generator.py — Genera imágenes de escenas para una historia a partir de su .srt.

Workflow (basado en guide.md):
  1. Leer el .srt y extraer el texto completo de la historia.
  2. Llamar a GPT-4 para crear el desglose en escenas (3-5 max), con timings e image prompts.
  3. Para cada escena, llamar a gpt-image-1 / DALL-E 3 para generar la imagen.
  4. Guardar imágenes en: outputs/scenes/<story_id>/scene_01.png, scene_02.png, ...
  5. Guardar el plan completo en: outputs/scenes/<story_id>/scenes.json

Uso:
    python scripts/scene_generator.py <story_id>
    python scripts/scene_generator.py 1u4xa2r
    python scripts/scene_generator.py 1u4xa2r --model gpt-image-1
    python scripts/scene_generator.py 1u4xa2r --model dall-e-3
"""
import sys
import json
import time
import re
import argparse
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OPENAI_API_KEY, SUBS_DIR, SCENES_DIR
from scripts import termui as ui

# ── Visual style from guide.md ─────────────────────────────────────────────
VISUAL_STYLE = """Dark papercraft horror world. Handcrafted paper-diorama environment made from folded paper, layered cardstock, and origami-like structures. Stylized but believable proportions. Clean geometric shapes. Slightly rough paper edges. Visible paper folds and layered construction. Soft cinematic lighting. Dark color palette with muted blues, greys, browns, and desaturated warm lights. Atmospheric fog. Subtle volumetric lighting. Cozy yet unsettling mood. Horror storybook aesthetic. Looks like a handcrafted miniature world built entirely from paper. Not realistic. Not cartoonish. Not anime. Not claymation. Not low-poly. High visual consistency. Professional animated short film quality. 12 FPS animation style with subtle stop-motion feel. Gentle camera movement implied. Paper textures remain visible. Vertical 9:16 composition. Designed for horror storytelling and mystery narrations. The scene should feel like a dark memory reconstructed inside a handmade paper world. Resolution 1080x1920."""

# ── System prompt for GPT ───────────────────────────────────────────────────
SCENE_ANALYSIS_SYSTEM = """You are a visual storytelling director specializing in horror short-form video content.

Given the full text of a horror story, your task is to:
1. Read and understand the complete narrative arc.
2. Divide the story into 3 to 5 scenes maximum (only add more if absolutely necessary).
3. Each scene must represent a major narrative change (beginning, escalation, climax, aftermath).
4. Provide exact second-level timing for each scene covering the full story duration with no gaps.
5. Write a cinematic image prompt for each scene focused purely on what is VISIBLE.

Return ONLY a valid JSON object in this exact format:
{
  "scenes": [
    {
      "scene_number": 1,
      "time_start": 0,
      "time_end": 12,
      "narrative_beat": "Normal situation",
      "description": "Brief cinematic description of what is happening, the emotional tone, camera angle, and key visual elements.",
      "image_prompt": "Detailed visual prompt focusing only on what should be seen in the image. No plot explanation."
    }
  ]
}

Rules:
- time_start and time_end are whole integers in seconds.
- time_start of scene N+1 must equal time_end of scene N.
- First scene always starts at 0.
- Last scene must end at the total duration provided.
- Maximum 5 scenes. Prefer 3-4.
- image_prompt must be purely visual, no narration.
- Do NOT include the visual style reference in image_prompt — it will be appended automatically."""


def find_subreddit_for_id(story_id: str) -> str | None:
    """Busca el subreddit que contiene el story_id recorriendo SUBS_DIR."""
    for sub_dir in SUBS_DIR.iterdir():
        if not sub_dir.is_dir():
            continue
        for f in sub_dir.glob(f"*_{story_id}.srt"):
            return sub_dir.name
    return None


def parse_srt_to_text(srt_path: Path) -> tuple[str, float]:
    """
    Lee un archivo .srt y devuelve:
    - El texto completo de la historia (sin timestamps ni números).
    - La duración total en segundos (basada en el último timestamp end).
    """
    content = srt_path.read_text(encoding="utf-8")
    
    # Extract last timestamp to get total duration
    timestamps = re.findall(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", content)
    total_duration = 0.0
    if timestamps:
        last_end = timestamps[-1][1]  # last "end" timestamp
        h, m, rest = last_end.split(":")
        s, ms = rest.split(",")
        total_duration = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    # Strip SRT formatting: remove block numbers, timestamps, keep only text
    lines = content.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", line):
            continue
        text_lines.append(line)

    full_text = " ".join(text_lines)
    # Clean up extra spaces
    full_text = re.sub(r"\s+", " ", full_text).strip()
    
    return full_text, total_duration


def analyze_story_with_gpt(story_text: str, total_duration: float) -> list[dict] | None:
    """
    Llama a GPT-4o para generar el desglose de escenas.
    Devuelve la lista de escenas en formato dict.
    """
    ui.info("Analizando la historia con GPT-4o...")
    
    user_message = f"""Story text (total duration: {int(total_duration)} seconds):

{story_text}

Divide this horror story into 3-5 scenes. The last scene must end exactly at second {int(total_duration)}."""

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SCENE_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        if resp.status_code != 200:
            ui.error(f"GPT API error ({resp.status_code}): {resp.text[:300]}")
            return None

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        scenes = parsed.get("scenes", [])
        ui.success(f"Plan generado: {len(scenes)} escenas")
        return scenes

    except Exception as e:
        ui.error(f"Error al llamar a GPT: {e}")
        return None


def generate_image(prompt: str, scene_num: int, model: str = "gpt-image-1") -> bytes | None:
    """
    Genera una imagen con la API de OpenAI.
    Soporta 'gpt-image-1' (nuevo) y 'dall-e-3'.
    Devuelve los bytes de la imagen PNG.
    """
    full_prompt = f"{prompt}\n\nVISUAL STYLE: {VISUAL_STYLE}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    if model == "gpt-image-1":
        payload = {
            "model": "gpt-image-1",
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1536",   # Closest to 9:16 for gpt-image-1
            "quality": "high",
            "output_format": "png",
        }
        endpoint = "https://api.openai.com/v1/images/generations"
    else:  # dall-e-3
        payload = {
            "model": "dall-e-3",
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1792",   # 9:16 for dall-e-3
            "quality": "hd",
        }
        endpoint = "https://api.openai.com/v1/images/generations"

    try:
        ui.info(f"  Generando imagen con {model}...")
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=120)

        if resp.status_code != 200:
            ui.error(f"  Image API error ({resp.status_code}): {resp.text[:300]}")
            return None

        data = resp.json()
        image_data = data["data"][0]

        # gpt-image-1 may return b64_json; dall-e-3 returns url
        if "b64_json" in image_data and image_data["b64_json"]:
            import base64
            return base64.b64decode(image_data["b64_json"])
        elif "url" in image_data and image_data["url"]:
            img_resp = requests.get(image_data["url"], timeout=60)
            return img_resp.content
        else:
            ui.error("  No se encontró imagen en la respuesta.")
            return None

    except Exception as e:
        ui.error(f"  Error generando imagen: {e}")
        return None


def generate_scenes(story_id: str, model: str = "gpt-image-1") -> Path | None:
    """
    Orquesta todo el proceso:
    1. Busca el .srt del story_id
    2. Analiza la historia con GPT
    3. Genera una imagen por escena
    4. Guarda todo en outputs/scenes/<story_id>/

    Devuelve la carpeta de salida si tuvo éxito.
    """
    if not OPENAI_API_KEY:
        ui.error("OPENAI_API_KEY no encontrada en el .env")
        return None

    # 1. Encontrar el subreddit y el .srt
    ui.info(f"Buscando archivos para story_id: {story_id}...")
    subreddit = find_subreddit_for_id(story_id)
    if not subreddit:
        ui.error(f"No se encontró .srt para el id '{story_id}' en {SUBS_DIR}")
        return None

    srt_path = SUBS_DIR / subreddit / f"{subreddit}_{story_id}.srt"
    ui.success(f"SRT: {srt_path}")

    # 2. Parsear el SRT
    story_text, total_duration = parse_srt_to_text(srt_path)
    ui.info(f"Duración total: {total_duration:.1f}s | Caracteres: {len(story_text)}")

    # 3. Analizar la historia con GPT
    scenes = analyze_story_with_gpt(story_text, total_duration)
    if not scenes:
        return None

    # 4. Preparar carpeta de salida
    out_dir = SCENES_DIR / story_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 5. Guardar el plan de escenas como JSON
    scenes_json_path = out_dir / "scenes.json"
    with open(scenes_json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "story_id": story_id,
                "subreddit": subreddit,
                "total_duration": total_duration,
                "model": model,
                "scenes": scenes,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    ui.success(f"Plan guardado: {scenes_json_path}")

    # 6. Generar imágenes escena por escena
    ui.info(f"\nGenerando {len(scenes)} imágenes con {model}...")
    print()

    failed = []
    for scene in scenes:
        n = scene["scene_number"]
        t_start = scene["time_start"]
        t_end = scene["time_end"]
        prompt = scene["image_prompt"]
        beat = scene.get("narrative_beat", "")

        ui.info(f"Escena {n}/{len(scenes)}: [{t_start}s - {t_end}s] {beat}")

        img_bytes = generate_image(prompt, n, model=model)

        if img_bytes:
            img_path = out_dir / f"scene_{n:02d}.png"
            img_path.write_bytes(img_bytes)
            ui.success(f"  Guardada: {img_path.name} ({len(img_bytes) // 1024} KB)")
        else:
            ui.warn(f"  Falló la imagen de escena {n}. Continuando...")
            failed.append(n)

        # Pausa entre generaciones para evitar rate limits
        if n < len(scenes):
            time.sleep(2)

    print()
    if failed:
        ui.warn(f"Escenas que fallaron: {failed}")
    else:
        ui.success(f"Todas las imágenes generadas correctamente en: {out_dir}")

    return out_dir


# ── CLI ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Genera imágenes de escenas para una historia a partir de su .srt."
    )
    parser.add_argument("story_id", help="ID de la historia (ej: 1u4xa2r)")
    parser.add_argument(
        "--model",
        choices=["dall-e-3", "gpt-image-1"],
        default="gpt-image-1",
        help="Modelo de imágenes a usar (default: dall-e-3)",
    )
    args = parser.parse_args()

    result = generate_scenes(args.story_id, model=args.model)
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
