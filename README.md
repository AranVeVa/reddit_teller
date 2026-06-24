# 🎙️ reddit_teller

> Automated pipeline to turn Reddit stories into short horror videos — with AI-generated scenes, animated cards, narration, and subtitles.

---

## ✨ What it does

1. **Fetches** posts from any subreddit (hot / new / top)
2. **Lets you review & edit** each story before processing
3. **Narrates** the text via ElevenLabs TTS
4. **Mixes** narration with background music
5. **Generates** AI scene images with OpenAI (`gpt-image-1` / `dall-e-3`) using a consistent *dark papercraft horror* visual style
6. **Animates** scenes with Ken Burns effect + cross-dissolve transitions
7. **Overlays** an animated Reddit card (light or dark mode) with bounce + SFX
8. **Burns subtitles** (via Whisper) into the final video
9. **Exports** a ready-to-upload `.mp4` — vertical (9:16) or horizontal

---

## 🗂️ Project structure

```
reddit_teller/
├── scripts/
│   ├── main.py             # Entry point — full interactive pipeline
│   ├── reddit.py           # Fetch & filter Reddit posts (PRAW)
│   ├── voice.py            # ElevenLabs TTS narration
│   ├── audio_mixer.py      # Mix narration + background music
│   ├── reddit_card.py      # Generate animated Reddit post cards
│   ├── card_sfx.py         # Sound effects for card animations
│   ├── scene_generator.py  # GPT-4o scene analysis + image generation
│   ├── scene_video.py      # Ken Burns + dissolve clip builder
│   ├── video.py            # Final video compositor (MoviePy)
│   ├── subtitles.py        # Whisper transcription → SRT
│   └── termui.py           # Terminal UI helpers
├── config.py               # Paths, env vars, video dimensions
├── assets/
│   ├── Redditcards/        # Reddit card templates (light + dark)
│   └── Sfx/                # Card land/exit sound effects
├── background_videos/      # Video loops for classic mode
├── background_audio/       # Background music tracks
├── fonts/                  # Custom fonts
└── outputs/                # Generated audios, videos, subtitles
```

---

## ⚙️ Setup

### 1. Clone & create virtual environment

```bash
git clone https://github.com/youruser/reddit_teller.git
cd reddit_teller
python -m venv reddit-env
source reddit-env/bin/activate
pip install -r requirements.txt
```

### 2. Install system dependencies

```bash
# FFmpeg (required by MoviePy & Whisper)
sudo apt install ffmpeg

# Fonts for Reddit cards
sudo apt install fonts-dejavu fonts-noto-color-emoji
```

### 3. Configure `.env`

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

```ini
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=reddit_teller

# ElevenLabs (comma-separated keys for rotation)
ELEVENLABS_API_KEYS=key1,key2
ELEVENLABS_VOICE_ID=your_voice_id
ELEVENLABS_SPEED=1.1

# OpenAI (for scene images)
OPENAI_API_KEY=your_openai_key

# Video dimensions (default: 1080x1920 vertical)
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920

# Background files
BACKGROUND_AUDIO=background_audio/your_track.mp3
BACKGROUND_VIDEO=background_videos/your_loop.mp4
```

### 4. Add required assets

Place the following files in `assets/Redditcards/`:
- `reddit-story.png` — light mode card template
- `reddit-story-dark.png` — dark mode card template

---

## 🚀 Usage

### Interactive mode (recommended)

```bash
python scripts/main.py
```

The pipeline will guide you through each step interactively.

### CLI flags (fully automated)

```bash
python scripts/main.py \
  --subreddit nosleep \
  --limit 1 \
  --duration 1 \
  --order hot \
  --scenes \
  --subs \
  --dark-mode \
  --yes
```

| Flag | Description |
|---|---|
| `--subreddit`, `-s` | Subreddit name or URL |
| `--limit`, `-l` | Number of stories to include |
| `--duration`, `-d` | `1` Shorts ~60s · `2` ~3min · `3` ~5min · `4` ~10min · `5` custom |
| `--order`, `-o` | `hot` / `new` / `top` |
| `--scenes` / `--no-scenes` | AI-generated scenes or classic video background |
| `--subs` / `--no-subs` | Burn subtitles into the video |
| `--dark-mode` / `--light-mode` | Reddit card theme |
| `--words-per-card`, `-w` | Words per subtitle card |
| `--start-sec` | Start second for classic background video |
| `--yes`, `-y` | Auto-approve all prompts |

### Generate scenes only

```bash
python scripts/scene_generator.py <story_id>
python scripts/scene_generator.py <story_id> --model dall-e-3
```

---

## 🎬 Video modes

### 🤖 AI Scenes mode (`--scenes`)
- GPT-4o analyzes the story and creates a **visual bible** + scene breakdown
- Each scene is rendered as an image (`gpt-image-1` or `dall-e-3`)
- Images are animated with **Ken Burns** effect and **cross-dissolve** transitions
- Scene count scales with story duration (4–5 scenes for ~60s, up to 9–10 for longer)

### 🎮 Classic mode (`--no-scenes`)
- Uses a looping background gameplay video
- Lighter, faster, no OpenAI usage

---

## 🧩 Dependencies

| Package | Purpose |
|---|---|
| `praw` | Reddit API |
| `moviepy` | Video editing & compositing |
| `openai-whisper` | Speech-to-text for subtitles |
| `requests` | OpenAI image/chat API calls |
| `python-dotenv` | Environment variable loading |
| `Pillow` | Reddit card image generation |

---

## 📄 License

MIT
