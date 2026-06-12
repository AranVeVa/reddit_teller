from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# Path config
FONT_SANS = "/usr/share/fonts/TTF/DejaVuSans.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
TEMPLATE_LIGHT = "/home/isael/Descargas/reddit-story.png"
TEMPLATE_DARK = "/home/isael/Descargas/reddit-story-dark.png"

def _load_font(font_path: str, size: int):
    try:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()

def wrap_text(text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        try:
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w, _ = font.getsize(test_line)
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
        lines = wrap_text(text, font, max_width)
        
        total_h = 0
        line_spacing = int(size * 0.25)
        for line in lines:
            try:
                bbox = font.getbbox(line)
                h = bbox[3] - bbox[1]
            except AttributeError:
                _, h = font.getsize(line)
            total_h += h + line_spacing
        if total_h > 0:
            total_h -= line_spacing
            
        if total_h <= max_height:
            return size, lines
        size -= 5
    font = _load_font(font_path, size)
    return size, wrap_text(text, font, max_width)

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
    total_h = 0
    line_spacing = int(font_size * 0.25)
    line_heights = []
    for line in lines:
        try:
            bbox = font_title.getbbox(line)
            lh = bbox[3] - bbox[1]
        except AttributeError:
            _, lh = font_title.getsize(line)
        line_heights.append(lh)
        total_h += lh + line_spacing
    if total_h > 0:
        total_h -= line_spacing

    start_y = 450 + (170 - total_h) // 2

    curr_y = start_y
    for i, line in enumerate(lines):
        draw.text((75, curr_y), line, font=font_title, fill=text_color)
        curr_y += line_heights[i] + line_spacing

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
        # 42% of screen width (slightly larger)
        card_w = int(video_w * 0.42)
        
    card_h = int(card_w / 1.775)
    resized_img = img.resize((card_w, card_h), Image.Resampling.LANCZOS)

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resized_img.save(output_path, "PNG")
    return output_path
