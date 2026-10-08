import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
ENV_PATH = ROOT / ".env"


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip()
    if len(v) <= 8:
        return "••••••••"
    return f"{v[:3]}••••{v[-4:]}"


def parse_env_file(env_file: Path = ENV_PATH) -> tuple[dict[str, str], list[str]]:
    """
    Parsea .env preservando las líneas brutas (comentarios, espacios) y extrayendo un dict.
    """
    if not env_file.exists():
        return {}, []

    lines = env_file.read_text(encoding="utf-8").splitlines()
    data = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            # Quitar comillas si las hay
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            data[key] = val

    return data, lines


def update_env_file(updates: dict[str, str], env_file: Path = ENV_PATH) -> None:
    """
    Actualiza variables en .env manteniendo comentarios y orden.
    Variables nuevas se agregan al final.
    """
    current_data, lines = parse_env_file(env_file)
    updated_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in updates:
                new_val = updates[key]
                new_lines.append(f"{key}={new_val}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Agregar llaves completamente nuevas que no existían
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")

    content = "\n".join(new_lines) + "\n"

    # Escritura atómica con archivo .tmp y backup .bak
    bak_path = env_file.with_suffix(".env.bak")
    tmp_path = env_file.with_suffix(".env.tmp")

    if env_file.exists():
        bak_path.write_text(env_file.read_text(encoding="utf-8"), encoding="utf-8")

    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(env_file)


def get_masked_settings() -> dict:
    """Retorna las configuraciones clave enmascaradas para la UI."""
    data, _ = parse_env_file()
    return {
        "REDDIT_CLIENT_ID": mask_secret(data.get("REDDIT_CLIENT_ID")),
        "REDDIT_CLIENT_SECRET": mask_secret(data.get("REDDIT_CLIENT_SECRET")),
        "REDDIT_USER_AGENT": data.get("REDDIT_USER_AGENT", "story_teller"),
        "ELEVENLABS_API_KEYS": mask_secret(data.get("ELEVENLABS_API_KEYS")),
        "ELEVENLABS_VOICE_ID": data.get("ELEVENLABS_VOICE_ID", ""),
        "ELEVENLABS_SPEED": float(data.get("ELEVENLABS_SPEED", 1.1)),
        "OPENAI_API_KEY": mask_secret(data.get("OPENAI_API_KEY")),
        "BACKGROUND_AUDIO": data.get("BACKGROUND_AUDIO", "background_audio/Initiation.mp3"),
        "BACKGROUND_VIDEO": data.get("BACKGROUND_VIDEO", "background_videos/gameplay.mp4"),
        "VIDEO_WIDTH": int(data.get("VIDEO_WIDTH", 1080)),
        "VIDEO_HEIGHT": int(data.get("VIDEO_HEIGHT", 1920)),
        "BACKGROUND_VOLUME_DB": float(data.get("BACKGROUND_VOLUME_DB", -18)),
    }


def reveal_secret(key: str) -> str | None:
    """Retorna el valor real completo de una sola variable para el servidor local."""
    data, _ = parse_env_file()
    return data.get(key)
