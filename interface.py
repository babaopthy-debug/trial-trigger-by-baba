"""LordVault terminal dashboard. Run with --preview for a safe, sample screen."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime

import lv_theme as theme

RS, BD = theme.RESET, theme.BOLD
CY, LP, MP = theme.CYAN, theme.PURPLE, theme.PINK
GD, GR, RD = theme.GOLD, theme.GREEN, theme.RED
WH, GY, DG = theme.WHITE, theme.MUTED, theme.BORDER
DEFAULT_ORBS_BUYER_SKU = '1342211853484429445'

MENU_ITEMS = [
    ('1', 'Launch LordVault', 'Open your workspace', CY),
    ('2', 'Token Manager', 'View counts and formats', GD),
    ('3', 'Configuration', 'Review your settings', LP),
    ('4', 'Quick Start Guide', 'Setup and essentials', MP),
    ('0', 'Exit', 'See you next time', GY),
]

_ansi = False
_motion = os.environ.get('LORDVAULT_REDUCED_MOTION', '').lower() not in ('1', 'true', 'yes')


def _root():
    return str(Path(__file__).resolve().parent)


def _read_lines(relative):
    try:
        with open(Path(_root()) / relative, encoding='utf-8') as stream:
            return [line.strip() for line in stream if line.strip()]
    except (OSError, UnicodeError):
        return []


def get_token_count():
    return len(_read_lines('input/tokens.txt'))


def get_orb_token_count():
    return len(_read_lines('orb_claimer/token.txt'))


def load_config():
    try:
        with open(Path(_root()) / 'input/config.json', encoding='utf-8') as stream:
            value = json.load(stream)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _mapping(value):
    return value if isinstance(value, dict) else {}


def snapshot():
    cfg = load_config()
    return {
        'tokens': get_token_count(), 'orbs': get_orb_token_count(),
        'workers': cfg.get('max_workers', 10),
        'quests': bool(_mapping(cfg.get('quest_completer')).get('enabled', False)),
        'proxy': bool(cfg.get('use_proxy', False)),
        'orb_buyer': _mapping(cfg.get('orb_buyer')).get('enabled', True) is not False,
    }


def _geometry(columns):
    # Reserve the final terminal column to avoid Windows auto-wrap.
    total = max(1, min(86, columns - 2))
    margin = ' ' * max(0, (columns - total) // 2)
    return max(1, total - 2), margin


def _edge(width, top=True, label=''):
    left, right = ('╭', '╮') if top else ('╰', '╯')
    heading = f' {label} ' if label else ''
    heading = theme.fit(heading, min(width, theme.visible_width(heading)))
    return f'{DG}{left}{heading}{"─" * max(0, width - theme.visible_width(heading))}{right}{RS}'


def _row(text, width):
    return f'{DG}│{RS}{theme.fit(text, width)}{DG}│{RS}'


def _join(left, right, width):
    right_width = min(theme.visible_width(right), max(0, width // 2))
    return theme.fit(left, max(0, width - right_width)) + theme.fit(right, right_width, align='right')


def _pill(label, enabled, color=GR):
    return f'{color if enabled else GY}{BD}{label}{RS}'


def _header(width, tall=False, phase=0):
    rows = [_join(f'{LP}◆{RS} {WH}{BD}LordVault{RS}', f'{GY}CONTROL CENTER  /  5.0{RS}', width + 2), '']
    if tall and width >= 58:
        for line in theme.BANNER_ROWS:
            rows.append(theme.fit(theme.gradient(line, phase=phase), width + 2, align='center'))
    else:
        rows.append(theme.fit(BD + theme.gradient('L O R D V A U L T', phase=phase), width + 2, align='center'))
    rows.append(theme.fit(f'{GY}YOUR WORKSPACE.  ONE COMMAND AWAY.{RS}', width + 2, align='center'))
    rows.append('')
    return rows


def render_dashboard(data, columns=80, rows=25, selected=0, phase=0, motion=True, clock=None, notice=''):
    """Pure rendering: no file access, terminal control, or application actions."""
    width, margin = _geometry(columns)
    clock = clock or datetime.now().strftime('%H:%M:%S')
    if columns < 42 or rows < 23:
        lines = [BD + theme.gradient('LordVault', phase=phase), f'{GY}CONTROL CENTER{RS}', '']
        for index, (key, label, hint, color) in enumerate(MENU_ITEMS):
            marker = '›' if index == selected else ' '
            lines.append(f'{color}{marker} [{key}] {label}{RS}')
        lines += ['', f'{GY}↑/↓ select · Enter open{RS}', f'{GY}M {"Motion ON" if motion else "Motion OFF"} · R refresh · 0 exit{RS}']
        if notice:
            lines.append(f'{GD}{notice}{RS}')
        return [theme.fit(line, max(1, columns - 1)).rstrip() for line in lines[:max(1, rows - 1)]]

    tall = rows >= 25 and width >= 58
    lines = _header(width, tall=tall, phase=phase)
    tokens = data.get('tokens', 0)
    ready = 'TOKENS LOADED' if tokens else 'ADD TOKENS TO BEGIN'
    pulse = ('●', '◉', '●', '·')[phase % 4] if motion else '●'
    left = f' {GR if tokens else GD}{pulse} {BD}{ready}{RS}'
    right = f'{GY}{clock}  {RS}'
    lines.append(_edge(width, label='WORKSPACE'))
    lines.append(_row(_join(left, right, width), width))
    cells = [
        f'{GD}{BD}{tokens}{RS} {GY}tokens{RS}',
        f'{MP}{BD}{data.get("orbs", 0)}{RS} {GY}orb tokens{RS}',
        f'{CY}{BD}{data.get("workers", 10)}{RS} {GY}workers{RS}',
    ]
    cell_width = (width - 2) // 3
    lines.append(_row(' ' + ''.join(theme.fit(cell, cell_width) for cell in cells), width))
    quest = _pill('ON' if data.get('quests') else 'OFF', data.get('quests'))
    proxy = _pill('ON' if data.get('proxy') else 'OFF', data.get('proxy'), GD)
    buyer = _pill('ON' if data.get('orb_buyer', True) else 'OFF', data.get('orb_buyer', True), MP)
    lines.append(_row(f' {GY}Quests {RS}{quest}    {GY}Proxy {RS}{proxy}    {GY}Orbs Buyer {RS}{buyer}', width))
    lines.append(_edge(width, top=False))
    if not tall:
        lines.append('')
    lines.append(_edge(width, label='QUICK ACTIONS'))
    for index, (key, label, hint, color) in enumerate(MENU_ITEMS):
        is_selected = index == selected
        marker = '›' if is_selected else ' '
        lead = f'{color}{BD}{marker} {key}{RS}  {WH if is_selected else GY}{BD if is_selected else ""}{label}{RS}'
        if width >= 66:
            inside = theme.fit(lead, 29) + f'{GY}{hint}{RS}'
        else:
            inside = lead
        inside = theme.fit(' ' + inside, width)
        if is_selected:
            inside = theme.SELECT_BG + inside.replace(RS, RS + theme.SELECT_BG) + RS
        lines.append(_row(inside, width))
    lines.append(_edge(width, top=False))
    if not tall:
        lines.append('')
    lines.append(_join(f'{CY}↑ ↓{RS} {GY}navigate   {CY}Enter{RS} {GY}open{RS}', f'{GY}[M] Motion {"ON" if motion else "OFF"}{RS}', width + 2))
    footer = f'{GD}{notice}{RS}' if notice else f'{GY}[R] Refresh   [0] Exit{RS}'
    lines.append(_join(footer, f'{LP}◆{RS} {GY}LordVault{RS}', width + 2))
    return [margin + theme.fit(line, width + 2) for line in lines]


class TerminalCanvas:
    """Send only changed lines in a single write, keeping RDP redraws small."""

    def __init__(self):
        self.previous = []
        self.size = None

    def draw(self, lines, size):
        columns, height = size
        lines = [theme.fit(line, max(1, columns - 1)) for line in lines[:max(1, height - 1)]]
        if not _ansi:
            sys.stdout.write('\n'.join(theme.strip_ansi(line).rstrip() for line in lines) + '\n')
            sys.stdout.flush()
            return
        output = []
        if self.size != size:
            output.append('\033[2J\033[H')
            self.previous = []
        for index in range(max(len(lines), len(self.previous))):
            line = lines[index] if index < len(lines) else ''
            if index >= len(self.previous) or line != self.previous[index]:
                output.append(f'\033[{index + 1};1H\033[2K{line}{RS}')
        if output:
            sys.stdout.write(''.join(output))
            sys.stdout.flush()
        self.previous = lines
        self.size = size


def _read_key():
    import msvcrt
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getwch()
    if key in ('\x00', '\xe0'):
        return {'H': 'up', 'P': 'down', 'K': 'left', 'M': 'right'}.get(msvcrt.getwch(), '')
    if key == '\x03':
        raise KeyboardInterrupt
    return {'\r': 'enter', '\x1b': 'escape', '\t': 'down'}.get(key, key.lower())


def _interactive():
    return _ansi and os.name == 'nt' and sys.stdin.isatty()


def _cursor(visible):
    if _ansi:
        sys.stdout.write('\033[?25h' if visible else '\033[?25l')
        sys.stdout.flush()


def clear():
    if _ansi:
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()


def _print(text=''):
    print(text if _ansi else theme.strip_ansi(text))


def _input(label):
    try:
        return input(label if _ansi else theme.strip_ansi(label)).strip()
    except EOFError:
        return '0'


def press_enter(msg='Press Enter to return'):
    _input(f'\n {GY}{msg}{RS} ')


def choose_action():
    global _motion
    data = snapshot()
    selected, phase = 0, 0
    canvas = TerminalCanvas()
    notice, notice_until = '', 0.0
    next_frame = 0.0
    _cursor(False)
    try:
        while True:
            now = time.monotonic()
            size = theme.terminal_size()
            if now >= next_frame or size != canvas.size:
                canvas.draw(render_dashboard(data, *size, selected=selected, phase=phase,
                    motion=_motion and _interactive(), notice=notice if now < notice_until else ''), size)
                if _motion and _interactive():
                    phase += 1
                next_frame = now + (0.25 if _motion else 1.0)
            if not _interactive():
                answer = _input(f'\n {CY}Select [1–4 / 0]{RS} › ').lower()
                if answer in {item[0] for item in MENU_ITEMS}:
                    return answer
                if answer == 'm':
                    _motion = not _motion
                elif answer == 'r':
                    data = snapshot()
                else:
                    _print(f' {GD}Choose 1, 2, 3, 4, or 0.{RS}')
                next_frame = 0
                continue
            key = _read_key()
            if key in ('up', 'down'):
                selected = (selected + (1 if key == 'down' else -1)) % len(MENU_ITEMS)
                next_frame = 0
            elif key in {item[0] for item in MENU_ITEMS}:
                return key
            elif key == 'enter':
                return MENU_ITEMS[selected][0]
            elif key == 'escape':
                return '0'
            elif key == 'm':
                _motion = not _motion
                phase = 0
                next_frame = 0
            elif key == 'r':
                data = snapshot()
                notice, notice_until = 'Workspace refreshed', now + 2.0
                next_frame = 0
            time.sleep(0.04)
    finally:
        _cursor(True)


def show_detail(title, rows):
    """Paginated cards keep settings and help accessible in short RDP windows."""
    page = 0
    canvas = TerminalCanvas()
    _cursor(False)
    try:
        while True:
            size = theme.terminal_size()
            width, margin = _geometry(size[0])
            page_size = max(1, size[1] - 10)
            pages = max(1, (len(rows) + page_size - 1) // page_size)
            page = min(page, pages - 1)
            lines = [f'{LP}◆ {WH}{BD}LordVault{RS}  {GY}/  {title}{RS}', '', _edge(width, label=title)]
            for row in rows[page * page_size:(page + 1) * page_size]:
                lines.append(_row(' ' + row, width))
            lines += [_edge(width, top=False), '', _join(f'{CY}← →{RS} {GY}pages   {CY}Enter / Esc{RS} {GY}back{RS}', f'{GY}{page + 1} / {pages}{RS}', width + 2)]
            canvas.draw([margin + theme.fit(line, width + 2) for line in lines], size)
            if not _interactive():
                key = _input('\n [N] Next  [P] Previous  [Enter] Back › ').lower()
                key = {'n': 'right', 'p': 'left'}.get(key, 'enter')
            else:
                key = _read_key()
            if key in ('enter', 'escape', '0'):
                return
            if key in ('right', 'down'):
                page = min(pages - 1, page + 1)
            elif key in ('left', 'up'):
                page = max(0, page - 1)
            time.sleep(0.04)
    finally:
        _cursor(True)


def _kv(key, value, color=CY):
    return f'{GY}{key:<17}{RS}{color}{value}{RS}'


def screen_tokens():
    tokens = _read_lines('input/tokens.txt')
    combo = sum(1 for token in tokens if token.count(':') >= 2)
    show_detail('TOKEN MANAGER', [
        f'{GD}{BD}Your token library{RS}', '',
        _kv('Total tokens', len(tokens), GD),
        _kv('Combo format', combo),
        _kv('Plain format', len(tokens) - combo, LP),
        _kv('Orb tokens', get_orb_token_count(), MP), '',
        _kv('Source', 'input/tokens.txt'),
        f'{GY}Counts reflect local files.{RS}',
    ])


def screen_config():
    cfg = load_config()
    qc = _mapping(cfg.get('quest_completer'))
    orb = _mapping(cfg.get('orb_claimer'))
    buyer = _mapping(cfg.get('orb_buyer'))
    setup = _mapping(cfg.get('setup'))
    enabled = lambda value: f'{GR}ON{RS}' if value else f'{GY}OFF{RS}'
    show_detail('CONFIGURATION', [
        f'{LP}{BD}GENERAL{RS}',
        _kv('Proxy', enabled(cfg.get('use_proxy'))),
        _kv('Debug mode', enabled(cfg.get('debug'))),
        _kv('Max workers', cfg.get('max_workers', 10)), '',
        f'{LP}{BD}QUEST COMPLETER{RS}',
        _kv('Enabled', enabled(qc.get('enabled'))),
        _kv('Enroll first', enabled(qc.get('enroll_first'))),
        _kv('Threads', qc.get('threads', 10)),
        _kv('Quest IDs', ', '.join(str(q) for q in (qc.get('quest_ids') or [])) or 'None', GD), '',
        f'{MP}{BD}ORB CLAIMER{RS}',
        _kv('Auto claim', enabled(orb.get('enabled', True))),
        _kv('Threads', orb.get('threads', 3)),
        _kv('Tokens ready', get_orb_token_count(), GD), '',
        f'{MP}{BD}ORBS BUYER{RS}',
        _kv('Enabled', enabled(buyer.get('enabled', True) is not False)),
        _kv('Item SKU', buyer.get('sku_id', DEFAULT_ORBS_BUYER_SKU), GD),
        f'{GY}Purchases only after a confirmed Orbs claim.{RS}', '',
        f'{CY}{BD}SERVER SETUP{RS}',
        _kv('Invite link', setup.get('invite', '—')),
        _kv('Voice channel', setup.get('voice_channel_id', '—'), LP),
        _kv('Text channel', setup.get('text_channel_id', '—'), LP), '',
        f'{GY}Edit settings in input/config.json.{RS}',
    ])


def screen_guide():
    show_detail('QUICK START', [
        f'{GD}{BD}01  PREPARE{RS}',
        f'{WH}Add tokens to input/tokens.txt.{RS}', '',
        f'{CY}{BD}02  CONFIGURE{RS}',
        f'{WH}Review input/config.json.{RS}',
        f'{GY}Set your invite link and channel IDs.{RS}', '',
        f'{MP}{BD}ORBS BUYER{RS}',
        f'{WH}Runs automatically after a confirmed Orbs claim.{RS}',
        f'{GY}Set orb_buyer.enabled and orb_buyer.sku_id in config.{RS}', '',
        f'{LP}{BD}03  OPEN{RS}',
        f'{WH}Choose Launch LordVault from the menu.{RS}', '',
        f'{MP}{BD}KEYBOARD SHORTCUTS{RS}',
        f'{WH}↑ / ↓      Select a menu item{RS}',
        f'{WH}Enter      Open the selected item{RS}',
        f'{WH}1–4 / 0    Open an action / exit{RS}',
        f'{WH}M          Toggle animation{RS}',
        f'{WH}R          Refresh workspace counts{RS}', '',
        f'{GD}{BD}TOKEN FORMATS{RS}',
        f'{GY}Plain: token   Combo: email:password:token{RS}',
    ])


def _launch(filename):
    clear()
    _print(f'\n {BD}{theme.gradient("LordVault")}{RS}\n')
    _print(f' {CY}›{RS} {WH}Opening workspace…{RS}\n')
    command = ['py', '-3.12'] if os.name == 'nt' else [sys.executable]
    subprocess.run(command + [str(Path(_root()) / filename)], cwd=_root(), check=False)
    press_enter('Press Enter to return to LordVault')


def screen_orbclaimer():
    # Retained for callers of the existing optional screen.
    while True:
        clear()
        _print(f'\n {MP}{BD}LordVault / Orb Claimer{RS}\n')
        _print(f' {GY}Tokens ready:{RS} {GD}{get_orb_token_count()}{RS}')
        buyer = _mapping(load_config().get('orb_buyer'))
        _print(f' {GY}Orbs Buyer:{RS} {MP}{"ON" if buyer.get("enabled", True) is not False else "OFF"}{RS}')
        _print(f' {GY}Item SKU:{RS} {GD}{buyer.get("sku_id", DEFAULT_ORBS_BUYER_SKU)}{RS}')
        _print(f' {GY}Purchases only after a confirmed Orbs claim.{RS}')
        _print('\n [1] Run Orb Claimer\n [2] Open Folder\n [3] Sync from success.txt\n [0] Back')
        choice = _input('\n Select › ')
        if choice == '1':
            _launch('orb_claimer/orb.py')
        elif choice == '2' and os.name == 'nt':
            os.startfile(str(Path(_root()) / 'orb_claimer'))
        elif choice == '3':
            try:
                from quest_completer.quest_completer import sync_to_orbclaimer
                _print(f' Synced {sync_to_orbclaimer()} token(s).')
            except Exception as error:
                _print(f' Sync error: {error}')
            press_enter()
        elif choice == '0':
            return


def show_intro():
    if not (_motion and _interactive()):
        return
    canvas = TerminalCanvas()
    _cursor(False)
    try:
        for phase in range(8):
            size = theme.terminal_size()
            width, margin = _geometry(size[0])
            lines = [''] * max(1, (size[1] - 10) // 2)
            lines += _header(width, tall=size[1] >= 22, phase=phase)
            lines.append(theme.fit(f'{CY}Welcome to your workspace{RS}', width + 2, align='center'))
            canvas.draw([margin + line for line in lines], size)
            time.sleep(0.09)
    finally:
        _cursor(True)


def main(argv=None):
    global _ansi, _motion
    parser = argparse.ArgumentParser(description='LordVault terminal dashboard')
    parser.add_argument('--no-animation', action='store_true', help='Disable motion for this session')
    parser.add_argument('--preview', action='store_true', help='Print a sample dashboard without reading project data')
    parser.add_argument('--columns', type=int, default=80, help='Preview width')
    parser.add_argument('--rows', type=int, default=25, help='Preview height')
    parser.add_argument('--color', action='store_true', help='Keep ANSI colors in preview output')
    args = parser.parse_args(argv)
    _motion = _motion and not args.no_animation
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    if args.preview:
        demo = {'tokens': 128, 'orbs': 24, 'workers': 10, 'quests': True, 'proxy': False}
        lines = render_dashboard(demo, max(1, args.columns), max(2, args.rows), clock='12:48:06', motion=_motion)
        print('\n'.join(lines if args.color else [theme.strip_ansi(line).rstrip() for line in lines]))
        return
    _ansi = theme.init_terminal()
    if _ansi:
        sys.stdout.write('\033]0;LordVault | Control Center\007')
    try:
        show_intro()
        while True:
            choice = choose_action()
            if choice == '1':
                _launch('launcher.py')
            elif choice == '2':
                screen_tokens()
            elif choice == '3':
                screen_config()
            elif choice == '4':
                screen_guide()
            elif choice == '0':
                clear()
                _print(f'\n {BD}{theme.gradient("LordVault")}{RS}  {GY}Until next time.{RS}\n')
                return
    finally:
        _cursor(True)
        if _ansi:
            sys.stdout.write(RS)
            sys.stdout.flush()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        _print(f'\n {GY}LordVault closed.{RS}')
