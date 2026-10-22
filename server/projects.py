import json
import uuid
from pathlib import Path
from typing import Any
from server import db

ROOT = Path(__file__).parent.parent.resolve()
PROJECTS_DIR = ROOT / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def create_project(initial_data: dict[str, Any] = None) -> dict[str, Any]:
    project_id = str(uuid.uuid4())[:8]
    p_dir = PROJECTS_DIR / project_id
    p_dir.mkdir(parents=True, exist_ok=True)

    project_data = {
        "id": project_id,
        "created_at": str(p_dir.stat().st_ctime),
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
        "background_type": "scenes",
        "background_video_path": "",
        "scenes_plan": None,
        "scenes_rendered": False,
        "final_video_path": None,
        "dark_mode": True,
        "words_per_card": 3,
        "language": None,
        **(initial_data or {})
    }

    save_project(project_data)
    return project_data


def get_project(project_id: str) -> dict[str, Any] | None:
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
    # 1. Guardar en Neon PostgreSQL si está activo
    if db.is_db_enabled():
        db.db_save_project(project_data)

    # 2. Respaldo local siempre disponible
    project_id = project_data["id"]
    p_dir = PROJECTS_DIR / project_id
    p_dir.mkdir(parents=True, exist_ok=True)
    json_path = p_dir / "project.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)


def list_projects(user_id: str | None = None) -> list[dict[str, Any]]:
    if db.is_db_enabled():
        db_projs = db.db_list_projects(user_id=user_id)
        if db_projs:
            return db_projs

    projects = []
    for p_dir in PROJECTS_DIR.iterdir():
        if p_dir.is_dir():
            p = get_project(p_dir.name)
            if p:
                if user_id and p.get("user_id") and p.get("user_id") != user_id:
                    continue
                projects.append(p)
    projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return projects
