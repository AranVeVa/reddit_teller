import sys
import shutil
import textwrap

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def _color(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def success(msg: str) -> None:
    print(f"{_color('  ✔', GREEN)} {msg}")


def error(msg: str) -> None:
    print(f"{_color('  ✖', RED)} {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"{_color('  ➜', CYAN)} {msg}")


def warn(msg: str) -> None:
    print(f"{_color('  ⚠', YELLOW)} {msg}")


def header(title: str) -> None:
    # Limit width to terminal size but cap at 80 columns to avoid overflow
    term_width = shutil.get_terminal_size((80, 20)).columns
    width = min(term_width, 80)
    # Truncate title if too long for the box
    max_title_len = width - 4  # account for side borders + space
    if len(title) > max_title_len:
        title = title[:max_title_len]
    sep = "═" * (width - 2)  # side borders consume 2 chars
    box_top = f"╔{sep}╗"
    box_mid = f"║{title.center(width - 2)}║"
    box_bot = f"╚{sep}╝"
    print(_color(box_top, CYAN))
    print(f"{BOLD}{_color(box_mid, CYAN)}{RESET}")
    print(_color(box_bot, CYAN))


def prompt_str(prompt: str) -> str:
    return f"{BOLD}{CYAN}{prompt}{RESET}"


def visual_len(text: str) -> int:
    """Calculates the visual width of a string in the terminal, counting emojis as 2 columns."""
    length = 0
    for char in text:
        cp = ord(char)
        if (0x1F300 <= cp <= 0x1F9FF or 
            0x1FA70 <= cp <= 0x1FAFF or 
            0x2600 <= cp <= 0x27BF or
            0x1F000 <= cp <= 0x1F2FF):
            length += 2
        else:
            length += 1
    return length


def show_candidate(
    index: int,
    total: int,
    accepted: int,
    limit: int,
    subreddit: str,
    title: str,
    score: int,
    content: str
) -> None:
    """Prints a candidate story in a simple, fluent preview format."""
    print(f"{_color('  ➜', CYAN)} [{index}] {BOLD}{title}{RESET} (score: {score})")
    print(f"{_color('  ➜', CYAN)} Content:")
    print(content)