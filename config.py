from pathlib import Path
from dotenv import load_dotenv
import os

# Raíz del proyecto = carpeta donde vive config.py
ROOT = Path(__file__).parent.resolve()

load_dotenv(ROOT / ".env")

# --- Reddit ---
REDDIT_CLIENT_ID     = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT    = os.getenv("REDDIT_USER_AGENT", "story_teller")

# --- ElevenLabs ---
# Múltiples keys separadas por coma → se rotan en orden
_raw_keys = os.getenv("ELEVENLABS_API_KEYS", "")
ELEVENLABS_API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# --- Archivos de entrada ---
BACKGROUND_AUDIO = ROOT / os.getenv("BACKGROUND_AUDIO", "background_audio/Initiation.mp3")
BACKGROUND_VIDEO = ROOT / os.getenv("BACKGROUND_VIDEO", "background_videos/gameplay.mp4")

# --- Salidas ---
OUTPUTS_DIR     = ROOT / "outputs"
AUDIOS_DIR      = OUTPUTS_DIR / "audios"
MIXED_DIR       = OUTPUTS_DIR / "mixed"
SUBS_DIR        = OUTPUTS_DIR / "subs"
VIDEOS_DIR      = OUTPUTS_DIR / "videos"
STORIES_DIR   = ROOT / "stories"

for _dir in [AUDIOS_DIR, MIXED_DIR, SUBS_DIR, VIDEOS_DIR, STORIES_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# --- Video ---
VIDEO_WIDTH           = int(os.getenv("VIDEO_WIDTH", 1080))
VIDEO_HEIGHT          = int(os.getenv("VIDEO_HEIGHT", 1920))
BACKGROUND_VOLUME_DB  = float(os.getenv("BACKGROUND_VOLUME_DB", -18))

# --- Fuente ---
FONT_PATH = ROOT / "fonts" / "Bebas_Neue" / "BebasNeue-Regular.ttf"