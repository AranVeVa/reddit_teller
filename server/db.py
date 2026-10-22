"""
server/db.py — Capa de persistencia para PostgreSQL en Neon.tech (o local).
Soporta usuarios, proyectos por usuario y almacenamiento en la nube gratuita de Neon.
"""
import os
import json
import uuid
import time
import hmac
import hashlib
import base64
import logging
from typing import Any
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.resolve()
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("JWT_SECRET", "reddit_teller_secret_key_2026")
LOCAL_USERS_FILE = ROOT / "projects" / "users.json"

logger = logging.getLogger("reddit_teller.db")


# ── Seguridad y Tokens ───────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${key}"


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt, key = stored_hash.split("$")
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return hmac.compare_digest(new_key, key)
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = json.dumps({"user_id": user_id, "email": email, "exp": time.time() + 86400 * 30})
    b64_payload = base64.urlsafe_b64encode(payload.encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), b64_payload.encode(), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{signature}"


def decode_access_token(token: str) -> dict | None:
    try:
        b64_payload, signature = token.split(".")
        expected_sig = hmac.new(SECRET_KEY.encode(), b64_payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode()).decode())
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ── Conexión Neon PostgreSQL ────────────────────────────────────────────────

def is_db_enabled() -> bool:
    """Retorna True si hay una URL de base de datos PostgreSQL configurada."""
    url = os.getenv("DATABASE_URL", "").strip()
    return bool(url and ("postgres://" in url or "postgresql://" in url))


def get_connection():
    """Crea una conexión con psycopg a PostgreSQL (Neon)."""
    import psycopg
    from psycopg.rows import dict_row

    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return psycopg.connect(url, row_factory=dict_row)


def init_db():
    """Inicializa las tablas necesarias en Neon PostgreSQL si no existen."""
    if not is_db_enabled():
        return False

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Tabla de usuarios
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(64) PRIMARY KEY,
                        email VARCHAR(128) UNIQUE NOT NULL,
                        password_hash VARCHAR(256) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Tabla de proyectos vinculados al usuario
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id VARCHAR(64) PRIMARY KEY,
                        user_id VARCHAR(64),
                        created_at VARCHAR(64),
                        current_step INT DEFAULT 1,
                        subreddit VARCHAR(128) DEFAULT '',
                        data JSONB NOT NULL,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Ajustes globales
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key VARCHAR(128) PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            conn.commit()
            logger.info("✔ Base de datos Neon inicializada correctamente con tabla de usuarios y proyectos.")
            return True
    except Exception as e:
        logger.warning(f"No se pudo inicializar la BD Neon ({e}). Usando almacenamiento local.")
        return False


# ── Gestión de Usuarios ─────────────────────────────────────────────────────

def _load_local_users() -> dict[str, dict]:
    LOCAL_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOCAL_USERS_FILE.exists():
        return {}
    try:
        return json.loads(LOCAL_USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_local_users(users: dict[str, dict]):
    LOCAL_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")


def register_user(email: str, password: str) -> dict[str, Any] | None:
    """Registra un nuevo usuario en Neon o localmente."""
    email_clean = email.strip().lower()
    pw_hash = hash_password(password)
    user_id = str(uuid.uuid4())[:8]

    if is_db_enabled():
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s;", (email_clean,))
                    if cur.fetchone():
                        return None  # Ya existe
                    cur.execute(
                        "INSERT INTO users (id, email, password_hash) VALUES (%s, %s, %s);",
                        (user_id, email_clean, pw_hash)
                    )
                conn.commit()
            token = create_access_token(user_id, email_clean)
            return {"user_id": user_id, "email": email_clean, "token": token}
        except Exception as e:
            logger.error(f"Error registrando usuario en Neon: {e}")

    # Fallback local
    users = _load_local_users()
    for u in users.values():
        if u.get("email") == email_clean:
            return None  # Ya existe
    users[user_id] = {
        "id": user_id,
        "email": email_clean,
        "password_hash": pw_hash,
        "created_at": time.time(),
    }
    _save_local_users(users)
    token = create_access_token(user_id, email_clean)
    return {"user_id": user_id, "email": email_clean, "token": token}


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """Verifica credenciales y retorna sesión de usuario."""
    email_clean = email.strip().lower()

    if is_db_enabled():
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, email, password_hash FROM users WHERE email = %s;", (email_clean,))
                    row = cur.fetchone()
                    if row and verify_password(row["password_hash"], password):
                        token = create_access_token(row["id"], row["email"])
                        return {"user_id": row["id"], "email": row["email"], "token": token}
        except Exception as e:
            logger.error(f"Error autenticando en Neon: {e}")

    # Fallback local
    users = _load_local_users()
    for uid, u in users.items():
        if u.get("email") == email_clean:
            if verify_password(u.get("password_hash", ""), password):
                token = create_access_token(uid, email_clean)
                return {"user_id": uid, "email": email_clean, "token": token}
    return None


def get_user_profile(user_id: str) -> dict[str, Any] | None:
    """Obtiene perfil de usuario sin hash."""
    if is_db_enabled():
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, email, created_at FROM users WHERE id = %s;", (user_id,))
                    row = cur.fetchone()
                    if row:
                        return {"id": row["id"], "email": row["email"]}
        except Exception as e:
            logger.error(f"Error obteniendo usuario en Neon: {e}")

    # Fallback local
    users = _load_local_users()
    u = users.get(user_id)
    if u:
        return {"id": u["id"], "email": u["email"]}
    return None


# ── Gestión de Proyectos ────────────────────────────────────────────────────

def db_save_project(project_data: dict[str, Any]) -> bool:
    """Guarda o actualiza un proyecto en Neon PostgreSQL."""
    if not is_db_enabled():
        return False

    project_id = project_data.get("id")
    if not project_id:
        return False

    user_id = project_data.get("user_id")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projects (id, user_id, created_at, current_step, subreddit, data, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        user_id = COALESCE(EXCLUDED.user_id, projects.user_id),
                        current_step = EXCLUDED.current_step,
                        subreddit = EXCLUDED.subreddit,
                        data = EXCLUDED.data,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    project_id,
                    user_id,
                    str(project_data.get("created_at", "")),
                    project_data.get("current_step", 1),
                    project_data.get("subreddit", ""),
                    json.dumps(project_data, ensure_ascii=False)
                ))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error al guardar proyecto {project_id} en Neon: {e}")
        return False


def db_get_project(project_id: str) -> dict[str, Any] | None:
    """Obtiene un proyecto por su ID desde Neon PostgreSQL."""
    if not is_db_enabled():
        return None

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM projects WHERE id = %s;", (project_id,))
                row = cur.fetchone()
                if row and "data" in row:
                    data = row["data"]
                    return json.loads(data) if isinstance(data, str) else data
    except Exception as e:
        logger.error(f"Error al obtener proyecto {project_id} de Neon: {e}")
    return None


def db_list_projects(user_id: str | None = None) -> list[dict[str, Any]]:
    """Lista proyectos desde Neon PostgreSQL (filtrando por user_id si se especifica)."""
    if not is_db_enabled():
        return []

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        "SELECT data FROM projects WHERE user_id = %s OR user_id IS NULL ORDER BY updated_at DESC;",
                        (user_id,)
                    )
                else:
                    cur.execute("SELECT data FROM projects ORDER BY updated_at DESC;")
                rows = cur.fetchall()
                results = []
                for r in rows:
                    data = r["data"]
                    results.append(json.loads(data) if isinstance(data, str) else data)
                return results
    except Exception as e:
        logger.error(f"Error al listar proyectos desde Neon: {e}")
        return []
# ── Ejecución directa de prueba / inicialización ────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if init_db():
        print("Tablas creadas exitosamente en Neon.")
    else:
        print("No se pudieron crear las tablas. Revisa que DATABASE_URL esté en el .env.")