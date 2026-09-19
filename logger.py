"""
LordVault — Terminal Logger
Clean, thread-safe, anti-spam logging with premium ANSI styling.
"""

import sys
import os
import threading
from datetime import datetime
import lv_theme as theme

# ── Windows UTF-8 ─────────────────────────────────────────────────────────────
if os.name == 'nt':
    os.system('chcp 65001 >nul 2>&1')
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

_print_lock = threading.Lock()

# ══════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE  (ANSI 256-colour)
# ══════════════════════════════════════════════════════════════════════════════
bold    = theme.BOLD
reset   = theme.RESET
gray    = theme.MUTED
dark    = theme.BORDER
cyan    = theme.CYAN
green   = theme.GREEN
yellow  = theme.GOLD
red     = theme.RED
white   = theme.WHITE
magenta = theme.PINK
purple  = theme.PURPLE
gold    = theme.GOLD
amber   = '\033[1;38;5;214m'

# Short aliases (kept for compatibility with binary modules)
R    = reset
B_   = bold
D    = gray
bGRN = green
bRED = red
bYEL = yellow
bCYN = cyan
bWHT = white
bMAG = magenta
GRN  = green
RED  = red
YEL  = yellow
CYN  = cyan
WHT  = white
ORG  = gold

# Gradient colours (magenta → cyan)
_GRAD = [
    '\033[38;5;201m',
    '\033[38;5;171m',
    '\033[38;5;141m',
    '\033[38;5;111m',
    '\033[38;5;81m',
    '\033[38;5;51m',
]

def _gradient(text):
    if not text:
        return ''
    return theme.gradient(text)

# ══════════════════════════════════════════════════════════════════════════════
# BADGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
BADGES = {
    'INFO':    (cyan,    'INFO     '),
    'OK':      (green,   'SUCCESS  '),
    'SUCCESS': (green,   'SUCCESS  '),
    'WARN':    (yellow,  'WARN     '),
    'ERR':     (red,     'ERROR    '),
    'ERROR':   (red,     'ERROR    '),
    'DBG':     (gray,    'SETUP    '),
    'DEBUG':   (gray,    'DEBUG    '),
    'READY':   (purple,  'READY    '),
    'CAPTCHA': (gold,    'CAPTCHA  '),
    'CODE':    (green,   'REWARD   '),
    'ASK':     (yellow,  'PROMPT   '),
}

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def masktoken(token):
    """Truncate a token for safe display."""
    if not token:
        return ''
    s = str(token)
    return s[:20] + '...' if len(s) > 20 else s

# ══════════════════════════════════════════════════════════════════════════════
# CORE PRINT
# ══════════════════════════════════════════════════════════════════════════════

def _print(tag, tag_color, message, detail=None):
    """Format and emit a single log line."""
    ts = datetime.now().strftime('%H:%M:%S')

    tag_clean = str(tag).strip().upper()
    if tag_clean in BADGES:
        tcolor, label = BADGES[tag_clean]
    else:
        tcolor = tag_color or cyan
        label  = f"{tag:<9}"

    time_part = f"{gray}[{ts}]{reset}"
    badge     = f"{tcolor}{bold}{label}{reset}"
    sep       = f"{dark}│{reset}"
    msg_part  = str(message)

    line = f"   {time_part}  {badge} {sep} {white}{msg_part}{reset}"
    if detail:
        line += f"  {gray}({detail}){reset}"

    with _print_lock:
        sys.stdout.write(line + '\n')
        sys.stdout.flush()

# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC LOG FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def info(token, message=None, detail=None):
    if message is None:
        message, token = token, ''
    _print('INFO', cyan, message, detail)

def success(token, message=None, detail=None):
    if message is None:
        message, token = token, ''
    _print('OK', green, message, detail)

def warning(token, message=None, detail=None):
    if message is None:
        message, token = token, ''
    _print('WARN', yellow, message, detail)

def error(token, message=None, detail=None):
    if message is None:
        message, token = token, ''
    _print('ERR', red, message, detail)

def debug(token, message=None, detail=None):
    if message is None:
        message, token = token, ''
    _print('DBG', gray, message, detail)

def captcha(token, message=None, detail=None):
    if message is None:
        message, token = token, ''
    _print('CAPTCHA', gold, message, detail)

def code(token, reward_code):
    _print('CODE', green, f"Reward Code: {bold}{reward_code}{reset}")

def login_ok(token_short):
    _print('OK', green, f"Session verified for {bold}{token_short}{reset}")

def login_fail(token_short, reason=''):
    _print('ERR', red, f"Auth failed for {token_short}", reason)

# ══════════════════════════════════════════════════════════════════════════════
# STRUCTURED OUTPUT COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

_BOX_W = 60

def _box_width():
    return max(8, min(_BOX_W, theme.terminal_size()[0] - 6))

def _card_row(text, width):
    print(f"   {dark}│{reset}{theme.fit(text, width)}{dark}│{reset}")

def config_box(rows):
    """Render a rounded configuration card."""
    width = _box_width()
    with _print_lock:
        print()
        print(f"   {dark}╭{'─' * width}╮{reset}")
        hdr = 'CONFIGURATION' if width >= 15 else 'SETUP'
        _card_row(_gradient(hdr.center(width)), width)
        print(f"   {dark}├{'─' * width}┤{reset}")
        for key, val in rows:
            key_width = min(12, max(3, width // 3))
            k = theme.fit(str(key), key_width)
            _card_row(f"  {cyan}{k}{reset} {dark}│{reset} {white}{val}{reset}", width)
        print(f"   {dark}╰{'─' * width}╯{reset}")
        print()
        sys.stdout.flush()

def section(title):
    """Print a named section divider."""
    with _print_lock:
        print()
        content = f"{purple}━━{reset} {bold}{white}{title}{reset} {cyan}━━{reset}"
        print(f"   {theme.fit(content, _box_width())}")
        print()
        sys.stdout.flush()

def divider():
    """Print a thin horizontal rule."""
    with _print_lock:
        print(f"   {dark}{'─' * _box_width()}{reset}")
        sys.stdout.flush()

def summary(title, total, success_count, failed_count):
    """Print a results summary card."""
    w = _box_width()
    with _print_lock:
        print()
        print(f"   {dark}╭{'─' * w}╮{reset}")
        _card_row(_gradient(str(title).center(w)), w)
        print(f"   {dark}├{'─' * w}┤{reset}")
        def _row(icon, col, label, count):
            c_str = str(count)
            label_width = min(12, max(3, w // 3))
            text = (
                f"  {col}{icon} {theme.fit(label, label_width)}{reset}"
                f" {dark}│{reset} {bold}{white}{c_str}{reset} accounts"
            )
            _card_row(text, w)
        _row('+', green, 'Successful',  success_count)
        _row('x', red,   'Failed',      failed_count)
        _row('=', cyan,  'Total',       total)
        print(f"   {dark}╰{'─' * w}╯{reset}")
        print()
        sys.stdout.flush()

# ══════════════════════════════════════════════════════════════════════════════
# BANNER  (matches ui.py v5.0)
# ══════════════════════════════════════════════════════════════════════════════

_BANNER_ROWS = theme.BANNER_ROWS

def print_banner():
    """Print the LordVault gradient banner with info rows."""
    wrapped_banner = getattr(sys.stdout, '_print_lord_vault_banner', None)
    if callable(wrapped_banner):
        with _print_lock:
            wrapped_banner()
        return
    width = _box_width()
    rows = _BANNER_ROWS if width >= max(map(theme.visible_width, _BANNER_ROWS)) else ['LordVault']
    with _print_lock:
        print()
        print(f"   {dark}╭{'─' * width}╮{reset}")
        for i, row in enumerate(rows):
            _card_row(theme.gradient(row.center(width), i), width)
        print(f"   {dark}╰{'─' * width}╯{reset}")
        print()
        for line in (
            f"{cyan}LORDVAULT{reset}  {gray}/  TERMINAL WORKSPACE{reset}",
            f"{gray}Support  {cyan}https://discord.gg/lord-vault{reset}",
            f"{gray}Built by {white}LordVault Team{reset}",
        ):
            print(f"   {theme.fit(line, width)}")
        print()
        sys.stdout.flush()
