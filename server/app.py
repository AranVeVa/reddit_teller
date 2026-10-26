import asyncio
import ipaddress
import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator
from urllib.parse import urlparse

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from server import db, envfile, mailer, payments, projects, storage


# ── Constantes ─────────────────────────────────────────────────────────────

PIPELINE_STEPS = {
    "search_stories", "accept_stories", "generate_voice", "mix_audio",
    "generate_subtitles", "plan_scenes", "render_scenes", "regenerate_scene",
    "render_video",
}
AI_STEPS = {"plan_scenes", "render_scenes", "regenerate_scene"}

MAX_VIDEO_UPLOAD_MB = 500
MAX_AUDIO_UPLOAD_MB = 50
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB

JOB_TTL_SECONDS = 60 * 60  # mantener jobs terminados 1h en memoria

# Diccionario en memoria para rastrear workers en ejecución y sus logs
JOBS: dict[str, dict] = {}


# ── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    projects.purge_stale_drafts()
    yield


app = FastAPI(title="reddit_teller API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://redditteller-frontend.vercel.app"
        ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos Pydantic ───────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    email: str
    password: str


class EmailRequest(BaseModel):
    email: str


class VerifyEmailRequest(BaseModel):
    token: str


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_premium: bool | None = None


class ConfirmCheckoutRequest(BaseModel):
    session_id: str


class SimulatePaymentRequest(BaseModel):
    outcome: str = "approved"  # approved | rejected


class VideoLinkValidate(BaseModel):
    url: str


class SettingsUpdate(BaseModel):
    settings: dict[str, Any]


class RevealRequest(BaseModel):
    key: str


class ProjectCommit(BaseModel):
    """Confirmación del proyecto completo (solo aquí se crea el registro en Neon)."""
    id: str
    subreddit: str | None = None
    order: str | None = None
    duration_preset: str | None = None
    min_chars: int | None = None
    max_chars: int | None = None
    limit: int | None = None
    dark_mode: bool | None = None
    words_per_card: int | None = None
    language: str | None = None
    background_type: str | None = None
    background_video_path: str | None = None
    start_second: float | None = None


class ProjectUpdate(BaseModel):
    data: dict


class StepRunRequest(BaseModel):
    args: dict = {}
    project: dict | None = None


# ── Helpers de sesión y permisos ───────────────────────────────────────────

def _bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def current_user_optional(request: Request) -> dict | None:
    """Fila de usuario (verificado) a partir del Bearer token, o None."""
    token = _bearer_token(request)
    payload = db.decode_access_token(token) if token else None
    if not payload:
        return None
    row = db.get_user(payload.get("user_id", ""))
    return row if row and row.get("is_verified") else None


def current_user_required(request: Request) -> dict:
    user = current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar")
    return user


def require_admin(request: Request) -> dict:
    user = current_user_required(request)
    if user.get("role") != db.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Se requiere rol Super Admin")
    return user


def _check_project_access(project: dict, user: dict | None) -> None:
    owner = project.get("user_id")
    if not owner:
        return
    if not user or (user["id"] != owner and user.get("role") != db.ROLE_ADMIN):
        raise HTTPException(status_code=403, detail="No tienes acceso a este proyecto")


# FIX: ahora acepta user=None sin reventar.
def _user_has_premium(user: dict | None) -> bool:
    if user is None:
        return False
    try:
        return bool(db.has_premium_access(user))
    except Exception:
        return False


def _step_requires_ai(step_name: str, args: dict, project: dict) -> bool:
    if step_name in AI_STEPS:
        return True
    if step_name == "render_video":
        # FIX (seguridad): si el proyecto fue comiteado con escenas, SIEMPRE
        # requiere Premium, sin importar lo que mande el cliente en `args`.
        # Así no se puede evadir el check enviando {"use_scenes": false}.
        if project.get("background_type") == "scenes":
            return True
        return bool(args.get("use_scenes", False))
    return False


# ── Helpers de jobs ────────────────────────────────────────────────────────

def _any_job_running() -> bool:
    return any(j["process"].poll() is None for j in JOBS.values())


def _prune_jobs() -> None:
    """Elimina jobs terminados hace más de JOB_TTL_SECONDS."""
    cutoff = time.time() - JOB_TTL_SECONDS
    for jid in [j for j, info in JOBS.items()
                if info.get("finished_at") and info["finished_at"] < cutoff]:
        JOBS.pop(jid, None)


# ── Helpers de red / seguridad ─────────────────────────────────────────────

def _assert_safe_public_url(url: str) -> None:
    """FIX: previene SSRF. Rechaza esquemas no http(s) y hosts privados/loopback."""
    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="URL inválida")

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail="Debe ser una URL válida que comience con http:// o https://",
        )
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL sin hostname")

    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail=f"No se pudo resolver el host: {parsed.hostname}")

    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise HTTPException(status_code=400, detail="La URL apunta a una dirección no permitida")


async def _save_upload_limited(file: UploadFile, dest_path: Path, max_mb: int) -> int:
    """FIX: guarda por chunks en vez de cargar todo en memoria, con tope de tamaño."""
    max_bytes = max_mb * 1024 * 1024
    total = 0
    try:
        with dest_path.open("wb") as f:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Archivo demasiado grande (máx {max_mb} MB)",
                    )
                f.write(chunk)
    except Exception:
        dest_path.unlink(missing_ok=True)
        raise
    return total


# ── Manejo de errores ──────────────────────────────────────────────────────

@app.exception_handler(db.DatabaseNotConfigured)
async def _db_not_configured(_: Request, exc: db.DatabaseNotConfigured):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# ── Autenticación ──────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def auth_register(payload: AuthRequest, background: BackgroundTasks):
    """Crea la cuenta sin verificar y envía el correo de confirmación. No inicia sesión."""
    try:
        result = db.register_user(payload.email, payload.password)
    except db.EmailAlreadyRegistered:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    except db.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background.add_task(
        mailer.send_verification_email,
        result["user"]["email"],
        result["verification_token"],
    )
    return {
        "status": "ok",
        "requires_verification": True,
        "email": result["user"]["email"],
        "message": "Cuenta creada. Revisa tu correo para confirmarla.",
    }


@app.post("/api/auth/verify-email")
def auth_verify_email(payload: VerifyEmailRequest):
    try:
        db.verify_email(payload.token)
    except db.InvalidToken:
        raise HTTPException(
            status_code=400,
            detail="El enlace de verificación no es válido o ya fue utilizado",
        )
    return {"status": "ok", "message": "Correo verificado. Ya puedes iniciar sesión."}


@app.post("/api/auth/resend-verification")
def auth_resend_verification(payload: EmailRequest, background: BackgroundTasks):
    # Respuesta idéntica exista o no la cuenta (no revela qué correos están registrados).
    res = db.regenerate_verification_token(payload.email)
    if res:
        background.add_task(
            mailer.send_verification_email,
            res["email"],
            res["verification_token"],
        )
    return {
        "status": "ok",
        "message": "Si la cuenta existe y no está verificada, enviamos un nuevo enlace.",
    }


@app.post("/api/auth/login")
def auth_login(payload: AuthRequest):
    try:
        session = db.authenticate_user(payload.email, payload.password)
    except db.InvalidCredentials:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    except db.EmailNotVerified:
        raise HTTPException(
            status_code=403,
            detail="Debes confirmar tu correo antes de iniciar sesión",
        )
    return {"status": "ok", "user": session["user"], "token": session["token"]}


@app.get("/api/auth/me")
def auth_me(request: Request):
    user = current_user_optional(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": db.public_user(user)}


# ── Panel de Super Administrador ───────────────────────────────────────────

@app.get("/api/admin/users")
def admin_list_users(request: Request):
    require_admin(request)
    return {"users": db.list_users()}


@app.patch("/api/admin/users/{user_id}")
def admin_update_user(user_id: str, payload: AdminUserUpdate, request: Request):
    admin = require_admin(request)
    if payload.role is None and payload.is_premium is None:
        raise HTTPException(status_code=400, detail="Nada que actualizar")

    target = db.get_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    leaving_admin = (
        target.get("role") == db.ROLE_ADMIN
        and payload.role not in (None, db.ROLE_ADMIN)
    )
    if leaving_admin and (admin["id"] == user_id or db.count_super_admins() <= 1):
        raise HTTPException(
            status_code=400,
            detail="No puedes quitar el rol al último Super Admin ni a tu propia cuenta",
        )

    try:
        updated = db.update_user_access(user_id, role=payload.role, is_premium=payload.is_premium)
    except db.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "user": updated}


# ── Pagos / suscripción Pro ────────────────────────────────────────────────

@app.get("/api/payments/config")
def payments_config():
    return payments.get_config()


@app.post("/api/payments/checkout")
def payments_checkout(request: Request):
    user = current_user_required(request)
    if db.has_premium_access(user):
        raise HTTPException(status_code=400, detail="Tu cuenta ya tiene acceso Premium")
    if payments.get_mode() != "stripe":
        raise HTTPException(
            status_code=400,
            detail="Stripe no está activo; usa el simulador de pago",
        )
    try:
        return {"mode": "stripe", "url": payments.create_checkout_session(user)}
    except payments.PaymentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error de Stripe: {e}")


@app.post("/api/payments/confirm")
def payments_confirm(payload: ConfirmCheckoutRequest, request: Request):
    user = current_user_required(request)
    try:
        return {
            "status": "ok",
            "user": payments.confirm_checkout_session(user, payload.session_id),
        }
    except payments.PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/payments/simulate")
def payments_simulate(payload: SimulatePaymentRequest, request: Request):
    user = current_user_required(request)
    try:
        return {"status": "ok", "user": payments.simulate_payment(user, payload.outcome)}
    except payments.PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))


@app.post("/api/payments/webhook")
async def payments_webhook(request: Request):
    try:
        payments.handle_webhook(await request.body(), request.headers.get("stripe-signature"))
    except payments.PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"received": True}


# ── Almacenamiento ─────────────────────────────────────────────────────────

@app.get("/api/storage/status")
def storage_status():
    return storage.get_storage_stats()


@app.post("/api/storage/cleanup")
def storage_cleanup(request: Request):
    """Limpieza manual: borra audios generados y renders antiguos (conserva el último MP4)."""
    current_user_required(request)
    if _any_job_running():
        raise HTTPException(
            status_code=409,
            detail="Hay un proceso en ejecución. Espera a que termine para limpiar.",
        )
    return {"status": "ok", **storage.cleanup_storage_manual()}


# ── Validación de enlaces ──────────────────────────────────────────────────

@app.post("/api/links/validate_video")
def validate_video_link(payload: VideoLinkValidate):
    url = payload.url.strip()
    # FIX (SSRF): pre-check + post-check tras redirects.
    _assert_safe_public_url(url)
    try:
        import requests
        resp = requests.head(url, timeout=10, allow_redirects=True, max_redirects=2)
        if resp.url and resp.url != url:
            _assert_safe_public_url(resp.url)

        content_type = resp.headers.get("Content-Type", "")
        content_length = resp.headers.get("Content-Length")
        size_mb = (
            round(int(content_length) / (1024 * 1024), 2)
            if content_length and content_length.isdigit()
            else None
        )
        return {
            "valid": True,
            "url": url,
            "final_url": resp.url,
            "content_type": content_type,
            "size_mb": size_mb,
            "msg": "Enlace de video válido y accesible",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo acceder al enlace: {e}")


# ── Configuración (.env) ───────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings(request: Request):
    # FIX: requiere sesión (aunque los valores estén enmascarados, expone la
    # existencia y estructura de las claves).
    current_user_required(request)
    return envfile.get_masked_settings()


@app.put("/api/settings")
def update_settings(payload: SettingsUpdate, request: Request):
    require_admin(request)
    try:
        envfile.update_env_file(payload.settings)
        return {"status": "success", "settings": envfile.get_masked_settings()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/reveal")
def reveal_setting(payload: RevealRequest, request: Request):
    require_admin(request)
    val = envfile.reveal_secret(payload.key)
    if val is None:
        raise HTTPException(status_code=404, detail="Llave no encontrada")
    return {"key": payload.key, "value": val}


@app.post("/api/settings/test/{service}")
def test_service_credentials(service: str, request: Request):
    require_admin(request)
    data, _ = envfile.parse_env_file()

    if service == "reddit":
        try:
            import praw
            r = praw.Reddit(
                client_id=data.get("REDDIT_CLIENT_ID"),
                client_secret=data.get("REDDIT_CLIENT_SECRET"),
                user_agent=data.get("REDDIT_USER_AGENT", "story_teller"),
            )
            sub = r.subreddit("test")
            return {"status": "ok", "msg": f"Conexión exitosa a Reddit API (r/{sub.display_name})"}
        except Exception as e:
            return {"status": "error", "msg": f"Fallo al conectar con Reddit: {e}"}

    elif service == "elevenlabs":
        try:
            import requests
            keys = [k.strip() for k in data.get("ELEVENLABS_API_KEYS", "").split(",") if k.strip()]
            if not keys:
                return {"status": "error", "msg": "No hay ELEVENLABS_API_KEYS en .env"}
            resp = requests.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": keys[0]},
                timeout=10,
            )
            if resp.status_code == 200:
                sub_info = resp.json().get("subscription", {})
                used = sub_info.get("character_count", 0)
                limit = sub_info.get("character_limit", 0)
                return {"status": "ok", "msg": f"ElevenLabs OK (Caracteres usados: {used}/{limit})"}
            return {
                "status": "error",
                "msg": f"ElevenLabs API error ({resp.status_code}): {resp.text[:100]}",
            }
        except Exception as e:
            return {"status": "error", "msg": f"Fallo de conexión con ElevenLabs: {e}"}

    elif service == "openai":
        try:
            import requests
            key = data.get("OPENAI_API_KEY")
            if not key:
                return {"status": "error", "msg": "OPENAI_API_KEY no configurada"}
            resp = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {"status": "ok", "msg": "Conexión exitosa con OpenAI API (GPT-4o / DALL-E 3)"}
            return {
                "status": "error",
                "msg": f"OpenAI API error ({resp.status_code}): {resp.text[:100]}",
            }
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
            return {
                "status": "error",
                "msg": "Fallo al conectar con Neon PostgreSQL. Revisa la URL y sslmode=require",
            }
        except Exception as e:
            return {"status": "error", "msg": f"Error conectando a Neon: {e}"}

    raise HTTPException(status_code=400, detail="Servicio desconocido")


# ── Assets / Biblioteca ────────────────────────────────────────────────────

@app.get("/api/assets")
def list_assets():
    audios = [str(f.relative_to(ROOT)) for f in (ROOT / "background_audio").glob("*.mp3")]
    videos = [str(f.relative_to(ROOT)) for f in (ROOT / "background_videos").glob("*.mp4")]
    return {"background_audios": audios, "background_videos": videos}


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


# ── Proyectos ──────────────────────────────────────────────────────────────

@app.get("/api/projects")
def get_projects(request: Request):
    user = current_user_optional(request)
    return projects.list_projects(user_id=user["id"] if user else None)


@app.post("/api/projects")
def commit_project(payload: ProjectCommit, request: Request):
    """
    Confirma el proyecto (pasos 1-6 completos) y lo guarda en Neon. Es la ÚNICA ruta que
    crea registros de proyecto en la base de datos; se invoca al pulsar
    "Comenzar Renderizado Final".
    """
    user = current_user_optional(request)
    if not projects.is_valid_project_id(payload.id):
        raise HTTPException(status_code=400, detail="ID de proyecto inválido")

    draft = projects.get_project(payload.id)
    if not draft:
        raise HTTPException(
            status_code=404,
            detail="No hay un borrador con ese ID: completa los pasos primero",
        )
    _check_project_access(draft, user)

    client_data = payload.dict(exclude={"id"}, exclude_none=True)
    # FIX: has_premium_access(None) ya no revienta.
    if client_data.get("background_type") == "scenes" and not _user_has_premium(user):
        raise HTTPException(
            status_code=403,
            detail="Las escenas con IA requieren una suscripción Premium",
        )

    try:
        return projects.commit_project(payload.id, client_data, user["id"] if user else None)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/projects/{project_id}")
def get_project_by_id(project_id: str, request: Request):
    p = projects.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    _check_project_access(p, current_user_optional(request))
    return p


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate, request: Request):
    p = projects.get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    user = current_user_optional(request)
    _check_project_access(p, user)

    allowed = {k: v for k, v in payload.data.items() if k in projects.CLIENT_FIELDS}
    # FIX: has_premium_access(None) + doble llamada a current_user_optional.
    if allowed.get("background_type") == "scenes" and not _user_has_premium(user):
        raise HTTPException(
            status_code=403,
            detail="Las escenas con IA requieren una suscripción Premium",
        )
    p.update(allowed)
    projects.save_project(p)
    return p


@app.post("/api/projects/{project_id}/steps/{step_name}")
def run_step(project_id: str, step_name: str, payload: StepRunRequest, request: Request):
    if step_name not in PIPELINE_STEPS:
        raise HTTPException(status_code=400, detail=f"Paso desconocido: {step_name}")
    if not projects.is_valid_project_id(project_id):
        raise HTTPException(status_code=400, detail="ID de proyecto inválido")

    user = current_user_optional(request)
    _prune_jobs()

    # Borrador local (sin tocar Neon) la primera vez que se ejecuta un paso.
    p = projects.get_project(project_id)
    if not p:
        # FIX: filtramos campos del payload.project para que el cliente no
        # pueda inyectar campos arbitrarios (p.ej. `committed=True` o `user_id`).
        initial_project = None
        if payload.project:
            initial_project = {
                k: v for k, v in payload.project.items() if k in projects.CLIENT_FIELDS
            }
        p = projects.create_draft(
            project_id, initial_project, user_id=user["id"] if user else None
        )
    _check_project_access(p, user)

    # Bloqueo preventivo: GPT-4o / DALL-E 3 solo para Premium y Super Admin.
    # FIX: user=None ya no revienta; y _step_requires_ai cierra el bypass.
    allow_ai = _user_has_premium(user)
    if _step_requires_ai(step_name, payload.args, p) and not allow_ai:
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Inicia sesión y activa Premium para usar escenas con IA",
            )
        raise HTTPException(
            status_code=403,
            detail="Las escenas con IA requieren una suscripción Premium",
        )

    if step_name == "render_video":
        if not p.get("committed"):
            raise HTTPException(
                status_code=409,
                detail="El proyecto debe confirmarse antes de renderizar",
            )
        stats = storage.get_storage_stats()
        if stats["used_mb"] >= stats["max_mb"]:
            storage.cleanup_storage_if_needed(target_free_margin_mb=100)
            stats = storage.get_storage_stats()
            if stats["used_mb"] >= stats["max_mb"]:
                raise HTTPException(
                    status_code=507,
                    detail=(
                        f"Almacenamiento lleno ({stats['used_mb']} MB / {stats['max_mb']} MB). "
                        "Usa «Limpiar almacenamiento»."
                    ),
                )

    job_id = str(uuid.uuid4())[:8]
    cmd = [
        sys.executable, "-m", "server.worker", project_id, step_name,
        "--args", json.dumps(payload.args),
    ]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["RT_ALLOW_AI"] = "1" if allow_ai else "0"

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
        start_new_session=True,  # FIX: permite killpg() para matar worker + ffmpeg
    )

    JOBS[job_id] = {
        "job_id": job_id,
        "project_id": project_id,
        "step_name": step_name,
        "process": proc,
        "status": "running",
        "events": [],
        "finished_at": None,
    }

    return {"job_id": job_id, "status": "started", "step_name": step_name}


# ── Jobs: SSE + cancelación ────────────────────────────────────────────────

@app.get("/api/jobs/{job_id}/events")
async def stream_job_events(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    proc = job["process"]

    async def event_generator() -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        try:
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
                    event_data = json.dumps(
                        {"type": "log", "level": "info", "msg": line_str}
                    )

                yield f"data: {event_data}\n\n"

            rc = proc.poll()
            if rc == 0:
                job["status"] = "done"
                end_evt = json.dumps(
                    {"type": "done", "level": "success", "msg": "Paso completado con éxito"}
                )
            else:
                job["status"] = "error"
                end_evt = json.dumps(
                    {"type": "error", "level": "error", "msg": f"Paso falló con código {rc}"}
                )
            yield f"data: {end_evt}\n\n"
        except asyncio.CancelledError:
            # Cliente desconectado del SSE. No matamos el worker: puede
            # reconectarse o el job debe terminar igual.
            raise
        finally:
            if job.get("finished_at") is None and proc.poll() is not None:
                job["finished_at"] = time.time()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    proc = job["process"]
    if proc.poll() is not None:
        return {"status": "already_finished"}

    # FIX: matar el grupo completo (worker + ffmpeg hijos), no solo el worker.
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass

    job["status"] = "cancelled"
    job["finished_at"] = time.time()
    return {"status": "cancelled"}


# ── Uploads ────────────────────────────────────────────────────────────────

@app.post("/api/upload/background_video")
async def upload_background_video(request: Request, file: UploadFile = File(...)):
    # FIX: auth + límite de tamaño + validación de nombre.
    current_user_required(request)
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
        raise HTTPException(
            status_code=400,
            detail="Formato de video no válido. Se requiere .mp4",
        )
    dest_dir = ROOT / "background_videos"
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    dest_path = dest_dir / safe_name
    size = await _save_upload_limited(file, dest_path, MAX_VIDEO_UPLOAD_MB)
    return {
        "status": "ok",
        "filename": safe_name,
        "path": f"background_videos/{safe_name}",
        "size_mb": round(size / (1024 * 1024), 2),
    }


@app.post("/api/upload/background_audio")
async def upload_background_audio(request: Request, file: UploadFile = File(...)):
    # FIX: auth + límite de tamaño + validación de nombre.
    current_user_required(request)
    if not file.filename.lower().endswith((".mp3", ".wav", ".aac", ".m4a", ".ogg")):
        raise HTTPException(
            status_code=400,
            detail="Formato de audio no válido. Se requiere .mp3",
        )
    dest_dir = ROOT / "background_audio"
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name
    dest_path = dest_dir / safe_name
    size = await _save_upload_limited(file, dest_path, MAX_AUDIO_UPLOAD_MB)
    return {
        "status": "ok",
        "filename": safe_name,
        "path": f"background_audio/{safe_name}",
        "size_mb": round(size / (1024 * 1024), 2),
    }


# ── Servir media ───────────────────────────────────────────────────────────

MEDIA_BLOCKED_DIRS = {"server", "scripts", "projects", "venv", ".venv", "__pycache__"}
# FIX: bloqueamos también datos estructurados y dumps que podrían caer en ROOT.
MEDIA_BLOCKED_SUFFIXES = {
    ".py", ".pyc", ".env", ".toml", ".cfg", ".ini", ".log",
    ".db", ".sqlite", ".sqlite3", ".dump", ".sql", ".bak",
    ".csv", ".xls", ".xlsx", ".swp", ".swo", ".tmp", ".pgpass",
}


@app.get("/media/{path:path}")
def serve_media(path: str):
    file_path = (ROOT / path).resolve()

    # Seguridad: solo dentro de la raíz y nunca código, .env, proyectos ni ocultos
    if not file_path.is_relative_to(ROOT):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    rel_parts = file_path.relative_to(ROOT).parts
    if (
        not rel_parts
        or rel_parts[0] in MEDIA_BLOCKED_DIRS
        or any(part.startswith(".") for part in rel_parts)
        or file_path.suffix.lower() in MEDIA_BLOCKED_SUFFIXES
    ):
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(str(file_path))