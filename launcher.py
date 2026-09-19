"""
LordVault — Runtime Output Wrapper
Intercepts stdout + input to match the LordVault terminal aesthetic:
  ▸ Shared gradient banner and adaptive rounded panels
  ▸ Braille-spinner progress bar for token validation
  ▸ Unified badge rows: [HH:MM:SS]  BADGE │ message
  ▸ CONFIG card with text labels, rounded border, gradient header
  ▸ PROMPT matching the ui.py  ╰─ ❯  style
"""

import sys
import os
import re
import builtins
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

# Force UTF-8 on Windows text file opens to prevent charmap/cp1252 decode errors
_orig_builtin_open = builtins.open
def _safe_open(file, mode='r', *args, **kwargs):
    if 'b' not in mode and 'encoding' not in kwargs:
        kwargs['encoding'] = 'utf-8'
        kwargs.setdefault('errors', 'replace')
    return _orig_builtin_open(file, mode, *args, **kwargs)
builtins.open = _safe_open

# ══════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE  — identical to ui.py
# ══════════════════════════════════════════════════════════════════════════════
RS  = theme.RESET
BD  = theme.BOLD
DM  = theme.DIM

P   = theme.PURPLE
LP  = '\033[38;5;177m'
MP  = theme.PINK
CY  = theme.CYAN
LB  = '\033[38;5;117m'
GD  = theme.GOLD
AM  = '\033[38;5;214m'
GR  = theme.GREEN
LG  = '\033[38;5;120m'
RD  = theme.RED
WH  = theme.WHITE
BWH = BD + WH
GY  = theme.MUTED
DG  = theme.BORDER

GRAD = [
    '\033[38;5;201m',
    '\033[38;5;171m',
    '\033[38;5;141m',
    '\033[38;5;111m',
    '\033[38;5;81m',
    '\033[38;5;51m',
]

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
W      = 68
INDENT = '   '

_ANSI = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')

def _vlen(s):
    return theme.visible_width(s)

def _fill(inner, width=W):
    return inner + ' ' * max(0, width - _vlen(inner))

def gradient(text):
    return theme.gradient(text)

def _panel_width(preferred):
    return max(8, min(preferred, theme.terminal_size()[0] - len(INDENT) - 3))

# ══════════════════════════════════════════════════════════════════════════════
# LOG LINE REGEX
# ══════════════════════════════════════════════════════════════════════════════
LOG_RE = re.compile(r'^(\d{2}:\d{2}:\d{2})\s+([A-Z_]+)\s+(.*)$')

# ══════════════════════════════════════════════════════════════════════════════
# BADGE MAP
# ══════════════════════════════════════════════════════════════════════════════
BADGE = {
    'INFO':    (CY,  'INFO     '),
    'OK':      (GR,  'OK       '),
    'SUCCESS': (GR,  'SUCCESS  '),
    'WARN':    (AM,  'WARN     '),
    'WARNING': (AM,  'WARN     '),
    'ERR':     (RD,  'ERROR    '),
    'ERROR':   (RD,  'ERROR    '),
    'DBG':     (GY,  'DEBUG    '),
    'CAPTCHA': (GD,  'CAPTCHA  '),
    'CODE':    (LG,  'REWARD   '),
    'SKIP':    (GY,  'SKIP     '),
    'ORBS':    (MP,  'ORBS     '),
    'DONE':    (GD,  'DONE     '),
    'FAIL':    (RD,  'FAIL     '),
}

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG CARD
# ══════════════════════════════════════════════════════════════════════════════
CFG_ICONS = {
    'Invite': '+',
    'Voice':  '~',
    'Text':   '>',
    'React':  '*',
    'VC':     '~',
    'Chat':   '>',
    'Reacts': '*',
    'Orbs':   'o',
}
CFG_W = 56

def _cfg_row(orig, key, val, width=None):
    width = _panel_width(CFG_W) if width is None else width
    icon  = CFG_ICONS.get(key, '+')
    key_s = f"{CY}{BD}{icon} {theme.fit(str(key), 7)}{RS}"
    sep   = f"{DG}│{RS}"
    val_s = str(val).strip()
    inner = f" {key_s} {sep} {WH}{val_s}{RS}"
    orig.write(f"{INDENT}{DG}│{RS}{theme.fit(inner, width)}{DG}│{RS}\n")

def flush_cfg_card(orig, rows):
    """Render buffered DBG rows as a rounded config card."""
    if not rows:
        return
    # Ensure Orbs row is displayed in the config card
    if not any(k == 'Orbs' for k, _ in rows):
        try:
            cfg_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input', 'config.json')
            with open(cfg_p, 'r', encoding='utf-8') as cf:
                import json
                _c = json.load(cf)
            _oc = _c.get('orb_claimer', {})
            _en = 'auto=y' if _oc.get('enabled', True) else 'auto=n'
            _th = _oc.get('threads', 3)
            rows.append(('Orbs', f"{_en}  threads={_th}"))
        except Exception:
            rows.append(('Orbs', 'auto=y  threads=3'))

    width = _panel_width(CFG_W)
    label = ' CONFIGURATION ' if width >= 17 else ' SETUP '
    half  = (width - len(label)) // 2
    extra = (width - len(label)) % 2
    hdr   = f"{'─' * half}{gradient(label)}{DG}{'─' * (half + extra)}"
    orig.write('\n')
    orig.write(f"{INDENT}{DG}╭{hdr}{DG}╮{RS}\n")
    for k, v in rows:
        _cfg_row(orig, k, v, width)
    orig.write(f"{INDENT}{DG}╰{'─' * width}╯{RS}\n\n")
    orig.flush()

# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION PROGRESS BAR
# ══════════════════════════════════════════════════════════════════════════════
_SPINNERS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
BAR_W = 22

_BATCH_OK   = {'OK', 'SUCCESS'}
_BATCH_WARN = {'WARN', 'WARNING'}
_BATCH_ERR  = {'ERR', 'ERROR'}
_BATCH_TAGS = _BATCH_OK | _BATCH_WARN | _BATCH_ERR

def _progress_line(ts, label, curr, tot, ok, warn, err, spin_idx):
    pct    = int(curr / max(tot, 1) * 100)
    width  = max(8, theme.terminal_size()[0] - len(INDENT) - 1)
    spin   = _SPINNERS[spin_idx % len(_SPINNERS)]
    counts = (
        f"{GR}{BD}OK {ok}{RS} "
        f"{AM}{BD}WARN {warn}{RS} "
        f"{RD}{BD}ERR {err}{RS}"
    )
    prefix = f"{GD}{spin}{RS} {CY}{BD}{label.strip()}{RS} "
    if width >= 90:
        prefix = f"{GY}[{ts}]{RS}  " + prefix
    suffix = f" {GD}{BD}{curr}/{tot}{RS} {GY}{pct}%{RS}  {counts}"
    bar_width = max(0, min(BAR_W, width - _vlen(prefix + suffix) - 2))
    filled = max(0, min(bar_width, int(curr / max(tot, 1) * bar_width)))
    bar = theme.gradient('━' * filled, spin_idx) + DG + '╌' * (bar_width - filled) + RS
    line = prefix + (f"[{bar}]" if bar_width else '') + suffix
    return f"\r{INDENT}{theme.fit(line, width)}{RS}"

# ══════════════════════════════════════════════════════════════════════════════
# BANNER INTERCEPT & RGB LORDVAULT BANNER
# ══════════════════════════════════════════════════════════════════════════════
RGB_GRAD = [
    '\033[38;5;196m',  # Red
    '\033[38;5;208m',  # Orange
    '\033[38;5;220m',  # Gold/Yellow
    '\033[38;5;82m',   # Green
    '\033[38;5;51m',   # Cyan
    '\033[38;5;129m',  # Purple
    '\033[38;5;201m',  # Magenta
]

_BANNER_CHARS = ('█', '╔', '╗', '╚', '╝', '╦', '╩', '╠', '╣', '╬')

_LORD_VAULT_BANNER_ROWS = theme.BANNER_ROWS


# ══════════════════════════════════════════════════════════════════════════════
# STREAM WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

class LordVaultStream:
    """Wraps stdout — unifies runtime logs with LordVault v5.0 aesthetics."""

    _REPLACEMENTS = [
        (bytes.fromhex('546f6f6c20487562').decode(), 'LordVault'),
        (bytes.fromhex('544f4f4c20485542').decode(), 'LordVault'),
        (bytes.fromhex('746f6f6c20687562').decode(), 'LordVault'),
        (bytes.fromhex('746f6f6c5f687562').decode(), 'LordVault'),
        (bytes.fromhex('546f6f6c487562').decode(), 'LordVault'),
        (bytes.fromhex('544f4f4c485542').decode(), 'LordVault'),
        (bytes.fromhex('746f6f6c687562').decode(), 'LordVault'),
        (bytes.fromhex('546f6f6c20487562205465616d').decode(), 'LordVault Team'),
        (bytes.fromhex('544f4f4c20485542205445414d').decode(), 'LordVault Team'),
        (bytes.fromhex('746f6f6c20687562207465616d').decode(), 'LordVault Team'),
        (bytes.fromhex('68747470733a2f2f646973636f72642e67672f746f6f6c687562').decode(), 'https://discord.gg/lord-vault'),
        (bytes.fromhex('68747470733a2f2f646973636f72642e67672f746f6f6c2d687562').decode(), 'https://discord.gg/lord-vault'),
    ]

    def __init__(self, original):
        self._o           = original
        self._dbg_buf     = []
        self._batch_total = 0
        self._batch_curr  = 0
        self._batch_ok    = 0
        self._batch_warn  = 0
        self._batch_err   = 0
        self._batch_spin  = 0
        self._batch_label = 'VERIFY'
        self._batch_ts    = ''
        self._in_progress = False
        self._banner_printed = False
        self._in_banner_block = False
        self._orbs_claimed_this_batch = False

    def _run_orbs_if_eligible(self):
        try:
            from quest_completer.quest_completer import sync_to_orbclaimer, auto_claim_orbs
            sync_to_orbclaimer()
            project_root = os.path.dirname(os.path.abspath(__file__))
            orb_file = os.path.join(project_root, 'orb_claimer', 'token.txt')
            if not os.path.exists(orb_file):
                return
            with open(orb_file, 'r', encoding='utf-8') as f:
                tokens = [l.strip() for l in f if l.strip()]
            if not tokens:
                return
            auto_claim_orbs()
        except Exception:
            pass

    def _print_lord_vault_banner(self):
        if self._banner_printed:
            return
        self._banner_printed = True
        width = _panel_width(W)
        rows = _LORD_VAULT_BANNER_ROWS if width >= max(map(_vlen, _LORD_VAULT_BANNER_ROWS)) else ['LordVault']
        self._o.write('\n')
        self._o.write(f"{INDENT}{DG}╭{'─' * width}╮{RS}\n")
        for i, row in enumerate(rows):
            centered = row.center(width)
            self._o.write(f"{INDENT}{DG}│{RS}{theme.gradient(centered, i)}{DG}│{RS}\n")
        self._o.write(f"{INDENT}{DG}╰{'─' * width}╯{RS}\n")
        self._o.write('\n')
        for line in (
            f"{CY}LORDVAULT{RS}  {GY}/  TERMINAL WORKSPACE{RS}",
            f"{GY}Support  {CY}https://discord.gg/lord-vault{RS}",
            f"{GY}Built by {WH}LordVault Team{RS}",
        ):
            self._o.write(f"{INDENT}{theme.fit(line, width)}\n")
        self._o.write('\n')
        self._o.flush()

    # ── Config card ───────────────────────────────────────────────────────────

    def flush_dbg_buffer(self):
        if self._dbg_buf:
            flush_cfg_card(self._o, self._dbg_buf)
            self._dbg_buf = []

    # ── Main write ────────────────────────────────────────────────────────────

    def write(self, text):
        if not text:
            return

        # Apply branding replacements
        text = re.sub(r'https?://discord\.gg/(?:tool[ _-]?hub|leak[ _-]?vault)\b', 'https://discord.gg/lord-vault', text, flags=re.IGNORECASE)
        for old, new in self._REPLACEMENTS:
            text = text.replace(old, new)
        text = re.sub(r'(?i)(?<![\w/-])(?:tool[ _-]?hub|leak[ _-]?vault|lord[ _]?vault)\b', 'LordVault', text)

        clean = _ANSI.sub('', text).strip()

        # Intercept and replace legacy banner from binary
        is_banner_art = any(ch in clean for ch in _BANNER_CHARS)
        is_banner_credit = ('»' in clean and any(w in clean for w in ('Support', 'Made by', 'Dev', 'Server')))
        is_banner = is_banner_art or is_banner_credit

        if is_banner:
            self._in_banner_block = True
            if not self._banner_printed:
                self._print_lord_vault_banner()
            return

        if self._in_banner_block:
            if not clean:
                return  # Skip empty spacing lines from the binary's banner block
            self._in_banner_block = False

        m = LOG_RE.match(clean)

        if not m:
            if 'Skipping Quest Completer for this batch' in clean:
                self._o.write(text)
                self._o.flush()
                if os.environ.get('ORB_CLAIMER_BATCH_ENABLED') == '1' and not self._orbs_claimed_this_batch:
                    self._orbs_claimed_this_batch = True
                    self._run_orbs_if_eligible()
                return
            # Flush config card before question-style lines
            if self._dbg_buf and ('?' in text or 'setup' in text or 'ASK' in text):
                self.flush_dbg_buffer()
            self._o.write(text)
            return

        ts, tag, msg = m.groups()

        # Intercept Quest skip notification to trigger Orbs Claimer if enabled & eligible
        if 'Skipping Quest Completer for this batch' in msg:
            self._o.write(
                f"{INDENT}{GY}[{ts}]{RS}  "
                f"{AM}{BD}WARN     {RS} "
                f"{DG}│{RS} "
                f"{WH}{msg}{RS}\n"
            )
            self._o.flush()
            if os.environ.get('ORB_CLAIMER_BATCH_ENABLED') == '1' and not self._orbs_claimed_this_batch:
                self._orbs_claimed_this_batch = True
                self._run_orbs_if_eligible()
            return

        # ── Validating N token(s) ─────────────────────────────────────────────
        vm = re.search(r'Validating\s+(\d+)\s+token', msg, re.IGNORECASE)
        if vm:
            self.flush_dbg_buffer()
            self._start_batch(int(vm.group(1)), 'VERIFY', ts)
            self._o.write(
                f"{INDENT}{GY}[{ts}]{RS}  "
                f"{CY}{BD}INFO     {RS} "
                f"{DG}│{RS} "
                f"{WH}Validating {GD}{BD}{self._batch_total}{RS} {WH}token(s)...{RS}\n"
            )
            return

        # ── Enrolling N tokens ────────────────────────────────────────────────
        em = re.search(r'Enrolling\s+(\d+)\s+token', msg, re.IGNORECASE)
        if em:
            self.flush_dbg_buffer()
            self._start_batch(int(em.group(1)), 'ENROLL', ts)
            self._o.write(
                f"{INDENT}{GY}[{ts}]{RS}  "
                f"{CY}{BD}INFO     {RS} "
                f"{DG}│{RS} "
                f"{WH}Enrolling {GD}{BD}{self._batch_total}{RS} {WH}token(s)...{RS}\n"
            )
            return

        # ── Valid: token (batch ok) ───────────────────────────────────────────
        if tag == 'OK' and msg.startswith('Valid:'):
            self._batch_ok   += 1
            self._batch_curr += 1
            self._batch_spin += 1
            self._batch_ts    = ts
            self._redraw_bar()
            return

        # ── During batch — count OK/WARN/ERR silently ─────────────────────────
        if self._in_progress and tag in _BATCH_TAGS:
            self._batch_curr += 1
            self._batch_spin += 1
            self._batch_ts    = ts
            if tag in _BATCH_OK:
                self._batch_ok   += 1
            elif tag in _BATCH_WARN:
                self._batch_warn += 1
            else:
                self._batch_err  += 1
            self._redraw_bar()
            return

        # ── Ready: master — batch complete ────────────────────────────────────
        if tag == 'OK' and 'Ready:' in msg:
            self.flush_dbg_buffer()
            self._end_batch(ts)
            rm = re.search(r'Ready:\s*(\S+).*?(\d+)\s+valid', msg)
            if rm:
                master, vcount = rm.groups()
                out = (
                    f"\r{INDENT}{GY}[{ts}]{RS}  "
                    f"{GR}{BD}READY    {RS} "
                    f"{DG}│{RS} "
                    f"{BWH}{vcount} Valid Tokens Ready{RS}  "
                    f"{DG}•{RS}  Master: {MP}{BD}{master}{RS}"
                    f"{' ' * 20}\n\n"
                )
            else:
                out = (
                    f"\r{INDENT}{GY}[{ts}]{RS}  "
                    f"{GR}{BD}READY    {RS} "
                    f"{DG}│{RS} {BWH}{msg}{RS}"
                    f"{' ' * 20}\n\n"
                )
            self._o.write(out)
            return

        # ── DBG — buffer into config card ─────────────────────────────────────
        if tag == 'DBG':
            parts = msg.split(None, 1)
            self._dbg_buf.append((parts[0], parts[1] if len(parts) > 1 else ''))
            return

        # ── End any active batch ──────────────────────────────────────────────
        if self._in_progress:
            self._end_batch(ts)

        # Flush any pending config card
        self.flush_dbg_buffer()

        # ── General log line ──────────────────────────────────────────────────
        bcol, blabel = BADGE.get(tag, (CY, f"{tag:<9}"))
        line = (
            f"{INDENT}{GY}[{ts}]{RS}  "
            f"{bcol}{BD}{blabel}{RS} "
            f"{DG}│{RS} "
            f"{WH}{msg}{RS}\n"
        )
        self._o.write(line)

    # ── Batch helpers ──────────────────────────────────────────────────────────

    def _start_batch(self, total, label, ts):
        self._batch_total = total
        self._batch_curr  = 0
        self._batch_ok    = 0
        self._batch_warn  = 0
        self._batch_err   = 0
        self._batch_spin  = 0
        self._batch_label = label
        self._batch_ts    = ts
        self._in_progress = True

    def _redraw_bar(self):
        line = _progress_line(
            self._batch_ts,
            self._batch_label,
            self._batch_curr,
            self._batch_total,
            self._batch_ok,
            self._batch_warn,
            self._batch_err,
            self._batch_spin,
        )
        self._o.write(line)
        self._o.flush()

    def _end_batch(self, ts):
        if not self._in_progress:
            return
        self._in_progress = False
        tot  = self._batch_total
        ok   = self._batch_ok
        warn = self._batch_warn
        err  = self._batch_err
        summary = (
            f"\r{INDENT}{GY}[{ts}]{RS}  "
            f"{GR}{BD}DONE     {RS} "
            f"{DG}│{RS}  "
            f"{GD}{BD}{tot}{RS} processed  "
            f"{GR}{BD}OK {ok}{RS}  "
            f"{AM}{BD}WARN {warn}{RS}  "
            f"{RD}{BD}ERR {err}{RS}"
            f"{' ' * 20}\n"
        )
        self._o.write(summary)
        self._o.flush()

    def flush(self):
        return self._o.flush()

    def __getattr__(self, name):
        return getattr(self._o, name)


# ══════════════════════════════════════════════════════════════════════════════
# INPUT HOOK  — matches LordVault  ╰─ ❯  prompt style with interactive y/n
# ══════════════════════════════════════════════════════════════════════════════
_orig_input = builtins.input

def interactive_yn(label, default='n'):
    """Interactive y / n prompt with arrow-key / y / n selection design."""
    if hasattr(sys.stdout, 'flush_dbg_buffer'):
        sys.stdout.flush_dbg_buffer()

    clean_label = _ANSI.sub('', label).strip()

    # Fallback to standard input if not a TTY or msvcrt unavailable
    if not (sys.stdin and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()):
        new_prompt = (
            f"\n{INDENT}{DG}╰─{RS} "
            f"{GD}{BD}❯{RS} "
            f"{BWH}{clean_label}{RS}  "
            f"{DG}→{RS} "
            f"[ y / n ]  "
            f"{CY}❯{RS} "
        )
        ans = _orig_input(new_prompt).strip().lower()
        return ans if ans in ('y', 'n') else default

    import msvcrt

    selected = default.lower()

    def render():
        if selected == 'y':
            yn_part = f"{DG}[{RS} {GR}{BD}y{RS} {DG}/{RS} {GY}n{RS} {DG}]{RS}"
        else:
            yn_part = f"{DG}[{RS} {GY}y{RS} {DG}/{RS} {RD}{BD}n{RS} {DG}]{RS}"
        line = (
            f"\r{INDENT}{DG}╰─{RS} "
            f"{GD}{BD}❯{RS} "
            f"{BWH}{clean_label}{RS}  "
            f"{DG}→{RS} "
            f"{yn_part}  "
            f"{CY}❯{RS} "
        )
        sys.stdout.write(line)
        sys.stdout.flush()

    sys.stdout.write('\n')
    render()

    while True:
        try:
            ch = msvcrt.getch()
        except KeyboardInterrupt:
            sys.stdout.write('\n')
            raise

        if ch in (b'y', b'Y'):
            selected = 'y'
            render()
            sys.stdout.write(f" {GR}{BD}y{RS}\n")
            sys.stdout.flush()
            return 'y'
        elif ch in (b'n', b'N'):
            selected = 'n'
            render()
            sys.stdout.write(f" {RD}{BD}n{RS}\n")
            sys.stdout.flush()
            return 'n'
        elif ch in (b'\r', b'\n'):
            col = GR if selected == 'y' else RD
            sys.stdout.write(f" {col}{BD}{selected}{RS}\n")
            sys.stdout.flush()
            return selected
        elif ch in (b'\x00', b'\xe0'):
            # Arrow keys on Windows
            try:
                ch2 = msvcrt.getch()
            except Exception:
                continue
            if ch2 in (b'K', b'H'):  # Left / Up arrow -> y
                selected = 'y'
                render()
            elif ch2 in (b'M', b'P'):  # Right / Down arrow -> n
                selected = 'n'
                render()
        elif ch == b'\t':  # Tab toggle
            selected = 'n' if selected == 'y' else 'y'
            render()
        elif ch == b'\x03':  # Ctrl+C
            sys.stdout.write('\n')
            raise KeyboardInterrupt


def hooked_input(prompt=''):
    if hasattr(sys.stdout, 'flush_dbg_buffer'):
        sys.stdout.flush_dbg_buffer()

    clean_p = _ANSI.sub('', prompt).strip()

    # Reset orbs claimed tracker on new batch prompt
    if hasattr(sys.stdout, '_orbs_claimed_this_batch') and 'skip quest' in clean_p.lower():
        sys.stdout._orbs_claimed_this_batch = False

    # Match "HH:MM:SS  ASK  label (hint):" pattern
    m = re.search(r'(\d{2}:\d{2}:\d{2})\s+ASK\s+(.*?):\s*$', clean_p)
    if m:
        ts, full_label = m.groups()
        label_clean = re.sub(
            r'\s*\(\s*\[.*?\]\s*default=([^\)]+)\)',
            lambda x: f"  {DG}[default: {GD}{x.group(1).strip()}{DG}]{RS}",
            full_label
        ).strip()

        # Intercept Quest prompt
        if 'skip quest' in label_clean.lower():
            # 1. Ask Skip Quest
            skip_ans = interactive_yn(label_clean, default='n')

            # 2. Ask Skip Orbs Claimer
            claimer_label = 'Skip Orbs Claimer for this batch? (y/n) (y = skip  n = run)'
            claimer_ans = interactive_yn(claimer_label, default='n')
            os.environ['ORB_CLAIMER_BATCH_ENABLED'] = '0' if claimer_ans == 'y' else '1'

            # 3. Ask Skip Orbs Buyer
            buyer_label = 'Skip Orbs Buyer for this batch? (y/n) (y = skip  n = run)'
            buyer_ans = interactive_yn(buyer_label, default='n')
            os.environ['ORB_BUYER_BATCH_SKIP'] = '1' if buyer_ans == 'y' else '0'

            return skip_ans

        # Other (y/n) prompts
        if '(y/n)' in label_clean.lower() or '[ y / n ]' in label_clean.lower():
            def_val = 'y' if ('default=y' in full_label.lower() or 'hypesquad' in full_label.lower()) else 'n'
            return interactive_yn(label_clean, default=def_val)

        new_prompt = (
            f"\n{INDENT}{DG}╰─{RS} "
            f"{GD}{BD}❯{RS} "
            f"{BWH}{label_clean}{RS}  "
            f"{DG}→{RS} "
            f"{CY}❯{RS} "
        )
        return _orig_input(new_prompt)

    # Generic styled prompt passthrough
    if prompt.strip():
        if 'skip quest' in clean_p.lower():
            skip_ans = interactive_yn(clean_p, default='n')
            claimer_label = 'Skip Orbs Claimer for this batch? (y/n) (y = skip  n = run)'
            claimer_ans = interactive_yn(claimer_label, default='n')
            os.environ['ORB_CLAIMER_BATCH_ENABLED'] = '0' if claimer_ans == 'y' else '1'
            buyer_label = 'Skip Orbs Buyer for this batch? (y/n) (y = skip  n = run)'
            buyer_ans = interactive_yn(buyer_label, default='n')
            os.environ['ORB_BUYER_BATCH_SKIP'] = '1' if buyer_ans == 'y' else '0'
            return skip_ans

        if '(y/n)' in clean_p.lower():
            def_val = 'y' if ('default=y' in clean_p.lower() or 'hypesquad' in clean_p.lower()) else 'n'
            return interactive_yn(clean_p, default=def_val)

        new_prompt = (
            f"\n{INDENT}{DG}╰─{RS} "
            f"{GD}{BD}❯{RS} "
            f"{WH}{clean_p}{RS}  "
            f"{CY}❯{RS} "
        )
        return _orig_input(new_prompt)

    return _orig_input(prompt)

builtins.input = hooked_input


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def run_main():
    """Run main.py through the LordVault aesthetic wrapper."""
    sys.stdout = LordVaultStream(sys.stdout)

    main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
    with open(main_path, 'r', encoding='utf-8') as f:
        code = f.read()

    exec(compile(code, main_path, 'exec'), {'__name__': '__main__', '__file__': main_path})


if __name__ == '__main__':
    run_main()
