"""Dependency-free terminal colors and layout helpers for LordVault.

Importing this module does not change the console. Call ``init_terminal``
explicitly before using ANSI output on Windows.
"""

import os
import re
import shutil
import sys
import unicodedata


RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
PURPLE = "\x1b[38;5;141m"
CYAN = "\x1b[38;5;87m"
PINK = "\x1b[38;5;212m"
GOLD = "\x1b[38;5;221m"
GREEN = "\x1b[38;5;120m"
RED = "\x1b[38;5;203m"
WHITE = "\x1b[38;5;255m"
MUTED = "\x1b[38;5;246m"
BORDER = "\x1b[38;5;60m"
SELECT_BG = "\x1b[48;5;24m"

# CSI colors/cursor commands, OSC titles/links, string commands, and short ESCs.
ANSI_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\].*?(?:\x07|\x1b\\)|"
    r"[PX^_].*?\x1b\\|[@-_])",
    re.DOTALL,
)


def strip_ansi(text):
    """Return text with terminal escape sequences removed."""
    return ANSI_RE.sub("", str(text))


def _cell_width(character):
    if unicodedata.category(character) in ("Mn", "Me", "Cf", "Cc", "Cs"):
        return 0
    if unicodedata.combining(character):
        return 0
    return 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1


def visible_width(text):
    """Count terminal cells, excluding ANSI escapes and combining marks.

    Intended for single-line labels. East Asian wide/full-width characters
    occupy two cells; control characters do not add a printable cell.
    """
    return sum(_cell_width(character) for character in strip_ansi(text))


def fit(text, width, align="left"):
    """Pad or ellipsize a label to exactly ``width`` terminal cells.

    Existing ANSI sequences stay intact. Truncated styled text receives a
    reset, and neither a wide character nor its combining marks is split.
    ``align`` accepts ``left``, ``center``, or ``right``.
    """
    if align not in ("left", "center", "right"):
        raise ValueError("align must be 'left', 'center', or 'right'")
    width = max(0, int(width))
    if width == 0:
        return ""
    text = str(text)
    text_width = visible_width(text)
    if text_width > width:
        budget = width - 1
        parts = []
        used = 0
        position = 0
        styled = False
        while position < len(text):
            escape = ANSI_RE.match(text, position)
            if escape:
                parts.append(escape.group())
                styled = True
                position = escape.end()
                continue
            character = text[position]
            cells = _cell_width(character)
            if used + cells > budget:
                break
            parts.append(character)
            used += cells
            position += 1
        parts.append("…")
        if styled:
            parts.append(RESET)
        text = "".join(parts)
        text_width = used + 1
    padding = width - text_width
    if align == "right":
        return " " * padding + text
    if align == "center":
        left_padding = padding // 2
        return " " * left_padding + text + " " * (padding - left_padding)
    return text + " " * padding


_GRADIENT_COLORS = (141, 177, 213, 212, 207, 171, 135, 99, 75, 81, 87, 123)


def gradient(text, phase=0):
    """Apply an animated violet/pink/cyan gradient in compact color bands.

    Increment ``phase`` between frames to move the bands. Existing colors are
    removed first; each band uses one escape sequence, not one per character.
    """
    text = strip_ansi(text)
    if not text:
        return ""
    parts = []
    previous_color = None
    column = int(phase)
    for character in text:
        color = _GRADIENT_COLORS[(column // 4) % len(_GRADIENT_COLORS)]
        if color != previous_color:
            parts.append("\x1b[38;5;{}m".format(color))
            previous_color = color
        parts.append(character)
        column += _cell_width(character)
    parts.append(RESET)
    return "".join(parts)


def terminal_size():
    """Return the current console size as ``(columns, lines)``."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return max(1, size.columns), max(1, size.lines)


def _stdout_is_terminal():
    try:
        return bool(sys.stdout.isatty())
    except (AttributeError, OSError, ValueError):
        return False


def _windows_console():
    """Read the stdout console handle/mode without changing console state."""
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetStdHandle.argtypes = (wintypes.DWORD,)
        kernel32.GetStdHandle.restype = wintypes.HANDLE
        kernel32.GetConsoleMode.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        )
        kernel32.GetConsoleMode.restype = wintypes.BOOL
        kernel32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel32.SetConsoleMode.restype = wintypes.BOOL
        handle = kernel32.GetStdHandle(wintypes.DWORD(-11))
        mode = wintypes.DWORD()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return None
        return kernel32, handle, mode.value
    except (AttributeError, OSError, ValueError):
        return None


def supports_ansi():
    """Check ANSI support without enabling it or invoking a shell."""
    if not _stdout_is_terminal() or os.environ.get("TERM", "").lower() == "dumb":
        return False
    if os.name != "nt":
        return True
    console = _windows_console()
    return bool(console and console[2] & 0x0004)


def init_terminal():
    """Enable Windows virtual-terminal output when possible; return success.

    Redirected output and TERM=dumb stay plain. No shell command is executed,
    and callers can use the returned boolean to choose a plain-text fallback.
    """
    if not _stdout_is_terminal() or os.environ.get("TERM", "").lower() == "dumb":
        return False
    if os.name != "nt":
        return True
    console = _windows_console()
    if not console:
        return False
    kernel32, handle, mode = console
    if mode & 0x0004:
        return True
    return bool(kernel32.SetConsoleMode(handle, mode | 0x0001 | 0x0004))


# A compact five-line wordmark, 53 cells wide: LORDVAULT.
_BANNER_GLYPHS = (
    ("█    ", "█    ", "█    ", "█    ", "█████"),
    (" ███ ", "█   █", "█   █", "█   █", " ███ "),
    ("████ ", "█   █", "████ ", "█  █ ", "█   █"),
    ("████ ", "█   █", "█   █", "█   █", "████ "),
    ("█   █", "█   █", "█   █", " █ █ ", "  █  "),
    (" ███ ", "█   █", "█████", "█   █", "█   █"),
    ("█   █", "█   █", "█   █", "█   █", " ███ "),
    ("█    ", "█    ", "█    ", "█    ", "█████"),
    ("█████", "  █  ", "  █  ", "  █  ", "  █  "),
)
BANNER_ROWS = tuple(
    " ".join(glyph[row] for glyph in _BANNER_GLYPHS) for row in range(5)
)
