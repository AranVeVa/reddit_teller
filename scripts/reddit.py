import praw
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    HISTORIAS_DIR
)

USED_IDS_FILE = HISTORIAS_DIR / "used_ids.txt"

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
    fetch_map = {"new": sub.new, "top": sub.top, "hot": sub.hot}
    posts = fetch_map.get(orden, sub.hot)(limit=limite * 50)

    used_ids = _load_used_ids()
    seen = set()
    historias = []

    for post in posts:
        if post.id in seen or post.id in used_ids:
            continue
        if not (min_chars <= len(post.selftext) <= max_chars):
            continue
        if "http" in post.selftext:
            continue
        seen.add(post.id)
        historias.append({
            "id":      post.id,
            "title":   post.title,
            "content": post.selftext,
            "score":   post.score,
        })
        if len(historias) >= limite:
            break

    historias.sort(key=lambda x: x["score"], reverse=True)
    return historias

def guardar_historias(historias: list[dict], subreddit: str) -> Path:
    if not historias:
        print("⚠️  No se encontraron historias que cumplan los filtros.")
        return None

    archivo = HISTORIAS_DIR / f"{subreddit}.txt"
    with open(archivo, "w", encoding="utf-8") as f:
        for h in historias:
            f.write(f"{h['title']}\n{h['content']}\n{'—'*40}\n\n")
            _save_used_id(h["id"])

    print(f"✅ {len(historias)} historias guardadas en {archivo}")
    return archivo

def mostrar_historias(historias: list[dict]):
    for i, h in enumerate(historias, 1):
        preview = h["content"][:120].replace("\n", " ")
        print(f"\n[{i}] {h['title']} (score: {h['score']})\n    {preview}…")