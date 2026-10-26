"""
server/storage.py — Gestión de almacenamiento y auto-limpieza para planes gratuitos.
Monitorea el espacio ocupado por videos/audios y borra automáticamente los archivos
más antiguos cuando se alcanza el límite gratuito (ej. 300MB de los 512MB de Render).
"""
import os
import shutil
from pathlib import Path
from typing import Any
import logging

ROOT = Path(__file__).parent.parent.resolve()
OUTPUTS_DIR = ROOT / "outputs"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
AUDIOS_DIR = OUTPUTS_DIR / "audios"
MIXED_DIR = OUTPUTS_DIR / "mixed"

logger = logging.getLogger("reddit_teller.storage")

# Límite por defecto en MB (ajustable en .env con MAX_STORAGE_MB)
DEFAULT_MAX_STORAGE_MB = int(os.getenv("MAX_STORAGE_MB", "350"))


def get_dir_size_bytes(directory: Path) -> int:
    """Calcula el tamaño total en bytes de un directorio."""
    total = 0
    if not directory.exists():
        return 0
    for root, _, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def get_storage_stats() -> dict[str, Any]:
    """Retorna estadísticas de espacio usado y porcentaje de cuota gratuita."""
    max_mb = int(os.getenv("MAX_STORAGE_MB", DEFAULT_MAX_STORAGE_MB))
    videos_bytes = get_dir_size_bytes(VIDEOS_DIR)
    audios_bytes = get_dir_size_bytes(AUDIOS_DIR) + get_dir_size_bytes(MIXED_DIR)
    total_bytes = videos_bytes + audios_bytes

    used_mb = round(total_bytes / (1024 * 1024), 2)
    percent = round(min(100.0, (used_mb / max_mb) * 100), 1) if max_mb > 0 else 0.0

    return {
        "used_mb": used_mb,
        "max_mb": max_mb,
        "percent": percent,
        "videos_mb": round(videos_bytes / (1024 * 1024), 2),
        "audios_mb": round(audios_bytes / (1024 * 1024), 2),
        "is_near_limit": percent >= 85.0,
    }


def _delete_files(files: list[Path]) -> tuple[list[str], int]:
    deleted, freed = [], 0
    for f in files:
        try:
            size = f.stat().st_size
            f.unlink()
            deleted.append(f.name)
            freed += size
        except OSError as e:
            logger.warning(f"No se pudo borrar {f}: {e}")
    return deleted, freed


def _prune_empty_dirs(root: Path) -> None:
    if not root.exists():
        return
    for d in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        try:
            d.rmdir()  # solo borra si está vacío
        except OSError:
            pass


def cleanup_storage_manual() -> dict[str, Any]:
    """
    Limpieza solicitada por el usuario: elimina los audios generados (voz y mezclas,
    se pueden regenerar) y todos los renders antiguos, conservando el MP4 más reciente.
    """
    before = get_storage_stats()
    audio_files = [f for d in (AUDIOS_DIR, MIXED_DIR) if d.exists() for f in d.rglob("*") if f.is_file()]
    videos = sorted((f for f in VIDEOS_DIR.rglob("*") if f.is_file()), key=lambda f: f.stat().st_mtime) if VIDEOS_DIR.exists() else []
    old_videos = videos[:-1]  # conserva el render más reciente

    deleted_a, freed_a = _delete_files(audio_files)
    deleted_v, freed_v = _delete_files(old_videos)
    for d in (AUDIOS_DIR, MIXED_DIR, VIDEOS_DIR):
        _prune_empty_dirs(d)

    after = get_storage_stats()
    return {
        "cleaned": bool(deleted_a or deleted_v),
        "deleted_count": len(deleted_a) + len(deleted_v),
        "deleted_files": deleted_a + deleted_v,
        "freed_mb": round((freed_a + freed_v) / (1024 * 1024), 2),
        "previous_used_mb": before["used_mb"],
        "current_used_mb": after["used_mb"],
    }


def cleanup_storage_if_needed(target_free_margin_mb: int = 50) -> dict[str, Any]:
    """
    Si el espacio usado excede el límite máximo configurado, elimina los archivos
    de video MP4 más antiguos hasta liberar el espacio requerido.
    """
    max_mb = int(os.getenv("MAX_STORAGE_MB", DEFAULT_MAX_STORAGE_MB))
    stats = get_storage_stats()
    deleted_files = []
    freed_mb = 0.0

    if stats["used_mb"] < max_mb:
        return {
            "cleaned": False,
            "deleted_count": 0,
            "freed_mb": 0.0,
            "current_used_mb": stats["used_mb"],
        }

    # Recolectar todos los archivos .mp4 de outputs/videos con su fecha de modificación
    video_files = []
    if VIDEOS_DIR.exists():
        for f in VIDEOS_DIR.rglob("*.mp4"):
            if f.is_file():
                try:
                    stat = f.stat()
                    video_files.append((f, stat.st_mtime, stat.st_size))
                except OSError:
                    pass

    # Ordenar por fecha de modificación (los más antiguos primero)
    video_files.sort(key=lambda x: x[1])

    target_bytes = (max_mb - target_free_margin_mb) * 1024 * 1024
    current_bytes = int(stats["used_mb"] * 1024 * 1024)

    for file_path, mtime, size in video_files:
        if current_bytes <= target_bytes:
            break
        try:
            file_path.unlink()
            current_bytes -= size
            freed_mb += round(size / (1024 * 1024), 2)
            deleted_files.append(str(file_path.name))
            logger.info(f"Auto-cleanup: Eliminado video antiguo {file_path.name} ({round(size/(1024*1024), 2)}MB)")
        except Exception as e:
            logger.warning(f"No se pudo borrar {file_path}: {e}")

    # Limpiar directorios vacíos dentro de outputs/videos
    if VIDEOS_DIR.exists():
        for d in list(VIDEOS_DIR.iterdir()):
            if d.is_dir() and not any(d.iterdir()):
                try:
                    d.rmdir()
                except OSError:
                    pass

    return {
        "cleaned": len(deleted_files) > 0,
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files,
        "freed_mb": round(freed_mb, 2),
        "current_used_mb": round(current_bytes / (1024 * 1024), 2),
    }
