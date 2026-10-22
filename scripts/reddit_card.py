from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import unicodedata

_ASSETS = Path(__file__).parent.parent / "assets" / "Redditcards"

def _resolve_font(*candidates: str) -> str:
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0] if candidates else ""

# Path config (Linux, Windows fallback)
FONT_SANS = _resolve_font(
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf"
)
FONT_SANS_BOLD = _resolve_font(
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf"
)
FONT_EMOJI = _resolve_font(
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "C:/Windows/Fonts/seguiemj.ttf"
)
TEMPLATE_LIGHT = str(_ASSETS / "reddit-story.png")
TEMPLATE_DARK  = str(_ASSETS / "reddit-story-dark.png")

def is_emoji(char):
    cp = ord(char)
    if (0x1F300 <= cp <= 0x1F9FF or 
        0x1FA70 <= cp <= 0x1FAFF or 
        0x2600 <= cp <= 0x27BF or
        0x1F000 <= cp <= 0x1F2FF or
        cp == 0x200d):
        return True
    cat = unicodedata.category(char)
    if cat == "So":
        return True
    return False

def split_text_and_emojis(text):
    runs = []
    current_run = ""
    current_is_emoji = None
    for char in text:
        char_is_emoji = is_emoji(char)
        if current_is_emoji is None:
            current_is_emoji = char_is_emoji
            current_run = char
        elif current_is_emoji == char_is_emoji:
            current_run += char
        else:
            runs.append((current_run, current_is_emoji))
            current_run = char
            current_is_emoji = char_is_emoji
    if current_run:
        runs.append((current_run, current_is_emoji))
    return runs

def get_text_width(text, font, font_size):
    runs = split_text_and_emojis(text)
    w = 0
    for run_text, is_emo in runs:
        if is_emo:
            for char in run_text:
                if char != "\u200d":
                    w += int(font_size * 1.1)
        else:
            try:
                bbox = font.getbbox(run_text)
                w += bbox[2] - bbox[0]
            except AttributeError:
                w += font.getsize(run_text)[0]
    return w

def draw_text_with_emojis(draw, img, xy, text, font, font_size, emoji_font_path, text_color):
    runs = split_text_and_emojis(text)
    x, y = xy
    font_emoji = None
    if os.path.exists(emoji_font_path):
        try:
            font_emoji = ImageFont.truetype(emoji_font_path, 109)
        except Exception:
            pass
    for run_text, is_emo in runs:
        if is_emo and font_emoji:
            for char in run_text:
                if char == "\u200d":
                    continue
                try:
                    emoji_img = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
                    emoji_draw = ImageDraw.Draw(emoji_img)
                    emoji_draw.text((10, 10), char, font=font_emoji, fill=(255, 255, 255, 255), embedded_color=True)
                    target_w = int(font_size * 1.1)
                    target_h = int(font_size * 1.1)
                    emoji_scaled = emoji_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    paste_y = y - int(font_size * 0.05)
                    img.alpha_composite(emoji_scaled, (x, paste_y))
                    x += int(font_size * 1.1)
                except Exception:
                    draw.text((x, y), char, font=font, fill=text_color)
                    try:
                        bbox = font.getbbox(char)
                        w = bbox[2] - bbox[0]
                    except AttributeError:
                        w = font.getsize(char)[0]
                    x += w
        else:
            draw.text((x, y), run_text, font=font, fill=text_color)
            try:
                bbox = font.getbbox(run_text)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w = font.getsize(run_text)[0]
            x += w

def _load_font(font_path: str, size: int):
    try:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()

def wrap_text(text: str, font, font_size: int, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        w = get_text_width(test_line, font, font_size)
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def find_optimum_font_size(text: str, font_path: str, max_width: int, max_height: int, start_size: int = 75) -> tuple[int, list[str]]:
    size = start_size
    while size > 25:
        font = _load_font(font_path, size)
        lines = wrap_text(text, font, size, max_width)
        
        try:
            line_h = font.getbbox("Ag")[3] - font.getbbox("Ag")[1]
        except AttributeError:
            _, line_h = font.getsize("Ag")
            
        line_spacing = int(size * 0.25)
        total_h = len(lines) * line_h + (len(lines) - 1) * line_spacing
            
        if total_h <= max_height:
            return size, lines
        size -= 5
    font = _load_font(font_path, size)
    return size, wrap_text(text, font, size, max_width)

def generate_reddit_card(
    subreddit: str,
    title: str,
    score: int,
    video_w: int,
    video_h: int,
    output_path: Path,
    dark_mode: bool = False
) -> Path:
    """
    Generates a beautiful Reddit post card using the selected template (light/dark).
    Overwrites the text dynamically, and resizes the final card to fit nicely on screen.
    """
    # 1. Select Template & Color palette
    if dark_mode:
        template_path = TEMPLATE_DARK
        cover_color = (14, 17, 19, 255)       # Reddit dark card background
        text_color = (242, 244, 245, 255)     # White text
        footer_color = (129, 131, 132, 255)   # Light gray text for footer stats
    else:
        template_path = TEMPLATE_LIGHT
        cover_color = (255, 255, 255, 255)     # White card background
        text_color = (26, 26, 27, 255)        # Dark charcoal text
        footer_color = (135, 138, 140, 255)   # Medium gray text for footer stats
        
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template image not found at: {template_path}")
        
    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 2. Clear old texts with rectangles matching the selected background color
    # Subreddit area
    draw.rectangle([(300, 220), (1600, 420)], fill=cover_color)
    # Title area
    draw.rectangle([(70, 450), (1590, 630)], fill=cover_color)
    # Upvotes count area
    draw.rectangle([(190, 640), (450, 790)], fill=cover_color)
    # Comments count area
    draw.rectangle([(570, 640), (1200, 790)], fill=cover_color)

    # 3. Load Fonts
    font_sub = _load_font(FONT_SANS_BOLD, 65)
    font_footer = _load_font(FONT_SANS_BOLD, 60)

    # 4. Draw Subreddit name
    draw.text((330, 270), f"r/{subreddit}", font=font_sub, fill=text_color)

    # 5. Draw Title (wrapped and dynamically resized to prevent overlap)
    # We restrict vertical height to 160px so it fits completely in the 450-630 slot
    font_size, lines = find_optimum_font_size(title, FONT_SANS_BOLD, 1450, 160, start_size=75)
    font_title = _load_font(FONT_SANS_BOLD, font_size)

    # Vertically center the lines in the 170px slot (y=450 to y=620)
    try:
        line_h = font_title.getbbox("Ag")[3] - font_title.getbbox("Ag")[1]
    except AttributeError:
        _, line_h = font_title.getsize("Ag")
        
    line_spacing = int(font_size * 0.25)
    total_h = len(lines) * line_h + (len(lines) - 1) * line_spacing

    start_y = 450 + (170 - total_h) // 2

    curr_y = start_y
    for line in lines:
        draw_text_with_emojis(
            draw, 
            img, 
            (75, curr_y), 
            line, 
            font_title, 
            font_size, 
            FONT_EMOJI, 
            text_color
        )
        curr_y += line_h + line_spacing

    # 6. Draw Footer stats
    score_str = f"{score}"
    if score > 1000:
        score_str = f"{score/1000:.1f}k"
    draw.text((200, 665), f"{score_str}+", font=font_footer, fill=footer_color)

    comments_count = max(5, int(score * 0.15))
    comments_str = f"{comments_count}"
    if comments_count > 1000:
        comments_str = f"{comments_count/1000:.1f}k"
    draw.text((580, 665), f"{comments_str}+", font=font_footer, fill=footer_color)

    # 7. Resize the card to fit nicely on the target video
    # Card is horizontal, aspect ratio: 1662 / 936 = 1.775
    is_vertical = video_w < video_h
    if is_vertical:
        # 72% of screen width (slightly larger)
        card_w = int(video_w * 0.72)
    else:
        # 34% of screen width (20% smaller than 42%)
        card_w = int(video_w * 0.34)
        
    card_h = int(card_w / 1.775)
    resized_img = img.resize((card_w, card_h), Image.Resampling.LANCZOS)

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resized_img.save(output_path, "PNG")
    return output_path
