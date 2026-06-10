import sys
import time
import shutil

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def _color(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def success(msg: str) -> None:
    print(f"{_color('[OK]', GREEN)} {msg}")


def error(msg: str) -> None:
    print(f"{_color('[ERR]', RED)} {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"{_color('[..]', CYAN)} {msg}")


def warn(msg: str) -> None:
    print(f"{_color('[!]', YELLOW)} {msg}")


def header(title: str) -> None:
    width = shutil.get_terminal_size((80, 20)).columns
    sep = "=" * width
    print(sep)
    print(f"{BOLD}{title.center(width)}{RESET}")
    print(sep)


def prompt_str(prompt: str) -> str:
    return f"{BOLD}{CYAN}{prompt}{RESET}"


def progress_bar(completed: int, total: int, width: int = 30) -> str:
    if total <= 0:
        return ""
    ratio = min(max(completed / total, 0.0), 1.0)
    fill = int(ratio * width)
    bar = "█" * fill + "-" * (width - fill)
    percent = int(ratio * 100)
    return f"[{bar}] {percent}%"


class Status:
    def __init__(self, total_steps: int):
        self.total = max(1, int(total_steps))
        self.done = 0
        self.start = time.time()

    def update(self, step: int = 1, message: str | None = None) -> None:
        self.done = min(self.done + int(step), self.total)
        elapsed = time.time() - self.start
        rate = (self.done / max(1, elapsed)) if elapsed > 0 else 0
        remaining_steps = max(0, self.total - self.done)
        eta = int(remaining_steps / rate) if rate > 0 else 0
        bar = progress_bar(self.done, self.total)
        msg = f"{bar} {self.done}/{self.total}"
        if message:
            msg += f" — {message}"
        msg += f" (ETA: {eta}s)"
        print(msg)
