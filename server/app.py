import os
import sys
import json
import asyncio
import subprocess
import uuid
from pathlib import Path
from typing import AsyncGenerator, Any
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from server import envfile
from server import projects
from server import db
from server import storage

app = FastAPI(title="reddit_teller Local API", version="2.0.0")

@app.on_event("startup")
def on_startup():
    db.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diccionario en memoria para rastrear workers en ejecución y sus logs
JOBS: dict[str, dict] = {}



class AuthRequest(BaseModel):
    email: str
    password: str


class VideoLinkValidate(BaseModel):
    url: str

class SettingsUpdate(BaseModel):
    settings: dict[str, Any]


class RevealRequest(BaseModel):
    key: str


class ProjectCreate(BaseModel):
    subreddit: str = ""
    order: str = "hot"
    duration_preset: str = "1"
    limit: int = 1
    dark_mode: bool = True
    words_per_card: int = 3


class StepRunRequest(BaseModel):
    args: dict = {}



@app.post("/api/auth/register")
def auth_register(payload: AuthRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email y contraseña son requeridos")
    if len(payload.password) < 4:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")
    user = db.register_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=409, detail="El correo ya se encuentra registrado")
    return {"status": "ok", "user": user}


@app.post("/api/auth/login")
def auth_login(payload: AuthRequest):
    user = db.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return {"status": "ok", "user": user}


@app.get("/api/auth/me")
def auth_me(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False, "user": None}
    token = auth_header.split(" ", 1)[1].strip()
    payload = db.decode_access_token(token)
    if not payload:
        return {"authenticated": False, "user": None}
    profile = db.get_user_profile(payload.get("user_id", ""))
    return {"authenticated": True, "user": profile}


@app.get("/api/storage/status")
def storage_status():
    return storage.get_storage_stats()


@app.post("/api/storage/cleanup")
def storage_cleanup():
    res = storage.cleanup_storage_if_needed(target_free_margin_mb=100)
    return {"status": "ok", **res}


@app.post("/api/links/validate_video")
def validate_video_link(payload: VideoLinkValidate):
    url = payload.url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Debe ser una URL válida que comience con http:// o https://")
    try:
        import requests
        resp = requests.head(url, timeout=10, allow_redirects=True)
        content_type = resp.headers.get("Content-Type", "")
        content_length = resp.headers.get("Content-Length")
        size_mb = round(int(content_length) / (1024 * 1024), 2) if content_length and content_length.isdigit() else None
        return {
            "valid": True,
            "url": url,
            "content_type": content_type,
            "size_mb": size_mb,
            "msg": "Enlace de video válido y accesible",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo acceder al enlace: {e}")

@app.get("/api/settings")
def get_settings():
    return envfile.get_masked_settings()


@app.put("/api/settings")
def update_settings(payload: SettingsUpdate):
    try:
        envfile.update_env_file(payload.settings)
        return {"status": "success", "settings": envfile.get_masked_settings()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/reveal")
def reveal_setting(payload: RevealRequest):
    val = envfile.reveal_secret(payload.key)
    if val is None:
        raise HTTPException(status_code=440, detail="Llave no encontrada")
    return {"key": payload.key, "value": val}


@app.post("/api/settings/test/{service}")
def test_service_credentials(service: str):
    data, _ = envfile.parse_env_file()
    if service == "reddit":
        try:
            import praw
            r = praw.Reddit(
                client_id=data.get("REDDIT_CLIENT_ID"),
                client_secret=data.get("REDDIT_CLIENT_SECRET"),
                user_agent=data.get("REDDIT_USER_AGENT", "story_teller")
            )
            # Prueba ligera leyendo r/test
            sub = r.subreddit("test")
            title = sub.display_name
            return {"status": "ok", "msg": f"Conexión exitosa a Reddit API (r/{title})"}
        except Exception as e:
            return {"status": "error", "msg": f"Fallo al conectar con Reddit: {e}"}

    elif service == "elevenlabs":
        try:
            import requests
            keys = [k.strip() for k in data.get("ELEVENLABS_API_KEYS", "").split(",") if k.strip()]
            if not keys:
                return {"status": "error", "msg": "No hay ELEVENLABS_API_KEYS en .env"}
            key = keys[0]
            resp = requests.get("https://api.elevenlabs.io/v1/user", headers={"xi-api-key": key}, timeout=10)
            if resp.status_code == 200:
                user_data = resp.json()
                sub_info = user_data.get("subscription", {})
                used = sub_info.get("character_count", 0)
                limit = sub_info.get("character_limit", 0)
                return {"status": "ok", "msg": f"ElevenLabs OK (Caracteres usados: {used}/{limit})"}
            else:
                return {"status": "error", "msg": f"ElevenLabs API error ({resp.status_code}): {resp.text[:100]}"}
        except Exception as e:
            return {"status": "error", "msg": f"Fallo de conexión con ElevenLabs: {e}"}

    elif service == "openai":
        try:
            import requests
            key = data.get("OPENAI_API_KEY")
            if not key:
                return {"status": "error", "msg": "OPENAI_API_KEY no configurada"}
            resp = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
            if resp.status_code == 200:
                return {"status": "ok", "msg": "Conexión exitosa con OpenAI API (GPT-4o / DALL-E 3)"}
            else:
                return {"status": "error", "msg": f"OpenAI API error ({resp.status_code}): {resp.text[:100]}"}
        except Exception as e:
            return {"status": "error", "msg": f"Fallo de conexión con OpenAI: {e}"}

    elif service == "neon":
        try:
            url = data.get("DATABASE_URL")
            if not url:
                return {"status": "error", "msg": "DATABASE_URL no configurada en .env"}
            ok = db.init_db()
            if ok:
                return {"status": "ok", "msg": "Conexión exitosa con Neon PostgreSQL"}
            else:
                return {"status": "error", "msg": "Fallo al conectar con Neon PostgreSQL. Revisa la URL y sslmode=require"}
        except Exception as e:
            return {"status": "error", "msg": f"Error conectando a Neon: {e}"}

    else:
        raise HTTPException(status_code=400, detail="Servicio desconocido")


@app.get("/api/assets")
def list_assets():
    audios = [str(f.relative_to(ROOT)) for f in (ROOT / "background_audio").glob("*.mp3")]
    videos = [str(f.relative_to(ROOT)) for f in (ROOT / "background_videos").glob("*.mp4")]
    return {
        "background_audios": audios,
        "background_videos": videos,
    }


@app.get("/api/projects")
def get_projects(request: Request):
    auth_header = request.headers.get("Authorization")
    user_id = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        payload = db.decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")
    return projects.list_projects(user_id=user_id)


@app.post("/api/projects")
def create_new_project(payload: ProjectCreate, request: Request):
    data = payload.dict()
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        u = db.decode_access_token(token)
        if u:
            data["user_id"] = u.get("user_id")
    p = projects.create_project(data)
    return p


class ProjectUpdate(BaseModel):
    data: dict


@app.get("/api/projects/{project_id}")
def get_project_by_id(project_id: str):
    p = projects.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return p


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate):
    p = projects.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    p.update(payload.data)
    projects.save_project(p)
    return p


@app.post("/api/projects/{project_id}/steps/{step_name}")
def run_step(project_id: str, step_name: str, payload: StepRunRequest):
    p = projects.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    job_id = str(uuid.uuid4())[:8]
    python_bin = sys.executable

    cmd = [
        python_bin, "-m", "server.worker", project_id, step_name, "--args", json.dumps(payload.args)
    ]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )

    JOBS[job_id] = {
        "job_id": job_id,
        "project_id": project_id,
        "step_name": step_name,
        "process": proc,
        "status": "running",
        "events": [],
    }

    return {"job_id": job_id, "status": "started", "step_name": step_name}


@app.get("/api/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    proc = job["process"]

    async def event_generator() -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, proc.stdout.readline)
            if not line:
                if proc.poll() is not None:
                    break
                await asyncio.sleep(0.1)
                continue

            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("__RT_EVENT__"):
                event_data = line_str.replace("__RT_EVENT__", "")
            else:
                event_data = json.dumps({"type": "log", "level": "info", "msg": line_str})

            yield f"data: {event_data}\n\n"

        rc = proc.poll()
        if rc == 0:
            end_evt = json.dumps({"type": "done", "level": "success", "msg": "Paso completado con éxito"})
        else:
            end_evt = json.dumps({"type": "error", "level": "error", "msg": f"Paso falló con código {rc}"})

        yield f"data: {end_evt}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    proc = job["process"]
    if proc.poll() is None:
        proc.terminate()
        job["status"] = "cancelled"
        return {"status": "cancelled"}
    return {"status": "already_finished"}


@app.get("/api/library")
def get_library_all_media():
    def scan_dir(directory: Path, glob_pattern: str, category_name: str, media_type: str):
        items = []
        if directory.exists():
            for f in directory.rglob(glob_pattern):
                if f.is_file():
                    rel = str(f.relative_to(ROOT))
                    items.append({
                        "name": f.name,
                        "path": rel,
                        "category": category_name,
                        "type": media_type,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                        "created_at": f.stat().st_mtime,
                    })
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items

    return {
        "produced_videos": scan_dir(ROOT / "outputs" / "videos", "*.mp4", "Videos Producidos MP4", "video"),
        "elevenlabs_audios": scan_dir(ROOT / "outputs" / "audios", "*.mp3", "Voces ElevenLabs", "audio"),
        "mixed_audios": scan_dir(ROOT / "outputs" / "mixed", "*.mp3", "Audios Mezclados", "audio"),
        "background_videos": scan_dir(ROOT / "background_videos", "*.*", "Videos de Fondo Locales", "video"),
        "background_audios": scan_dir(ROOT / "background_audio", "*.*", "Música Ambiental Local", "audio"),
    }


@app.post("/api/upload/background_video")
async def upload_background_video(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
        raise HTTPException(status_code=400, detail="Formato de video no válido. Se requiere .mp4")
    dest_dir = ROOT / "background_videos"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename
    content = await file.read()
    dest_path.write_bytes(content)
    return {"status": "ok", "filename": file.filename, "path": f"background_videos/{file.filename}"}


@app.post("/api/upload/background_audio")
async def upload_background_audio(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp3", ".wav", ".aac", ".m4a", ".ogg")):
        raise HTTPException(status_code=400, detail="Formato de audio no válido. Se requiere .mp3")
    dest_dir = ROOT / "background_audio"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename
    content = await file.read()
    dest_path.write_bytes(content)
    return {"status": "ok", "filename": file.filename, "path": f"background_audio/{file.filename}"}


@app.get("/media/{path:path}")
def serve_media(path: str):
    file_path = (ROOT / path).resolve()
    # Seguridad: solo permitir servir dentro de la raíz del proyecto
    if not str(file_path).startswith(str(ROOT)):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(str(file_path))
