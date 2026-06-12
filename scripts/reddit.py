import praw
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    STORIES_DIR,
)
from scripts import termui as ui

USED_IDS_FILE = STORIES_DIR / "used_ids.txt"

def _load_used_ids() -> set:
    if not USED_IDS_FILE.exists():
        return set()
    return set(USED_IDS_FILE.read_text(encoding="utf-8").splitlines())

def _save_used_id(post_id: str):
    with open(USED_IDS_FILE, "a", encoding="utf-8") as f:
        f.write(post_id + "\n")

def _get_reddit():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

def obtener_historias(
    subreddit: str,
    limite: int = 10,
    min_chars: int = 300,
    max_chars: int = 1500,
    orden: str = "hot",
) -> list[dict]:
    reddit = _get_reddit()
    sub = reddit.subreddit(subreddit)

    fetch_map = {
        "new": sub.new,
        "top": sub.top,
        "hot": sub.hot,
    }

    SEARCH_LIMIT = max(1000, limite * 100)
    posts = fetch_map.get(orden, sub.hot)(limit=SEARCH_LIMIT)

    used_ids = _load_used_ids()

    seen = set()
    historias = []

    descartados_usados = 0
    descartados_tamano = 0
    descartados_links = 0
    revisados = 0

    for post in posts:
        revisados += 1

        if post.id in seen or post.id in used_ids:
            descartados_usados += 1
            continue

        if not (min_chars <= len(post.selftext) <= max_chars):
            descartados_tamano += 1
            continue

        if "http" in post.selftext:
            descartados_links += 1
            continue

        seen.add(post.id)

        historias.append({
            "id": post.id,
            "title": post.title,
            "content": post.selftext,
            "score": post.score,
        })

        if len(historias) >= limite:
            break

    historias.sort(key=lambda x: x["score"], reverse=True)

    ui.info("Diagnóstico")
    ui.info(f"Posts revisados: {revisados}")
    ui.info(f"Descartados por tamaño: {descartados_tamano}")
    ui.info(f"Descartados por links: {descartados_links}")
    ui.info(f"Descartados por usados: {descartados_usados}")
    ui.success(f"Historias encontradas: {len(historias)}")

    return historias


def guardar_historias(historias: list[dict], subreddit: str) -> Path:
    if not historias:
        ui.warn("No se encontraron historias que cumplan los filtros.")
        return None

    # Create subdirectory for _dir in [AUDIOS_DIR, MIXED_DIR, SUBS_DIR, VIDEOS_DIR, STORIES_DIR]:
    sub_dir = STORIES_DIR / subreddit
    sub_dir.mkdir(parents=True, exist_ok=True)
    # Use the ID of the first story (or a placeholder) in the filename for identification
    first_id = historias[0]["id"] if historias else "unknown"
    archivo = sub_dir / f"{subreddit}_{first_id}.txt"
    
    with open(archivo, "w", encoding="utf-8") as f:
        for h in historias:
            f.write(
                f"{h['title']}\n"
                f"{h['content']}\n"
                f"{'—' * 40}\n\n"
            )
            _save_used_id(h["id"])
    
    ui.success(f"{len(historias)} historias guardadas en {archivo}")
    return archivo

def mostrar_historias(historias: list[dict]):
    for i, h in enumerate(historias, 1):
        preview = h["content"][:120].replace("\n", " ")
        ui.info(f"[{i}] {h['title']} (score: {h['score']})")
        ui.info(f"    {preview}...")