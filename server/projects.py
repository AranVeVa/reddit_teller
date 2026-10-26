"""
server/projects.py — Proyectos del pipeline.

Un proyecto nace como BORRADOR (solo archivo local en projects/<id>/project.json,
necesario para que los workers lean/escriban resultados de los pasos 1-6) y
únicamente se envía a Neon cuando se confirma (`commit_project`), es decir, cuando
está completo y el usuario pulsa "Comenzar Renderizado Final".
"""
import json
import re
import shutil
import time
from pathlib import Path
from typing import Any
from server import db

ROOT = Path(__file__).parent.parent.resolve()
PROJECTS_DIR = ROOT / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

# Campos que el cliente puede fijar al crear el borrador / confirmar el proyecto.
CLIENT_FIELDS = (
    "subreddit", "order", "duration_preset", "min_chars", "max_chars", "limit",
    "dark_mode", "words_per_card", "language",
    "background_type", "background_video_path", "start_second",
)


def is_valid_project_id(project_id: str) -> bool:
    return bool(project_id and PROJECT_ID_RE.match(project_id))


def _pick_client_fields(data: dict[str, Any] | None) -> dict[str, Any]:
    return {k: v for k, v in (data or {}).items() if k in CLIENT_FIELDS}


def _default_project(project_id: str) -> dict[str, Any]:
    return {
        "id": project_id,
        "created_at": str(time.time()),
        "committed": False,
        "user_id": None,
        "current_step": 1,
        "subreddit": "",
        "order": "hot",
        "duration_preset": "1",
        "min_chars": 300,
        "max_chars": 1500,
        "limit": 1,
        "candidates": [],
        "accepted_stories": [],
        "voice_result": None,
        "mixed_result": None,
        "subtitles_result": None,
        "background_type": "video",
        "background_video_path": "",
        "scenes_plan": None,
        "scenes_rendered": False,
        "final_video_path": None,
        "dark_mode": True,
        "words_per_card": 3,
        "language": None,
    }


def create_draft(project_id: str, initial_data: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    """Crea el borrador local (NO toca la base de datos)."""
    if not is_valid_project_id(project_id):
        raise ValueError("ID de proyecto inválido")
    project = {**_default_project(project_id), **_pick_client_fields(initial_data), "user_id": user_id}
    save_project(project)
    return project


def get_project(project_id: str) -> dict[str, Any] | None:
    if not is_valid_project_id(project_id):
        return None
    if db.is_db_enabled():
        res = db.db_get_project(project_id)
        if res:
            return res
    json_path = PROJECTS_DIR / project_id / "project.json"
    if not json_path.exists():
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_project(project_data: dict[str, Any]) -> None:
    """Siempre respalda en disco; sube a Neon solo los proyectos confirmados."""
    if project_data.get("committed") and db.is_db_enabled():
        db.db_save_project(project_data)

    project_id = project_data["id"]
    if not is_valid_project_id(project_id):
        raise ValueError("ID de proyecto inválido")
    p_dir = PROJECTS_DIR / project_id
    p_dir.mkdir(parents=True, exist_ok=True)
    with open(p_dir / "project.json", "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)


def missing_for_render(project: dict[str, Any]) -> list[str]:
    """Lista legible de lo que falta para poder renderizar (vacía si está completo)."""
    missing = []
    if not project.get("accepted_stories"):
        missing.append("Historias aceptadas (paso 2-3)")
    voice = project.get("voice_result") or {}
    mixed = project.get("mixed_result") or {}
    if not (voice.get("audio_path") or mixed.get("mixed_audio_path")):
        missing.append("Voz / mezcla de audio (paso 4)")
    if not (project.get("subtitles_result") or {}).get("srt_path"):
        missing.append("Subtítulos (paso 5)")
    if project.get("background_type") == "scenes" and not project.get("scenes_rendered"):
        missing.append("Escenas IA renderizadas (paso 6)")
    return missing


def commit_project(project_id: str, client_data: dict[str, Any], user_id: str | None) -> dict[str, Any]:
    """
    Confirma un borrador: aplica solo los campos permitidos del cliente, valida que esté
    completo y lo guarda por primera vez en Neon. Lanza LookupError / ValueError.
    """
    project = get_project(project_id)
    if not project:
        raise LookupError("Proyecto no encontrado")

    project.update(_pick_client_fields(client_data))
    missing = missing_for_render(project)
    if missing:
        raise ValueError("El proyecto está incompleto: " + "; ".join(missing))

    project["committed"] = True
    if user_id:
        project["user_id"] = user_id
    project["current_step"] = max(int(project.get("current_step") or 1), 7)
    save_project(project)
    return project


def list_projects(user_id: str | None = None) -> list[dict[str, Any]]:
    """Proyectos confirmados. Con sesión: solo los del usuario; sin sesión: los sin dueño."""
    if db.is_db_enabled():
        db_projs = db.db_list_projects(user_id=user_id)
        if db_projs:
            return db_projs

    projects = []
    for p_dir in PROJECTS_DIR.iterdir():
        if not p_dir.is_dir():
            continue
        p = get_project(p_dir.name)
        if not p or p.get("committed") is False:  # los borradores no se listan
            continue
        owner = p.get("user_id")
        if (user_id and owner and owner != user_id) or (not user_id and owner):
            continue
        projects.append(p)
    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return projects


def purge_stale_drafts(max_age_days: float = 3.0) -> int:
    """Borra del disco los borradores abandonados (nunca confirmados)."""
    removed = 0
    limit = time.time() - max_age_days * 86400
    for p_dir in PROJECTS_DIR.iterdir():
        json_path = p_dir / "project.json"
        if not json_path.exists():
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if data.get("committed") is False and json_path.stat().st_mtime < limit:
                shutil.rmtree(p_dir, ignore_errors=True)
                removed += 1
        except Exception:
            continue
    return removed
