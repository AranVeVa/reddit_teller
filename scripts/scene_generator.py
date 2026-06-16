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
2. Create a VISUAL BIBLE: define the world, environment, key locations, and characters that appear in the story. This visual bible will be prepended to EVERY image prompt to ensure absolute visual consistency across all scenes.
3. Decide how many scenes are appropriate for the story duration. Use this guideline:
   - Under 30 seconds: 2 scenes
   - 30-60 seconds: 3 scenes
   - 60-90 seconds: 4 scenes
   - 90-150 seconds: 5-6 scenes
   - Over 150 seconds: 6-8 scenes
   You may adjust slightly based on narrative beats, but respect the approximate ratio.
4. Each scene must represent a major narrative change (beginning, escalation, climax, aftermath).
5. Provide exact second-level timing for each scene covering the full story duration with no gaps.
6. Write a cinematic image prompt for each scene focused purely on what is VISIBLE.

Return ONLY a valid JSON object in this exact format:
{
  "visual_bible": "Detailed description of the world/environment, recurring locations (architecture, colors, textures, lighting), and each character (appearance, clothing, distinguishing features, approximate age). This must be specific enough that a different artist could recreate the same world and characters consistently. Example: 'Setting: A cramped one-bedroom apartment in a Soviet-era concrete block. Yellowed wallpaper peeling at the corners. A single bare bulb hanging from the ceiling. Character: ANNA — mid-30s woman, pale skin, dark circles under her eyes, long black hair always tied in a loose braid, wearing a faded blue nightgown.'",
  "scenes": [
    {
      "scene_number": 1,
      "time_start": 0,
      "time_end": 12,
      "narrative_beat": "Normal situation",
      "description": "Brief cinematic description of what is happening, the emotional tone, camera angle, and key visual elements.",
      "image_prompt": "Detailed visual prompt focusing only on what should be seen in THIS SPECIFIC scene. Do NOT repeat the visual bible here — it will be prepended automatically. Focus on action, composition, camera angle, lighting changes, and emotional tone unique to this moment."
    }
  ]
}

Rules:
- visual_bible is REQUIRED and must be detailed enough for visual consistency.
- time_start and time_end are whole integers in seconds.
- time_start of scene N+1 must equal time_end of scene N.
- First scene always starts at 0.
- Last scene must end at the total duration provided.
- The number of scenes must match the duration guideline above.
- image_prompt must be purely visual, no narration.
- image_prompt should NOT repeat environment/character descriptions from visual_bible.
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


def analyze_story_with_gpt(story_text: str, total_duration: float) -> tuple[list, str] | None:
    """
    Llama a GPT-4o para generar el desglose de escenas.
    Devuelve la lista de escenas en formato dict.
    """
    ui.info("Analizando la historia con GPT-4o...")

    # Calcular escenas sugeridas basado en la duración
    if total_duration < 30:
        suggested = 2
    elif total_duration < 60:
        suggested = 3
    elif total_duration < 90:
        suggested = 4
    elif total_duration < 150:
        suggested = 5
    else:
        suggested = min(8, max(6, int(total_duration / 25)))

    ui.info(f"Duración: {int(total_duration)}s → sugiriendo ~{suggested} escenas")
    
    user_message = f"""Story text (total duration: {int(total_duration)} seconds):

{story_text}

Based on the duration ({int(total_duration)} seconds), create approximately {suggested} scenes. The last scene must end exactly at second {int(total_duration)}. Remember to include the visual_bible field with detailed descriptions of the world and characters."""

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
        visual_bible = parsed.get("visual_bible", "")
        if visual_bible:
            ui.success(f"Visual Bible generada ({len(visual_bible)} chars)")
        else:
            ui.warn("No se generó visual bible — la consistencia visual puede variar.")
        ui.success(f"Plan generado: {len(scenes)} escenas")
        return scenes, visual_bible

    except Exception as e:
        ui.error(f"Error al llamar a GPT: {e}")
        return None


def generate_image(prompt: str, scene_num: int, model: str = "gpt-image-1", visual_bible: str = "") -> tuple[bytes | None, str | None]:
    """
    Genera una imagen con la API de OpenAI.
    Soporta 'gpt-image-1' (nuevo) y 'dall-e-3'.
    Devuelve (bytes, None) si tiene éxito, o (None, error_message) si falla.
    """
    # Construir prompt completo: visual bible + prompt de escena + estilo visual
    parts = []
    if visual_bible:
        parts.append(f"VISUAL BIBLE (maintain these designs consistently):\n{visual_bible}")
    parts.append(f"SCENE:\n{prompt}")
    parts.append(f"VISUAL STYLE: {VISUAL_STYLE}")
    full_prompt = "\n\n".join(parts)

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
            error_msg = resp.text
            ui.error(f"  Image API error ({resp.status_code}): {error_msg[:300]}")
            return None, error_msg

        data = resp.json()
        image_data = data["data"][0]

        # gpt-image-1 may return b64_json; dall-e-3 returns url
        if "b64_json" in image_data and image_data["b64_json"]:
            import base64
            return base64.b64decode(image_data["b64_json"]), None
        elif "url" in image_data and image_data["url"]:
            img_resp = requests.get(image_data["url"], timeout=60)
            return img_resp.content, None
        else:
            ui.error("  No se encontró imagen en la respuesta.")
            return None, "No image found in response data"

    except Exception as e:
        ui.error(f"  Error generando imagen: {e}")
        return None, str(e)


def rewrite_prompt_for_safety(original_prompt: str, error_message: str) -> str | None:
    """
    Pide a GPT-4o que reescriba un prompt que fue rechazado por el sistema de seguridad
    de OpenAI para que cumpla con las políticas de contenido sin perder la atmósfera de terror.
    """
    ui.warn("  [Sistema de Seguridad] El prompt fue rechazado. Pidiendo a GPT-4o que lo suavice/sanitice...")
    
    system_prompt = (
        "You are an expert prompt engineer. An image generation prompt was rejected by OpenAI's safety system. "
        "Your task is to rewrite the prompt so that it is 100% compliant with OpenAI's safety guidelines "
        "(absolutely avoiding words related to blood, gore, nudity, violence, body parts, or anything that "
        "could trigger filters) while keeping the same dark, spooky, and unsettling papercraft horror atmosphere. "
        "Focus on metaphors, dark shadows, stylized representations, and moody lighting rather than explicit scary figures. "
        "Return ONLY the rewritten prompt as plain text, with no introduction, quotes, or formatting."
    )
    
    user_message = (
        f"Original Prompt: {original_prompt}\n\n"
        f"Safety System Error Message: {error_message}\n\n"
        f"Rewrite it to be safe, clean, and guidelines-compliant."
    )
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.5,
            },
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200:
            new_prompt = resp.json()["choices"][0]["message"]["content"].strip()
            ui.success(f"  [Reescrito] Nuevo prompt sugerido: {new_prompt}")
            return new_prompt
        else:
            ui.error(f"  Error al reescribir prompt ({resp.status_code}): {resp.text}")
    except Exception as e:
        ui.error(f"  Error en llamada de reescritura: {e}")
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
    result = analyze_story_with_gpt(story_text, total_duration)
    if not result:
        return None
    scenes, visual_bible = result

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
                "visual_bible": visual_bible,
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

        img_bytes, error_msg = generate_image(prompt, n, model=model, visual_bible=visual_bible)

        # Si falla (ej: por seguridad o error 400), intentamos corregirlo con GPT-4o
        if not img_bytes and error_msg:
            if "safety" in error_msg.lower() or "policy" in error_msg.lower() or "rejected" in error_msg.lower() or "violation" in error_msg.lower():
                new_prompt = rewrite_prompt_for_safety(prompt, error_msg)
                if new_prompt:
                    time.sleep(2)  # Pausa corta
                    img_bytes, error_msg = generate_image(new_prompt, n, model=model, visual_bible=visual_bible)

        if img_bytes:
            img_path = out_dir / f"scene_{n:02d}.png"
            img_path.write_bytes(img_bytes)
            ui.success(f"  Guardada: {img_path.name} ({len(img_bytes) // 1024} KB)")
        else:
            ui.warn(f"  Falló la imagen de escena {n} (incluso tras reintentar desinfección).")
            failed.append(n)

        # Pausa entre generaciones para evitar rate limits
        if n < len(scenes):
            time.sleep(2)

    print()
    # ── Fallback para imágenes fallidas ──────────────────────────────────────
    if failed:
        ui.warn(f"Escenas que fallaron: {failed}. Aplicando fallbacks...")
        successful_imgs = sorted(list(out_dir.glob("scene_*.png")))
        if successful_imgs:
            # Usar la primera imagen exitosa como plantilla de fallback por defecto
            fallback_source = successful_imgs[0]
            
            for f_num in failed:
                dest_path = out_dir / f"scene_{f_num:02d}.png"
                # Intentar usar la escena anterior (n-1) si existe
                prev_path = out_dir / f"scene_{f_num-1:02d}.png"
                if prev_path.exists():
                    import shutil
                    shutil.copy(prev_path, dest_path)
                    ui.success(f"  [Fallback] Escena {f_num} copiada de Escena {f_num-1:02d}")
                else:
                    import shutil
                    shutil.copy(fallback_source, dest_path)
                    ui.success(f"  [Fallback] Escena {f_num} copiada de {fallback_source.name}")
        else:
            ui.error("Todas las imágenes de las escenas fallaron. No hay imágenes disponibles para fallback.")
            return None
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
