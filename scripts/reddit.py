import praw
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    HISTORIAS_DIR
)


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
    """
    Devuelve hasta `limite` historias del subreddit que cumplan los filtros.
    Cada historia es un dict con: title, content, score, id.
    """
    reddit = _get_reddit()
    sub = reddit.subreddit(subreddit)

    fetch_map = {"new": sub.new, "top": sub.top, "hot": sub.hot}
    posts = fetch_map.get(orden, sub.hot)(limit=limite * 50)

    seen = set()
    historias = []

    for post in posts:
        if post.id in seen:
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
    """Guarda las historias en historias/<subreddit>.txt y devuelve la ruta."""
    if not historias:
        print("⚠️  No se encontraron historias que cumplan los filtros.")
        return None

    archivo = HISTORIAS_DIR / f"{subreddit}.txt"
    with open(archivo, "w", encoding="utf-8") as f:
        for i, h in enumerate(historias, 1):
            f.write(f"{h['title']}\n{h['content']}\n{'—'*40}\n\n")

    print(f"✅ {len(historias)} historias guardadas en {archivo}")
    return archivo


def mostrar_historias(historias: list[dict]):
    for i, h in enumerate(historias, 1):
        preview = h["content"][:120].replace("\n", " ")
        print(f"\n[{i}] {h['title']} (score: {h['score']})\n    {preview}…")