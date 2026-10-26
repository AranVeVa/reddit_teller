import os
import json
import uuid
import time
import hmac
import hashlib
import base64
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from pathlib import Path

import bcrypt
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.resolve()
load_dotenv(ROOT / ".env")

logger = logging.getLogger("reddit_teller.db")


# ── Constantes ─────────────────────────────────────────────────────────────

ROLE_ADMIN = "Super Admin"
ROLE_USER = "Usuario"

VERIFICATION_TTL = timedelta(hours=1)
ACCESS_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7   # 7 días


# ── Excepciones ────────────────────────────────────────────────────────────

class DatabaseNotConfigured(Exception):
    """DATABASE_URL ausente o inválida."""


class EmailAlreadyRegistered(Exception):
    """El correo ya tiene cuenta."""


class ValidationError(Exception):
    """Datos de entrada inválidos."""


class InvalidToken(Exception):
    """Token inválido, expirado o ya consumido."""


class InvalidCredentials(Exception):
    """Correo o contraseña incorrectos."""


class EmailNotVerified(Exception):
    """Falta verificar el correo."""


# ── Conexión ───────────────────────────────────────────────────────────────

def is_db_enabled() -> bool:
    url = os.getenv("DATABASE_URL", "").strip()
    return bool(url and ("postgres://" in url or "postgresql://" in url))


def get_connection():
    if not is_db_enabled():
        raise DatabaseNotConfigured(
            "DATABASE_URL no está configurada. Añádela al .env con sslmode=require."
        )
    import psycopg
    from psycopg.rows import dict_row

    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg.connect(url, row_factory=dict_row)


def init_db() -> bool:
    if not is_db_enabled():
        return False
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Tabla base (creación nueva)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(64) PRIMARY KEY,
                        email VARCHAR(128) UNIQUE NOT NULL,
                        password_hash VARCHAR(256) NOT NULL,
                        role VARCHAR(32) DEFAULT 'Usuario',
                        is_premium BOOLEAN DEFAULT FALSE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        verification_token_hash VARCHAR(128),
                        verification_expires TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Migraciones idempotentes: añaden columnas si la tabla ya
                # existía de una versión anterior sin ellas.
                cur.execute("""
                    ALTER TABLE users
                        ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'Usuario',
                        ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE,
                        ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
                        ADD COLUMN IF NOT EXISTS verification_token_hash VARCHAR(128),
                        ADD COLUMN IF NOT EXISTS verification_expires TIMESTAMP WITH TIME ZONE,
                        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                """)

                # Rellenar NULLs por si la migración añadió columnas a filas viejas.
                cur.execute("""
                    UPDATE users
                    SET role = COALESCE(role, 'Usuario'),
                        is_premium = COALESCE(is_premium, FALSE),
                        is_verified = COALESCE(is_verified, FALSE)
                    WHERE role IS NULL OR is_premium IS NULL OR is_verified IS NULL;
                """)
            conn.commit()
        logger.info("✔ Base de datos Neon inicializada correctamente.")
        return True
    except Exception as e:
        logger.warning(f"Error inicializando BD Neon: {e}")
        return False

# ── Hashing ────────────────────────────────────────────────────────────────

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── Validación ─────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_registration(email: str, password: str) -> str:
    email_clean = (email or "").strip().lower()
    if not _EMAIL_RE.match(email_clean):
        raise ValidationError("El correo electrónico no tiene un formato válido")
    if not password or len(password) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres")
    return email_clean


# ── Access token (HMAC-SHA256, sin PyJWT) ──────────────────────────────────

def _secret_key() -> str:
    return os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET") or "dev-insecure-secret-change-me"


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (4 - len(s) % 4))


def _sign(payload_b64: str) -> str:
    sig = hmac.new(_secret_key().encode(), payload_b64.encode(), hashlib.sha256).digest()
    return _b64e(sig)


def create_access_token(user_id: str) -> str:
    now = int(time.time())
    payload = {"user_id": user_id, "iat": now, "exp": now + ACCESS_TOKEN_TTL_SECONDS}
    payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    return f"{payload_b64}.{_sign(payload_b64)}"


def decode_access_token(token: str) -> dict | None:
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(payload_b64), sig):
        return None
    try:
        payload = json.loads(_b64d(payload_b64))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


# ── Serialización pública ──────────────────────────────────────────────────

_PUBLIC_USER_FIELDS = ("id", "email", "role", "is_premium", "is_verified", "created_at")


def public_user(user: dict) -> dict:
    return {k: user.get(k) for k in _PUBLIC_USER_FIELDS if k in user}


# ── Registro y verificación ────────────────────────────────────────────────

def register_user(email: str, password: str) -> dict[str, Any]:
    email_clean = _validate_registration(email, password)
    if not is_db_enabled():
        raise DatabaseNotConfigured("DATABASE_URL no está configurada")

    user_id = str(uuid.uuid4())[:8]
    pw_hash = hash_password(password)
    raw_token = str(uuid.uuid4())
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + VERIFICATION_TTL

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s;", (email_clean,))
                if cur.fetchone():
                    raise EmailAlreadyRegistered()
                cur.execute(
                    """
                    INSERT INTO users
                        (id, email, password_hash, role, is_premium, is_verified,
                         verification_token_hash, verification_expires)
                    VALUES (%s, %s, %s, %s, FALSE, FALSE, %s, %s);
                    """,
                    (user_id, email_clean, pw_hash, ROLE_USER, token_hash, expires_at),
                )
            conn.commit()
    except EmailAlreadyRegistered:
        raise
    except Exception as e:
        logger.error(f"Error registrando usuario en Neon: {e}")
        raise ValidationError("Error interno al procesar el registro")

    return {
        "user": {
            "id": user_id,
            "email": email_clean,
            "role": ROLE_USER,
            "is_premium": False,
            "is_verified": False,
        },
        "verification_token": raw_token,
    }


def verify_email(raw_token: str) -> None:
    if not is_db_enabled():
        raise DatabaseNotConfigured("DATABASE_URL no está configurada")

    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, is_verified, verification_expires FROM users WHERE verification_token_hash = %s;",
                (token_hash,),
            )
            row = cur.fetchone()
            if not row:
                raise InvalidToken()
            if row["is_verified"]:
                return  # idempotente
            if row["verification_expires"] and row["verification_expires"] < now:
                raise InvalidToken()
            cur.execute(
                """
                UPDATE users
                SET is_verified = TRUE,
                    verification_token_hash = NULL,
                    verification_expires = NULL
                WHERE id = %s;
                """,
                (row["id"],),
            )
        conn.commit()


def regenerate_verification_token(email: str) -> dict | None:
    """Devuelve {'email', 'verification_token'} o None si no procede (silencioso)."""
    if not is_db_enabled():
        return None
    email_clean = (email or "").strip().lower()
    raw_token = str(uuid.uuid4())
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + VERIFICATION_TTL

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, is_verified FROM users WHERE email = %s;", (email_clean,))
                row = cur.fetchone()
                if not row or row["is_verified"]:
                    return None
                cur.execute(
                    """
                    UPDATE users
                    SET verification_token_hash = %s, verification_expires = %s
                    WHERE id = %s;
                    """,
                    (token_hash, expires_at, row["id"]),
                )
            conn.commit()
            return {"email": email_clean, "verification_token": raw_token}
    except Exception as e:
        logger.error(f"Error regenerando token: {e}")
        return None


# ── Autenticación ──────────────────────────────────────────────────────────

def authenticate_user(email: str, password: str) -> dict[str, Any]:
    if not is_db_enabled():
        raise DatabaseNotConfigured("DATABASE_URL no está configurada")
    email_clean = (email or "").strip().lower()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, password_hash, role, is_premium, is_verified "
                    "FROM users WHERE email = %s;",
                    (email_clean,),
                )
                user = cur.fetchone()
    except Exception as e:
        logger.error(f"Error autenticando usuario: {e}")
        raise InvalidCredentials()

    if not user or not _verify_password(password, user["password_hash"]):
        raise InvalidCredentials()
    if not user.get("is_verified"):
        raise EmailNotVerified()

    user.pop("password_hash", None)
    return {
        "user": public_user(user),
        "token": create_access_token(user["id"]),
    }


# ── Consultas / Admin ──────────────────────────────────────────────────────

def get_user(user_id: str) -> dict | None:
    if not is_db_enabled() or not user_id:
        return None
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, role, is_premium, is_verified, created_at "
                    "FROM users WHERE id = %s;",
                    (user_id,),
                )
                return cur.fetchone()
    except Exception as e:
        logger.error(f"Error obteniendo usuario {user_id}: {e}")
        return None


def list_users() -> list[dict]:
    if not is_db_enabled():
        return []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, role, is_premium, is_verified, created_at "
                    "FROM users ORDER BY created_at DESC;"
                )
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        return []


def count_super_admins() -> int:
    if not is_db_enabled():
        return 0
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM users WHERE role = %s;", (ROLE_ADMIN,))
                row = cur.fetchone()
                return int(row["n"]) if row else 0
    except Exception as e:
        logger.error(f"Error contando super admins: {e}")
        return 0


def update_user_access(
    user_id: str,
    role: str | None = None,
    is_premium: bool | None = None,
) -> dict:
    if not is_db_enabled():
        raise DatabaseNotConfigured("DATABASE_URL no está configurada")
    if role is None and is_premium is None:
        raise ValidationError("Nada que actualizar")
    if role is not None and (not isinstance(role, str) or not role.strip() or len(role) > 32):
        raise ValidationError("Rol inválido")

    sets, params = [], []
    if role is not None:
        sets.append("role = %s")
        params.append(role.strip())
    if is_premium is not None:
        sets.append("is_premium = %s")
        params.append(bool(is_premium))
    params.append(user_id)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {', '.join(sets)} WHERE id = %s "
                    f"RETURNING id, email, role, is_premium, is_verified, created_at;",
                    tuple(params),
                )
                row = cur.fetchone()
                if not row:
                    raise ValidationError("Usuario no encontrado")
            conn.commit()
            return row
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error actualizando usuario {user_id}: {e}")
        raise ValidationError("Error interno al actualizar el usuario")


def has_premium_access(user: dict | None) -> bool:
    if not user:
        return False
    if user.get("role") == ROLE_ADMIN:
        return True
    return bool(user.get("is_premium"))