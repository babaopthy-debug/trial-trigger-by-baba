# Desktop entry only. Imports and calls through the original launcher retain
# the complete terminal backend below, including its existing input/output flow.
if __name__ == "__main__":
    import os as _lv_os
    import sys as _lv_sys
    if (
        _lv_os.environ.get("LORDVAULT_BACKEND") != "1"
        and "--terminal" not in _lv_sys.argv
        and _lv_os.path.basename(_lv_sys.argv[0]).lower() != "launcher.py"
    ):
        from lordvault_gui.bootstrap import launch as _lv_launch
        raise SystemExit(_lv_launch())

import asyncio
from datetime import datetime
import threading
import aiohttp
import json
import os
import sys
import time
import importlib.util
import tfa as _tfa
import hypesquad as _hypesquad

def cls():
    os.system("cls" if os.name == "nt" else "clear")

# Terminal UTF-8 output encoding setup
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import random
import base64
import uuid
import requests
import websockets
import websockets.exceptions as ws_exc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Set, Tuple, Dict
from colorama import init, Fore
from base64 import b64encode
from tls_client import Session, response



init(autoreset=True)

# Path configuration
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
QUEST_COMPLETER_DIR = os.path.join(BASE, "quest_completer")
if QUEST_COMPLETER_DIR not in sys.path:
    sys.path.insert(0, QUEST_COMPLETER_DIR)
INPUT_DIR = os.path.join(BASE, "input")
OUTPUT_DIR = os.path.join(BASE, "output")
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(INPUT_DIR, "config.json")
TOKENS_FILE = os.path.join(INPUT_DIR, "tokens.txt")
PROJECT_ROOT = os.path.dirname(BASE)
DOMAINS = ["discord.com", "canary.discord.com", "ptb.discord.com"]
_hdr_cache = None
_hdr_time = 0

# ── ANSI colors ──────────────────────────────────────
def c(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def bc(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"

R = "\033[0m"
B = "\033[1m"
D = "\033[2m"

# ── Palettes ──────────────────────────────────────────
EMBER   = [(255,60,0),(255,100,10),(255,140,30),(255,180,60),(255,210,90)]
LAVA    = [(140,0,0),(200,10,0),(255,30,0),(255,70,20),(255,110,40)]
MINT    = [(0,200,120),(30,230,140),(80,255,170),(140,255,200),(200,255,230)]
BLOOD   = [(180,0,20),(220,10,20),(255,20,40),(255,70,80),(255,110,110)]
ICE     = [(0,180,220),(20,210,240),(60,230,255),(120,245,255),(180,250,255)]
GOLD    = [(180,120,0),(220,160,10),(255,200,30),(255,220,80),(255,240,140)]
GHOST   = [(25,25,30),(40,40,50),(60,60,70),(85,85,95),(110,110,120)]
PURPLE  = [(80,0,160),(120,20,200),(160,60,240),(200,110,255),(220,160,255)]


def W():
    try:
        return os.get_terminal_size().columns
    except:
        return 110

def grad_line(text, palette, shift=0, center=True, width=None):
    w = width or W()
    out = ""
    for i, ch in enumerate(text):
        r, g, b = palette[(i + shift) % len(palette)]
        out += c(r, g, b) + ch
    return (B + out + R).center(w + len(out) - len(text)) if center else B + out + R

def hbar(w, ch="─", pal=GHOST):
    line = ""
    for i in range(w):
        r, g, b = pal[i % len(pal)]
        line += c(r, g, b) + ch
    return line + R

# ── UI Components ─────────────────────────────────────
def box(title, pal=None):
    pass

def ask(label, hint=""):
    ts = datetime.now().strftime('%H:%M:%S')
    hint_str = f" {ev_gray}({hint}){ev_reset}" if hint else ""
    ans = input(f"{ev_gray}{ts}{ev_reset}  {ev_yellow}ASK{ev_reset} {ev_white}{label}{ev_reset}{hint_str}{ev_white}: {ev_reset}")
    return ans.strip()

def ask_int(label: str, hint: str, minimum: int = 0, maximum: int = 10_000_000) -> int:
    while True:
        raw = ask(label, hint=hint).strip()
        if not raw:
            return 0
        if not raw.lstrip("-").isdigit():
            log_warn(f"'{raw}' is not a valid number. Try again.")
            continue
        n = int(raw)
        if n < minimum or n > maximum:
            log_warn(f"Value must be between {minimum} and {maximum}.")
            continue
        return n

# ---- Log design (EV Gen style) -------------------------------
ev_bold   = '\033[1m'
ev_reset  = '\033[0m'
ev_gray   = '\033[38;2;125;125;125m'
ev_cyan   = '\033[1;38;2;0;235;255m'
ev_green  = '\033[1;38;2;60;255;120m'
ev_yellow = '\033[1;38;2;255;220;50m'
ev_red    = '\033[1;38;2;255;70;70m'
ev_white  = '\033[38;2;250;250;250m'

_log_lock = threading.Lock()

def _ev_print(tag, tag_color, message):
    ts = datetime.now().strftime('%H:%M:%S')
    with _log_lock:
        sys.stdout.write(f"{ev_gray}{ts}{ev_reset}  {tag_color}{tag}{ev_reset} {ev_white}{message}{ev_reset}\n")
        sys.stdout.flush()

def log_info(text):
    _ev_print("INFO", ev_cyan, text)

def log_ok(text):
    _ev_print("OK", ev_green, text)

def log_warn(text):
    _ev_print("WARN", ev_yellow, text)

def log_fail(text):
    _ev_print("ERR", ev_red, text)

def log_err(text):
    _ev_print("ERR", ev_red, text)

def log_dim(text):
    _ev_print("DBG", ev_gray, text)

def spin_result(text, palette=None):
    log_ok(text)

def divider(pal=None):
    pass

def show_banner():
    cls()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_cfg = {
            "bot_token": "YOUR_BOT_TOKEN",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "http://localhost:8080",
            "use_proxy": False,
            "max_workers": 10,
            "quest_completer": {
                "enabled": True,
                "enroll_first": True,
                "quest_ids": [],
                "threads": 5
            },
            "setup": {
                "invite": "",
                "voice_channel_id": "",
                "text_channel_id": "",
                "vc_mute": 0,
                "vc_video": 0,
                "vc_stream": 0,
                "chat_delay": 5,
                "smart_chat": True
            }
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_cfg, f, indent=4)
        return default_cfg

    with open(CONFIG_FILE) as f:
        return json.load(f)

SETUP_DEFAULTS = {
    "invite": "",
    "voice_channel_id": "",
    "text_channel_id": "",
    "vc_mute": 0,
    "vc_video": 0,
    "vc_stream": 0,
    "chat_delay": 5,
    "smart_chat": True,
    "react_channel_id": "",
    "react_emojis": "👍,❤️,🔥,😂,😮,🎉,💯,👀",
    "react_delay": 3,
}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)
        log_dim(f"Saved to {os.path.basename(CONFIG_FILE)}")
    except Exception as e:
        log_warn(f"Could not write config.json: {e}")

def get_setup(cfg):
    setup = dict(SETUP_DEFAULTS)
    setup.update(cfg.get("setup", {}) or {})
    return setup

def load_tokens():
    """Returns (tokens_list, raw_map) where raw_map[token] = original_line."""
    if not os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "w") as f:
            f.write("# Put tokens here, one per line\n")
        return [], {}
    with open(TOKENS_FILE, encoding="utf-8") as f:
        raw = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    out     = []
    raw_map = {}
    seen    = set()
    for line in raw:
        parts = line.split(":")
        token = parts[-1] if len(parts) >= 3 else line
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
        raw_map[token] = line   # preserve full email:password:token line
    return out, raw_map

# ── Dynamic module loader ─────────────────────────────────
def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Quest Completer local import
def run_quest_completer(cfg):
    try:
        import quest_completer
        import importlib
        importlib.reload(quest_completer)
        result = quest_completer.run(cfg)
        return result if isinstance(result, list) else []
    except Exception as e:
        log_fail(f"Quest Completer error: {e}")
        return []

_CHROME_VER_FALLBACK  = "152.0.7977.64"
_BUILD_NUMBER_FALLBACK = "605146"

def get_headers():
    global _hdr_cache, _hdr_time
    now = time.time()
    if _hdr_cache and (now - _hdr_time) < 600:
        return _hdr_cache

    import re
    # Try to grab the live Discord build number
    try:
        r = requests.get("https://discord.com/login", timeout=10,
                         headers={"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{_CHROME_VER_FALLBACK} Safari/537.36"})
        m = re.search(r'"BUILD_NUMBER":"(\d+)"', r.text)
        build = m.group(1) if m else _BUILD_NUMBER_FALLBACK
    except:
        build = _BUILD_NUMBER_FALLBACK

    # Try to grab the live Chrome stable version
    try:
        r = requests.get(
            "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json",
            timeout=5)
        chrome_ver = r.json()['channels']['Stable']['version']
    except:
        chrome_ver = _CHROME_VER_FALLBACK

    ua        = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"
    milestone = chrome_ver.split('.')[0]
    sec_ch_ua = f'"Google Chrome";v="{milestone}", "Not-A.Brand";v="8", "Chromium";v="{milestone}"'

    props = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": ua,
        "browser_version": chrome_ver,
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": int(build),
        "client_event_source": None,
        "client_launch_id": str(uuid.uuid4()),
        "launch_signature": str(uuid.uuid4()),
        "design_id": 0,
    }
    xsp = base64.b64encode(json.dumps(props, separators=(',', ':')).encode()).decode()
    _hdr_cache = {"ua": ua, "xsp": xsp, "build": build, "sec_ch_ua": sec_ch_ua,
                  "chrome_ver": chrome_ver, "milestone": milestone}
    _hdr_time = now
    return _hdr_cache

def resolve_invite(invite_input):
    code = invite_input.strip().split("/")[-1]
    try:
        r = requests.get(f"https://discord.com/api/v10/invites/{code}?with_counts=true",
                         headers={"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{_CHROME_VER_FALLBACK} Safari/537.36"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            g = data.get("guild", {})
            return {"guild_id": g.get("id"), "guild_name": g.get("name"),
                    "invite_code": code, "members": data.get("approximate_member_count", 0)}
    except:
        pass
    return None

def _get_uid(token):
    try:
        return base64.urlsafe_b64decode(token.split(".")[0] + "==").decode()
    except:
        return None

def oauth_authorize(token, cfg):
    try:
        import tls_client
    except ImportError:
        log_fail("Please install tls_client (pip install tls_client)")
        sys.exit(1)
        
    raw = token.strip().split(":")[-1] if ":" in token else token.strip()
    hdr = get_headers()
    headers = {
        "Authorization": raw, "Origin": "https://discord.com", "Accept": "*/*",
        "X-Super-Properties": hdr["xsp"], "User-Agent": hdr["ua"],
        "Content-Type": "application/json", "Sec-Ch-Ua": hdr.get("sec_ch_ua", ""),
        "Sec-Ch-Ua-Platform": '"Windows"', "Sec-Ch-Ua-Mobile": "?0"
    }
    auth_url = (f"https://discord.com/api/oauth2/authorize?client_id={cfg['client_id']}"
                f"&redirect_uri={cfg['redirect_uri']}&response_type=code"
                f"&scope=identify%20guilds.join%20guilds")

    session = tls_client.Session(client_identifier="chrome_131", random_tls_extension_order=True)
    session.headers['Accept-Encoding'] = 'gzip, deflate, br, zstd'

    try:
        r = session.post(auth_url, json={"authorize": "true"}, headers=headers)
        if r.status_code == 429:
            retry_after = r.json().get("retry_after", 2)
            time.sleep(retry_after)
            return oauth_authorize(token, cfg)
        if r.status_code not in (200, 201, 204):
            return None
        loc = r.json().get("location", "")
        if "code=" not in loc:
            return None
        code = loc.split("code=")[1]

        r = session.post("https://discord.com/api/v10/oauth2/token",
            data={"client_id": cfg["client_id"], "client_secret": cfg["client_secret"],
                  "grant_type": "authorization_code", "code": code, "redirect_uri": cfg["redirect_uri"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code not in (200, 201, 204):
            return None
        at = r.json()["access_token"]
        uid = _get_uid(raw)
        return (uid, at, raw)
    except Exception as e:
        return None

async def verify_token(token: str) -> Optional[Tuple[str, str]]:
    hdr = get_headers()
    headers = {"Authorization": token, "Content-Type": "application/json",
                "User-Agent": hdr["ua"], "X-Super-Properties": hdr["xsp"],
                "x-discord-locale": "en-US", "x-debug-options": "bugReporterEnabled"}
    attempt = 0
    while attempt < 5:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://discord.com/api/v10/users/@me",
                                 headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 429:
                        try:
                            body = await r.json(content_type=None)
                            ra   = float(body.get("retry_after", 5))
                        except Exception:
                            ra = 5.0
                        await asyncio.sleep(ra + 1.5)
                        continue   # don't increment attempt — retry same slot
                    if r.status == 200:
                        d = await r.json()
                        return d.get("username", "?"), d.get("discriminator", "0")
                    if r.status in (401, 403):
                        return None   # definitely invalid
                    # 5xx / anything else — back off and retry
                    await asyncio.sleep(2 * (attempt + 1))
                    attempt += 1
        except Exception:
            await asyncio.sleep(2 * (attempt + 1))
            attempt += 1
    return None

async def join_via_oauth2(bot_token, guild_id, user_id, access_token):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}"
    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers,
                                   json={"access_token": access_token}) as resp:
                if resp.status == 429:
                    body = await resp.json()
                    ra = float(body.get("retry_after", 2))
                    await asyncio.sleep(ra + 0.5)
                    return await join_via_oauth2(bot_token, guild_id, user_id, access_token)
                return resp.status in (200, 201, 204)
    except:
        return False

async def join_via_invite(token, invite_code):
    raw = token.strip().split(":")[-1] if ":" in token else token.strip()
    hdr = get_headers()
    headers = {
        "Authorization":      raw,
        "User-Agent":         hdr["ua"],
        "X-Super-Properties": hdr["xsp"],
        "Content-Type":       "application/json",
        "sec-ch-ua":          hdr["sec_ch_ua"],
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-discord-locale":   "en-US",
        "x-debug-options":    "bugReporterEnabled",
        "Origin":             "https://discord.com",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://discord.com/api/v10/invites/{invite_code}",
                                    headers=headers, json={}) as resp:
                return resp.status in (200, 201, 204)
    except:
        return False

async def check_membership(token, guild_id):
    raw = token.strip().split(":")[-1] if ":" in token else token.strip()
    hdr = get_headers()
    headers = {"Authorization": raw, "User-Agent": hdr["ua"]}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v10/users/@me/guilds",
                                   headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    guilds = await resp.json()
                    return any(g['id'] == guild_id for g in guilds)
    except:
        pass
    return False

# VC starts stream logic copied from core/automation.py
async def vc_start_stream(ws, token, guild_id, channel_id, user_id, tag):
    try:
        await ws.send(json.dumps({
            "op": 18, "d": {
                "type": "guild",
                "guild_id": str(guild_id),
                "channel_id": str(channel_id),
                "preferred_region": random.choice(["us-east", "us-central", "us-south"])
            }
        }))

        stream_key = None
        for _ in range(10):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                d = json.loads(raw)
                if d.get('t') in ('STREAM_CREATE', 'STREAM_SERVER_UPDATE'):
                    stream_key = d.get('d', {}).get('stream_key')
                    if stream_key:
                        break
            except asyncio.TimeoutError:
                break

        if not stream_key:
            stream_key = f"guild:{guild_id}:{channel_id}:{user_id}"

        await ws.send(json.dumps({
            "op": 20, "d": {"stream_key": stream_key, "paused": False}
        }))
        log_ok(f"{tag} stream go-live active")
    except Exception as e:
        log_warn(f"{tag} stream go-live error: {e}")

# VC heartbeat and auto-rejoin/move loop copied from core/automation.py
async def vc_heartbeat_loop(ws, hb_interval, token, guild_id, channel_id, self_mute, self_video, go_live, user_id, seq_ref, stop_event, tag):
    last_ack = time.time()
    ack_timeout = hb_interval * 2.5
    waiting_for_ack = False
    last_vc_refresh = time.time()
    vc_refresh_interval = 300

    _WS_CLOSED_EXC = (
        ws_exc.ConnectionClosed,
        ws_exc.ConnectionClosedOK,
        ws_exc.ConnectionClosedError,
    )

    while not stop_event.is_set():
        if time.time() - last_vc_refresh > vc_refresh_interval:
            try:
                await ws.send(json.dumps({
                    "op": 4, "d": {
                        "guild_id": str(guild_id),
                        "channel_id": str(channel_id),
                        "self_mute": self_mute,
                        "self_deaf": False,
                        "self_video": self_video,
                    }
                }))
                last_vc_refresh = time.time()
            except:
                return

        # Send heartbeat
        try:
            await ws.send(json.dumps({"op": 1, "d": seq_ref[0]}))
            waiting_for_ack = True
        except:
            return

        deadline = time.time() + hb_interval
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 10.0))
                d = json.loads(raw)

                if d.get('s') is not None:
                    seq_ref[0] = d['s']

                op = d.get('op')
                t = d.get('t')

                if op == 11:
                    last_ack = time.time()
                    waiting_for_ack = False
                elif op in (7, 9):
                    log_warn(f"{tag} gateway requested reconnect (op {op})")
                    return
                elif t == 'VOICE_STATE_UPDATE':
                    vs_data = d.get('d', {})
                    vs_user = vs_data.get('user_id', '')
                    vs_channel = vs_data.get('channel_id')

                    if user_id and vs_user == user_id:
                        if vs_channel is None:
                            log_warn(f"{tag} disconnected from VC, rejoining...")
                            await asyncio.sleep(random.uniform(1.0, 3.0))
                            await ws.send(json.dumps({
                                "op": 4, "d": {
                                    "guild_id": str(guild_id),
                                    "channel_id": str(channel_id),
                                    "self_mute": self_mute,
                                    "self_deaf": False,
                                    "self_video": self_video
                                }
                            }))
                            await asyncio.sleep(random.uniform(1.0, 2.0))
                            if go_live:
                                await vc_start_stream(ws, token, guild_id, channel_id, user_id, tag)
                        elif vs_channel != channel_id:
                            log_warn(f"{tag} moved to wrong VC, rejoining target...")
                            await asyncio.sleep(random.uniform(0.5, 2.0))
                            await ws.send(json.dumps({
                                "op": 4, "d": {
                                    "guild_id": str(guild_id),
                                    "channel_id": str(channel_id),
                                    "self_mute": self_mute,
                                    "self_deaf": False,
                                    "self_video": self_video
                                }
                            }))

            except asyncio.TimeoutError:
                pass
            except _WS_CLOSED_EXC:
                return
            except Exception as e:
                if 'closed' in str(e).lower():
                    return
                pass

        if waiting_for_ack and (time.time() - last_ack) > ack_timeout:
            log_warn(f"{tag} zombie connection (no ACK), reconnecting...")
            return

# VC gateway connecting logic copied from core/automation.py
async def vc_connect(token, guild_id, channel_id, self_mute, self_video, go_live, idx, stop_event):
    tag = f"Token[{idx}]"
    log_info(f"{tag} Connecting Voice presence...")
    
    consecutive_failures = 0
    session_id = None
    resume_url = None
    seq_ref = [None]
    
    while not stop_event.is_set():
        ws = None
        try:
            gateway_url = resume_url or 'wss://gateway.discord.gg/?v=10&encoding=json'
            ws = await websockets.connect(
                gateway_url,
                ping_interval=None,
                ping_timeout=None,
                close_timeout=5,
                max_size=2**20,
            )

            # Hello
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
            hb_interval = msg['d']['heartbeat_interval'] / 1000

            # Try Resume if we have a session
            if session_id and seq_ref[0] is not None:
                await ws.send(json.dumps({
                    "op": 6, "d": {
                        "token": token,
                        "session_id": session_id,
                        "seq": seq_ref[0]
                    }
                }))
                log_warn(f"{tag} attempting gateway resume...")

                # Check for RESUMED or INVALID_SESSION
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    d = json.loads(raw)
                    if d.get('s'):
                        seq_ref[0] = d['s']
                    if d.get('t') == 'RESUMED':
                        log_ok(f"{tag} resumed successfully!")
                        consecutive_failures = 0
                        # Re-join VC after resume
                        await ws.send(json.dumps({
                            "op": 4, "d": {
                                "guild_id": str(guild_id),
                                "channel_id": str(channel_id),
                                "self_mute": self_mute,
                                "self_deaf": False,
                                "self_video": self_video
                            }
                        }))
                        await vc_heartbeat_loop(ws, hb_interval, token, guild_id, channel_id, self_mute, self_video, go_live, None, seq_ref, stop_event, tag)
                        continue
                    elif d.get('op') == 9:
                        session_id = None
                        seq_ref[0] = None
                        log_warn(f"{tag} resume failed, fresh identify...")
                except asyncio.TimeoutError:
                    session_id = None
                    seq_ref[0] = None

            # Fresh Identify
            await ws.send(json.dumps({
                "op": 2, "d": {
                    "token": token,
                    "capabilities": 30717,
                    "properties": {
                        "os": "Windows",
                        "browser": "Chrome",
                        "device": "",
                        "system_locale": "en-US",
                        "browser_user_agent": __useragent__,
                        "browser_version": cv,
                        "os_version": "10",
                        "referrer": "",
                        "referring_domain": "",
                        "referrer_current": "",
                        "referring_domain_current": "",
                        "release_channel": "stable",
                        "client_build_number": build_number,
                        "client_event_source": None,
                        "design_id": 0,
                    },
                    "presence": {"status": "online", "since": 0, "activities": [], "afk": False},
                    "compress": False,
                    "client_state": {"guild_versions": {}},
                }
            }))

            # Wait READY
            ready = False
            user_id = None
            for _ in range(20):
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    msg = json.loads(raw)
                    if msg.get('s'):
                        seq_ref[0] = msg['s']
                    if msg.get('t') == 'READY':
                        ready = True
                        user_id = msg.get('d', {}).get('user', {}).get('id')
                        session_id = msg.get('d', {}).get('session_id')
                        resume_url = msg.get('d', {}).get('resume_gateway_url')
                        if resume_url and not resume_url.endswith('?v=10&encoding=json'):
                            resume_url += '?v=10&encoding=json'
                        break
                except asyncio.TimeoutError:
                    break

            if not ready:
                consecutive_failures += 1
                backoff = min(5 * (2 ** min(consecutive_failures, 6)), 120) + random.uniform(0, 3)
                log_fail(f"{tag} READY timeout, retry in {backoff:.1f}s")
                await asyncio.sleep(backoff)
                continue

            # Voice State Update - join VC
            await ws.send(json.dumps({
                "op": 4, "d": {
                    "guild_id": str(guild_id),
                    "channel_id": str(channel_id),
                    "self_mute": self_mute,
                    "self_deaf": False,
                    "self_video": self_video
                }
            }))

            await asyncio.sleep(random.uniform(1.0, 2.5))

            # Go Live
            if go_live and user_id:
                await vc_start_stream(ws, token, guild_id, channel_id, user_id, tag)

            consecutive_failures = 0
            log_ok(f"{tag} Connected to VC {channel_id} (mute={self_mute} video={self_video} live={go_live})")

            # Heartbeat + event monitoring loop
            await vc_heartbeat_loop(ws, hb_interval, token, guild_id, channel_id, self_mute, self_video, go_live, user_id, seq_ref, stop_event, tag)

        except asyncio.CancelledError:
            if ws is not None:
                try:
                    await ws.send(json.dumps({
                        "op": 4, "d": {
                            "guild_id": str(guild_id),
                            "channel_id": None,
                            "self_mute": False,
                            "self_deaf": False
                        }
                    }))
                except:
                    pass
                try:
                    await ws.close()
                except:
                    pass
            break
        except Exception as e:
            err_str = str(e)
            if '4004' in err_str:
                log_fail(f"{tag} auth failed ({err_str}) - stopping permanently")
                break

            consecutive_failures += 1
            backoff = min(3 * (2 ** min(consecutive_failures, 6)), 120) + random.uniform(0.5, 3)
            log_fail(f"{tag} error: {e} - reconnecting in {backoff:.1f}s")
            if consecutive_failures >= 5:
                session_id = None
                seq_ref[0] = None
                resume_url = None
            await asyncio.sleep(backoff)
        finally:
            if ws is not None:
                try:
                    await ws.close()
                except:
                    pass
__useragent__ = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7977.64 Safari/537.36"
build_number = 605146
cv = "152.0.7977.64"
# Modern tls_client identifiers (chrome_131 is the latest stable available in tls_client)
client_identifiers = [
    'chrome_131', 'chrome_130', 'chrome_129', 'chrome_128',
    'chrome_127', 'chrome_126', 'chrome_124', 'chrome_120',
]

__properties__ = b64encode(
  json.dumps(
    {
      "os": "Windows",
      "browser": "Chrome",
      "device": "",
      "system_locale": "en-US",
      "browser_user_agent": __useragent__,
      "browser_version": cv,
      "os_version": "10",
      "referrer": "",
      "referring_domain": "",
      "referrer_current": "",
      "referring_domain_current": "",
      "release_channel": "stable",
      "client_build_number": build_number,
      "client_event_source": None,
      "design_id": 0
    },
    separators=(',', ':')).encode()).decode()
# Chat automation loops

async def trigger_typing(token, channel_id):
    hdr = get_headers()
    session = Session(
        client_identifier=random.choice(client_identifiers),
        random_tls_extension_order=True
    )
    headers = {
        "Authorization":      token,
        "Accept":             "*/*",
        "Accept-Language":    "en-US,en;q=0.9",
        "Content-Type":       "application/json",
        "Origin":             "https://discord.com",
        "Referer":            "https://discord.com/channels/@me",
        "sec-ch-ua":          hdr["sec_ch_ua"],
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-origin",
        "user-agent":         hdr["ua"],
        "x-debug-options":    "bugReporterEnabled",
        "x-discord-locale":   "en-US",
        "x-super-properties": hdr["xsp"],
    }
    try:
        r = session.post(f"https://discord.com/api/v10/channels/{channel_id}/typing", headers=headers)
        return r.status_code in (200, 204)
    except:
        return False



async def send_msg(token, channel_id, content, reply_to=None, image_path=None):
    hdr = get_headers()
    # Per-request nonce (Discord uses this for dedup)
    nonce = str((int(time.time() * 1000) - 1420070400000) << 22)
    # Referer with actual channel
    referer = f"https://discord.com/channels/@me/{channel_id}"
    session = Session(
        client_identifier=random.choice(client_identifiers),
        random_tls_extension_order=True
    )
    base_headers = {
        "Authorization":      token,
        "Accept":             "*/*",
        "Accept-Language":    "en-US,en;q=0.9",
        "Accept-Encoding":    "gzip, deflate, br",
        "Origin":             "https://discord.com",
        "Referer":            referer,
        "sec-ch-ua":          hdr["sec_ch_ua"],
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-origin",
        "user-agent":         hdr["ua"],
        "x-debug-options":    "bugReporterEnabled",
        "x-discord-locale":   "en-US",
        "x-super-properties": hdr["xsp"],
    }
    payload = {"content": content, "nonce": nonce, "tts": False}
    if reply_to:
        payload["message_reference"] = {"message_id": reply_to, "fail_if_not_exists": False}
        payload["allowed_mentions"]  = {"replied_user": random.choice([True, False])}

    try:
        if image_path and os.path.exists(image_path):
            # Multipart: build manually since tls_client doesn't support files=
            import mimetypes, email.generator, email.mime.multipart, email.mime.application, email.mime.base
            fname    = os.path.basename(image_path)
            mime     = mimetypes.guess_type(fname)[0] or "image/jpeg"
            boundary = uuid.uuid4().hex
            with open(image_path, "rb") as img_f:
                img_data = img_f.read()

            # Build raw multipart body
            body  = f"--{boundary}\r\n"
            body += f'Content-Disposition: form-data; name="payload_json"\r\n'
            body += "Content-Type: application/json\r\n\r\n"
            body += json.dumps(payload) + "\r\n"
            body += f"--{boundary}\r\n"
            body += f'Content-Disposition: form-data; name="files[0]"; filename="{fname}"\r\n'
            body += f"Content-Type: {mime}\r\n\r\n"
            body_bytes = body.encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

            img_headers = {**base_headers,
                           "Content-Type": f"multipart/form-data; boundary={boundary}"}
            r = session.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers=img_headers,
                data=body_bytes,
            )
        else:
            headers = {**base_headers, "Content-Type": "application/json"}
            r = session.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers=headers, json=payload
            )

        if r.status_code in (200, 201):
            res = r.json()
            return True, res.get("id")
        try:
            err_body = r.json()
            err_msg  = err_body.get("message", str(err_body))
            err_code = err_body.get("code", "")
        except Exception:
            err_msg  = r.text[:120]
            err_code = ""
        log_warn(f"send_msg HTTP {r.status_code} code={err_code} → {err_msg}")
        return False, None
    except Exception as e:
        log_warn(f"send_msg exception: {e}")
        return False, None





# Inline reaction helper — used by chat loop to react right after a reply is sent
async def add_reaction(token, channel_id, message_id, emoji):
    import urllib.parse
    hdr = get_headers()
    headers = {
        "Authorization": token,
        "Accept": "*/*",
        "User-Agent": hdr["ua"],
        "x-super-properties": hdr["xsp"],
    }
    emoji_encoded = urllib.parse.quote(emoji, safe='')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}/@me",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:
                if resp.status == 429:
                    body = await resp.json()
                    await asyncio.sleep(float(body.get("retry_after", 2)) + 0.3)
                elif resp.status in (200, 201, 204):
                    return True
    except Exception:
        pass
    return False

# React Loop — one token reacts to pre-existing messages with rotating emoji list
# Fetches the message snapshot ONCE at startup so it never reacts to new chat messages
async def react_loop(token, channel_id, emojis, delay, stop_event):
    if not emojis:
        log_fail("No emojis configured for react_loop")
        return

    hdr = get_headers()
    headers = {
        "Authorization": token,
        "Accept": "*/*",
        "User-Agent": hdr["ua"],
        "x-super-properties": hdr["xsp"],
    }

    # Fetch message snapshot once at startup
    snapshot_ids = []
    log_info(f"React loop fetching message snapshot from channel {channel_id}...")
    for attempt in range(5):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=50",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 429:
                        body = await resp.json()
                        ra = float(body.get("retry_after", 5))
                        await asyncio.sleep(ra + 1)
                        continue
                    if resp.status == 200:
                        messages = await resp.json()
                        snapshot_ids = [m["id"] for m in messages if m.get("id")]
                        break
                    await asyncio.sleep(3)
        except Exception as e:
            log_warn(f"React loop snapshot fetch error: {e}")
            await asyncio.sleep(3)

    if not snapshot_ids:
        log_fail("React loop: no messages found in snapshot, aborting.")
        return

    log_ok(f"React loop: {len(snapshot_ids)} message(s) in snapshot, starting reactions...")
    emoji_idx = 0
    msg_idx   = 0

    while not stop_event.is_set():
        try:
            msg_id = snapshot_ids[msg_idx % len(snapshot_ids)]
            msg_idx += 1
            emoji   = emojis[emoji_idx % len(emojis)]
            emoji_idx += 1

            # URL-encode emoji for the reaction endpoint
            import urllib.parse
            emoji_encoded = urllib.parse.quote(emoji, safe='')

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}/reactions/{emoji_encoded}/@me",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as react_resp:
                    if react_resp.status == 429:
                        body = await react_resp.json()
                        ra = float(body.get("retry_after", 2))
                        log_warn(f"React rate limited, waiting {ra:.1f}s...")
                        await asyncio.sleep(ra + 0.5)
                        msg_idx -= 1   # retry same message
                        emoji_idx -= 1
                        continue
                    elif react_resp.status in (200, 201, 204):
                        log_ok(f"Reacted {emoji} to msg {msg_id}")
                    elif react_resp.status == 404:
                        log_warn(f"Message {msg_id} not found, removing from snapshot")
                        snapshot_ids.remove(msg_id)
                        msg_idx -= 1
                        emoji_idx -= 1
                        if not snapshot_ids:
                            log_fail("React loop: all snapshot messages gone, stopping.")
                            return
                        continue
                    else:
                        log_fail(f"React failed ({react_resp.status}) on msg {msg_id}")

            await asyncio.sleep(delay + random.uniform(0.5, 1.5))

        except asyncio.TimeoutError:
            log_warn("React loop timeout, retrying...")
            await asyncio.sleep(5)
        except Exception as e:
            log_warn(f"React loop error: {e}")
            await asyncio.sleep(5)

_IMAGES_DIR = os.path.join(INPUT_DIR, "images")
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def _pick_image(chance=0.25):
    """Return a random image path from input/images/ with `chance` probability, else None."""
    if random.random() > chance:
        return None
    if not os.path.isdir(_IMAGES_DIR):
        return None
    imgs = [f for f in os.listdir(_IMAGES_DIR)
            if os.path.splitext(f)[1].lower() in _IMAGE_EXTS]
    if not imgs:
        return None
    return os.path.join(_IMAGES_DIR, random.choice(imgs))

# Run the Chat Automator
async def start_chat_loop(tokens, channel_id, delay, smart_mode, stop_event):
    if not tokens:
        log_fail("No tokens to start chat loop")
        return

    log_ok(f"Chat automation activated on channel {channel_id}")

    def _next_idx(exclude=-1, tries=10):
        """Pick a random token index, avoiding exclude."""
        for _ in range(tries):
            i = random.randint(0, len(tokens) - 1)
            if i != exclude:
                return i
        return (exclude + 1) % len(tokens)

    if smart_mode:
        from conversation import ConversationEngine
        engine = ConversationEngine()
        last_sent_id      = None
        last_sent_content = None
        convo_depth       = 0
        max_depth         = random.randint(3, 7)
        last_sender_idx   = -1

        while not stop_event.is_set():
            try:
                if convo_depth == 0 or convo_depth >= max_depth or last_sent_content is None:
                    # ── Starter — try tokens until one succeeds ──────────────
                    msg_content = engine.generate_starter()
                    sent = False
                    for _ in range(min(len(tokens), 5)):
                        idx   = _next_idx(last_sender_idx)
                        token = tokens[idx]
                        tag   = f"Token[{idx}]"
                        log_info(f"{tag} starting thread/starter...")
                        await trigger_typing(token, channel_id)
                        await asyncio.sleep(len(msg_content) * random.uniform(0.04, 0.07) + 0.3)
                        success, msg_id = await send_msg(token, channel_id, msg_content, image_path=_pick_image(0.25))
                        if success:
                            log_ok(f"{tag} sent: {msg_content}")
                            last_sent_id      = msg_id
                            last_sent_content = msg_content
                            last_sender_idx   = idx
                            convo_depth       = 1
                            max_depth         = random.randint(3, 7)
                            sent = True
                            break
                        else:
                            log_fail(f"{tag} failed, trying next token instantly...")
                    if not sent:
                        log_fail("All fallback tokens failed for starter, cooling down...")
                        await asyncio.sleep(3)
                        continue

                else:
                    # ── Reply — try tokens until one succeeds ────────────────
                    msg_content = engine.generate_reply(last_sent_content)
                    reply_to    = last_sent_id
                    sent = False
                    for _ in range(min(len(tokens), 5)):
                        idx   = _next_idx(last_sender_idx)
                        token = tokens[idx]
                        tag   = f"Token[{idx}]"
                        log_info(f"{tag} replying to Token[{last_sender_idx}]...")
                        await trigger_typing(token, channel_id)
                        await asyncio.sleep(len(msg_content) * random.uniform(0.04, 0.07) + 0.3)
                        success, msg_id = await send_msg(token, channel_id, msg_content, reply_to, image_path=_pick_image(0.15))
                        if success:
                            log_ok(f"{tag} sent: {msg_content}")
                            # React to the message being replied to
                            _react_emoji = random.choice(["👍","❤️","🔥","😂","😮","🎉","💯","👀"])
                            asyncio.create_task(add_reaction(token, channel_id, reply_to, _react_emoji))
                            last_sent_id      = msg_id
                            last_sent_content = msg_content
                            last_sender_idx   = idx
                            convo_depth      += 1
                            sent = True
                            break
                        else:
                            log_fail(f"{tag} failed, trying next token instantly...")
                    if not sent:
                        log_fail("All fallback tokens failed for reply, cooling down...")
                        await asyncio.sleep(3)
                        convo_depth = 0   # reset thread on consecutive fail
                        continue

                await asyncio.sleep(delay + random.uniform(0.5, 2.0))
            except Exception as e:
                log_warn(f"Smart chat error: {e}")
                await asyncio.sleep(3)

    else:
        static_msgs = [
            "yo whats up", "anyone alive?", "whats good yall", "how is it going",
            "heyy", "hey", "sup", "chat is quiet", "wsg", "wsp"
        ]
        msg_idx = 0
        while not stop_event.is_set():
            try:
                sent = False
                for attempt in range(min(len(tokens), 5)):
                    idx   = (msg_idx + attempt) % len(tokens)
                    token = tokens[idx]
                    tag   = f"Token[{idx}]"
                    msg_content = random.choice(static_msgs)
                    await trigger_typing(token, channel_id)
                    await asyncio.sleep(len(msg_content) * 0.04 + 0.2)
                    success, _ = await send_msg(token, channel_id, msg_content)
                    if success:
                        log_ok(f"{tag} sent: {msg_content}")
                        msg_idx += 1
                        sent = True
                        break
                    else:
                        log_fail(f"{tag} failed, trying next token instantly...")
                if not sent:
                    msg_idx += 1
                    await asyncio.sleep(2)
                    continue

                await asyncio.sleep(delay + random.uniform(0.5, 2.0))
            except Exception as e:
                log_warn(f"Static chat error: {e}")
                await asyncio.sleep(3)

async def main():
    show_banner()
    cfg    = load_config()
    tokens, raw_map = load_tokens()
    
    if not tokens:
        log_fail("No tokens loaded from input/tokens.txt. Please populate it first.")
        input("  Press Enter to exit...")
        sys.exit(1)
        
    log_info(f"Validating {len(tokens)} token(s)...")

    valid_tokens   = []
    invalid_tokens = []
    _val_lock      = threading.Lock()

    # Semaphore to avoid hitting rate limits with too many parallel requests
    _sem = asyncio.Semaphore(5)

    async def _check(token):
        async with _sem:
            result = await verify_token(token)
            await asyncio.sleep(random.uniform(0.3, 0.7))
            with _val_lock:
                if result:
                    valid_tokens.append(token)
                    log_ok(f"Valid: {token[:20]}... ({result[0]})")
                else:
                    invalid_tokens.append(token)
                    log_fail(f"Invalid/dead token removed: {token[:20]}...")

    await asyncio.gather(*[_check(t) for t in tokens])

    if invalid_tokens:
        # Rewrite tokens.txt keeping only valid lines
        with open(TOKENS_FILE, encoding="utf-8") as f:
            all_lines = f.readlines()

        invalid_set = set(invalid_tokens)
        kept_lines  = []
        for line in all_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                kept_lines.append(line)
                continue
            parts = stripped.split(":")
            tok   = parts[-1] if len(parts) >= 3 else stripped
            if tok not in invalid_set:
                kept_lines.append(line)

        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            f.writelines(kept_lines)

        log_warn(f"Removed {len(invalid_tokens)} invalid token(s) from tokens.txt")

    if not valid_tokens:
        log_fail("No valid tokens remaining. Exiting.")
        input("  Press Enter to exit...")
        sys.exit(1)

    tokens  = valid_tokens
    raw_map = {t: raw_map[t] for t in tokens if t in raw_map}

    info = await verify_token(tokens[0])
    uname, disc = info if info else ("?", "0")
    log_ok(f"Ready: {uname}#{disc} — {len(tokens)} valid token(s)")
    
    # ── target servers
    setup = get_setup(cfg)
    reuse = False
    if setup["invite"]:
        box("SAVED SETUP", ICE)
        log_dim(f'Invite      {setup["invite"]}')
        log_dim(f'Voice       {setup["voice_channel_id"] or "skip"}')
        log_dim(f'Text        {setup["text_channel_id"] or "skip"}')
        log_dim(f'React       {setup["react_channel_id"] or "skip"}')
        log_dim(f'VC          mute={setup["vc_mute"]}  video={setup["vc_video"]}  stream={setup["vc_stream"]}')
        log_dim(f'Chat        delay={setup["chat_delay"]}s  smart={"y" if setup["smart_chat"] else "n"}')
        log_dim(f'Reacts      emojis={setup["react_emojis"]}  delay={setup["react_delay"]}s')
        print()
        reuse = ask("Use saved setup? (y/n)", hint="[y / n] default=y").lower() != "n"

    if not reuse:
        box("INITIALIZATION", EMBER)
        setup["invite"] = ask("Server invite link or code", hint="e.g. https://discord.gg/invite")

    info = resolve_invite(setup["invite"])
    if not info:
        log_fail("Invalid server invite link or code")
        input("  Press Enter to exit...")
        sys.exit(1)

    guild_id = info["guild_id"]
    invite_code = info["invite_code"]
    log_ok(f"Guild identified: {info['guild_name']} ({guild_id})")

    # ── channel configuration
    if not reuse:
        box("TARGET CHANNELS", LAVA)
        setup["voice_channel_id"] = ask("Voice Channel ID", hint="leave empty to skip VC")
        setup["text_channel_id"]  = ask("Text Channel ID",  hint="leave empty to skip Chat")
        setup["react_channel_id"] = ask("React Channel ID", hint="leave empty to skip Reacts")

    vc_id     = str(setup["voice_channel_id"] or "").strip()
    text_id   = str(setup["text_channel_id"]  or "").strip()
    react_id  = str(setup["react_channel_id"] or "").strip()

    if not vc_id and not text_id and not react_id:
        log_fail("Voice, Text and React channels are all empty. Nothing to execute.")
        input(f"  {Fore.WHITE}Press Enter to exit...")
        sys.exit(1)

    if vc_id and not reuse:
        box("VC CONFIGURATION", GOLD)
        setup["vc_mute"] = ask_int("VC Mute amount", hint=f"default={len(tokens)}")
        setup["vc_video"] = ask_int("VC Video amount", hint="default=0")
        setup["vc_stream"] = ask_int("VC Stream amount", hint="default=0")

    mute_c = int(setup["vc_mute"] or 0)
    vid_c = int(setup["vc_video"] or 0)
    str_c = int(setup["vc_stream"] or 0)
    if vc_id and mute_c == 0:
        mute_c = len(tokens)

    if text_id and not reuse:
        box("CHAT CONFIGURATION", PURPLE)
        setup["chat_delay"] = ask_int("Chat Delay in seconds", hint="default=5")
        setup["smart_chat"] = ask("Smart Chat Mode? (y/n)", hint="[y / n] default=y").lower() != "n"

    delay     = int(setup["chat_delay"] or 0) or 5
    smart_opt = bool(setup["smart_chat"])

    if react_id and not reuse:
        box("REACT CONFIGURATION", BLOOD)
        setup["react_emojis"] = ask(
            "Emoji list (comma separated)",
            hint="default=👍,❤️,🔥,😂,😮,🎉,💯,👀"
        ) or "👍,❤️,🔥,😂,😮,🎉,💯,👀"
        setup["react_delay"] = ask_int("Delay between reacts (seconds)", hint="default=3", minimum=1) or 3

    react_emojis = [e.strip() for e in str(setup.get("react_emojis", "👍,❤️,🔥,😂,😮,🎉,💯,👀")).split(",") if e.strip()]
    react_delay  = int(setup.get("react_delay", 3) or 3)

    if not reuse:
        cfg["setup"] = setup
        save_config(cfg)
    divider()

    # 0. Quest Completer — optional skip per batch
    _skip_quest = ask("Skip Quest for this batch? (y/n)", hint="y = skip  n = run").lower()
    _skip_tfa   = ask("Skip 2FA cycle for this batch? (y/n)", hint="y = skip  n = run").lower()
    _equip_hypesquad = ask("Equip random Hypesquad badge? (y/n)", hint="y = equip  n = skip").lower() != "y"
    _skip_join  = ask("Skip Join for this batch? (y/n)", hint="y = skip  n = run").lower()

    qc_cfg = cfg.get("quest_completer", {})
    if _skip_quest != "y" and qc_cfg.get("enabled", True):
        box("QUEST COMPLETER", MINT)
        log_info("Running Quest Completer (enroll + video progress)...")
        completed_quest_ids = run_quest_completer(qc_cfg)
        if completed_quest_ids:
            log_ok(f"Quest Completer finished — {len(completed_quest_ids)} quest(s) processed")
        else:
            log_warn("Quest Completer — no quests completed or found")
        divider()
    else:
        log_warn("Skipping Quest Completer for this batch.")

    # 1. 2FA cycle
    if _skip_tfa == "y":
        log_warn("Skipping 2FA cycle for this batch.")
    else:
        box("2FA CYCLE", MINT)
        tfa_eligible_tokens = [
            t for t in tokens
            if raw_map.get(t, "").count(":") >= 2
        ]
        tfa_skip_count = len(tokens) - len(tfa_eligible_tokens)

        if not tfa_eligible_tokens:
            log_warn(f"2FA cycle — no tokens have email:password prefix, skipping ({tfa_skip_count} plain token(s))")
        else:
            if tfa_skip_count:
                log_dim(f"2FA cycle — skipping {tfa_skip_count} plain token(s) without credentials")
            log_info(f"Running 2FA enable→disable on {len(tfa_eligible_tokens)} token(s)...")

            tfa_ok2   = 0
            tfa_fail2 = 0
            tfa_lock2 = threading.Lock()
            updated_tokens2 = {}

            def _run_tfa(tk):
                nonlocal tfa_ok2, tfa_fail2
                short    = tk[:20] + "..."
                raw_line = raw_map.get(tk, tk)
                try:
                    result = _tfa.tfa_cycle(raw_line)
                    if result:
                        new_tok = result["new_token"]
                        with tfa_lock2:
                            updated_tokens2[tk] = new_tok
                            tfa_ok2 += 1
                        log_ok(f"{short} 2FA cycle done → {new_tok[:20]}...")
                    else:
                        with tfa_lock2:
                            tfa_fail2 += 1
                        log_fail(f"{short} 2FA cycle failed")
                except Exception as e:
                    with tfa_lock2:
                        tfa_fail2 += 1
                    log_fail(f"{short} 2FA cycle error: {e}")

            with ThreadPoolExecutor(max_workers=min(cfg.get("max_workers", 10), len(tfa_eligible_tokens))) as ex:
                futs = [ex.submit(_run_tfa, tk) for tk in tfa_eligible_tokens]
                for f in as_completed(futs):
                    pass

            # Update tokens list and raw_map with new tokens from 2FA cycle
            tokens = [updated_tokens2.get(t, t) for t in tokens]
            for old_tok, new_tok in updated_tokens2.items():
                old_raw = raw_map.pop(old_tok, "")
                if old_raw:
                    raw_map[new_tok] = old_raw.replace(old_tok, new_tok)

            # Write updated tokens back to tokens.txt so new tokens persist
            try:
                with open(TOKENS_FILE, "w", encoding="utf-8") as _f:
                    for tok in tokens:
                        _f.write(raw_map.get(tok, tok) + "\n")
                log_ok(f"tokens.txt updated with {len(updated_tokens2)} new token(s) from 2FA cycle")
            except Exception as _e:
                log_warn(f"Could not write updated tokens to tokens.txt: {_e}")

            log_ok(f"2FA cycle done → success: {tfa_ok2}  failed: {tfa_fail2}  skipped: {tfa_skip_count}")
            divider()

    # 2. Hypesquad badge equipping — optional per batch
    if _equip_hypesquad:
        log_warn("Skipping Hypesquad badge equipping for this batch.")
    else:
        box("HYPESQUAD BADGE", PURPLE)
        log_info(f"Equipping random Hypesquad badge on {len(tokens)} token(s)...")

        hypesquad_ok = 0
        hypesquad_fail = 0
        hypesquad_lock = threading.Lock()

        async def _equip_one(token_idx, token):
            nonlocal hypesquad_ok, hypesquad_fail
            short = token[:20] + "..."
            try:
                success, house_name = await _hypesquad.equip_random_hypesquad(token, max_retries=2)
                with hypesquad_lock:
                    if success:
                        hypesquad_ok += 1
                        log_ok(f"{short} → {house_name}")
                    else:
                        hypesquad_fail += 1
                        reason = house_name or "Unknown error"
                        if "locked" in reason.lower() or "403" in reason:
                            log_fail(f"{short} Account locked/restricted: {reason}")
                        else:
                            log_fail(f"{short} Failed: {reason}")
            except Exception as e:
                with hypesquad_lock:
                    hypesquad_fail += 1
                log_fail(f"{short} Exception: {str(e)[:60]}")
            finally:
                # Rate limit protection
                await asyncio.sleep(random.uniform(0.5, 1.5))

        # Run concurrently with semaphore to avoid rate limiting
        async def _run_all_hypesquad():
            sem = asyncio.Semaphore(3)  # Only 3 concurrent requests
            async def _with_sem(idx, tok):
                async with sem:
                    await _equip_one(idx, tok)
            await asyncio.gather(*[_with_sem(i, t) for i, t in enumerate(tokens)])

        try:
            # We're already in an event loop, so use create_task instead of asyncio.run()
            await _run_all_hypesquad()
        except Exception as e:
            log_fail(f"Hypesquad batch error: {e}")

        log_ok(f"Hypesquad done → success: {hypesquad_ok}  failed: {hypesquad_fail}")
        divider()

    # 3. OAuth2 authorization + join — skippable per batch
    if _skip_join == "y":
        log_warn("Skipping OAuth2 authorization and join for this batch.")
        # Build authed list from plain tokens so deployment works
        authed = [(None, None, t) for t in tokens]
    else:
        box("AUTHORIZATION", EMBER)
        log_info("Authorizing tokens via OAuth...")
        authed = []
        with ThreadPoolExecutor(max_workers=cfg.get("max_workers", 10)) as ex:
            futs = [ex.submit(oauth_authorize, t, cfg) for t in tokens]
            for f in as_completed(futs):
                res = f.result()
                if res:
                    authed.append(res)
        log_ok(f"Authorized: {len(authed)}/{len(tokens)}")

        # 3. Join server via OAuth2 bot
        box("MEMBERSHIP", LAVA)
        bot_token = cfg.get("bot_token", "")
        if not bot_token or "YOUR_BOT_TOKEN" in bot_token:
            log_fail("No valid bot_token in config.json — cannot join members via OAuth2.")
            input("  Press Enter to exit...")
            sys.exit(1)

        joined = 0
        already = 0
        failed  = 0
        log_info(f"Joining {len(authed)} token(s) to guild via OAuth2 bot...")

        for uid, at, tk in authed:
            short = tk[:20] + "..."
            try:
                in_guild = await check_membership(tk, guild_id)
                if in_guild:
                    already += 1
                    joined  += 1
                    log_dim(f"{short} already in guild")
                    continue

                ok = await join_via_oauth2(bot_token, guild_id, uid, at)
                if ok:
                    joined += 1
                    log_ok(f"{short} joined via OAuth2 bot")
                else:
                    failed += 1
                    log_fail(f"{short} join failed (bot PUT returned non-2xx)")
            except Exception as e:
                failed += 1
                log_fail(f"{short} join error: {e}")

            await asyncio.sleep(random.uniform(0.3, 0.8))

        log_ok(f"Membership done → joined: {joined}  already: {already}  failed: {failed}  /  {len(authed)} total")
        if joined == 0:
            log_fail("No tokens could enter the server. Exiting.")
            input("  Press Enter to exit...")
            sys.exit(1)

    # 4. Deployment
    box("DEPLOYMENT", GOLD)
    log_info("Starting automatic deployment...")

    stop_event = asyncio.Event()
    tasks = []

    # Deploy Voice presence if enabled
    if vc_id:
        log_info("Spawning VC joiner processes...")
        for i, a in enumerate(authed):
            mute   = i < mute_c
            video  = mute_c <= i < (mute_c + vid_c)
            stream = (mute_c + vid_c) <= i < (mute_c + vid_c + str_c)
            tasks.append(asyncio.create_task(
                vc_connect(a[2], guild_id, vc_id, mute, video, stream, i, stop_event)))
            await asyncio.sleep(0.3)

    # Deploy Chat presence if enabled
    if text_id:
        log_info("Spawning chat automation process...")
        chat_tokens = [a[2] for a in authed]
        tasks.append(asyncio.create_task(
            start_chat_loop(chat_tokens, text_id, delay, smart_opt, stop_event)))

    # Deploy Onliner — status/presence rotation for all tokens
    box("ONLINER", ICE)
    from onliner import run_onliner_async
    onliner_tokens = [a[2] for a in authed]
    log_info(f"Spawning onliner for {len(onliner_tokens)} token(s)...")
    tasks.append(asyncio.create_task(
        run_onliner_async(onliner_tokens, stop_event)))

    # Deploy React loop if enabled
    if react_id:
        box("REACT AUTOMATION", BLOOD)
        react_token = authed[0][2] if authed else None
        if react_token:
            log_info(f"Spawning react automation for 1 token ({react_token[:20]}...)")
            tasks.append(asyncio.create_task(
                react_loop(react_token, react_id, react_emojis, react_delay, stop_event)))
        else:
            log_fail("No tokens available for react loop")

    log_ok("All processes running. Press Ctrl+C to stop...")
    print("")
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        log_warn("Termination signal received. Cleaning up...")
    finally:
        stop_event.set()
        for t in tasks:
            t.cancel()
        log_ok("All processes stopped successfully.")
        time.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_warn("Exited.")

