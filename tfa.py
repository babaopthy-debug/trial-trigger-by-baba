"""
tfa.py — 2FA enable / disable helpers for X-Trail
Requires: pyotp, curl_cffi

Token formats supported:
  - email:password:token          (plain, for enable)
  - token                         (no email/pass — 2FA skipped)

enable_2fa(email, password, token)  → dict | None
    Returns {"token": new_token, "secret": secret, "backups": [...]}

disable_2fa(token, secret)          → str | None
    Returns new_token after disabling

tfa_cycle(raw_line)                 → dict | None
    Full enable→disable in one call.
    Returns {"new_token": ..., "email": ..., "password": ...}
"""

import json
import time
import uuid
import base64
import random
import pyotp
from curl_cffi.requests import Session

# ── Discord headers ────────────────────────────────────────────────────────────
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.7977.64 Safari/537.36"
)
_BUILD = 605146


def _xsup() -> str:
    p = {
        "os": "Windows", "browser": "Chrome", "device": "",
        "system_locale": "en-US", "has_client_mods": False,
        "browser_user_agent": _UA, "browser_version": "152.0.7977.64",
        "os_version": "10", "referrer": "", "referring_domain": "",
        "referrer_current": "", "referring_domain_current": "",
        "release_channel": "stable", "client_build_number": _BUILD,
        "client_event_source": None,
        "client_launch_id": str(uuid.uuid4()),
        "launch_signature": str(uuid.uuid4()),
        "client_heartbeat_session_id": str(uuid.uuid4()),
        "client_app_state": "focused",
        "design_id": 0,
    }
    return base64.b64encode(json.dumps(p, separators=(",", ":")).encode()).decode()


def _headers(token: str, mfa_token: str = None) -> dict:
    h = {
        "Authorization":       token,
        "Content-Type":        "application/json",
        "User-Agent":          _UA,
        "X-Super-Properties":  _xsup(),
        "X-Discord-Locale":    "en-US",
        "X-Discord-Timezone":  "America/New_York",
        "X-Debug-Options":     "bugReporterEnabled",
        "Referer":             "https://discord.com/channels/@me",
        "Origin":              "https://discord.com",
        "sec-ch-ua":           '"Google Chrome";v="152", "Not-A.Brand";v="8", "Chromium";v="152"',
        "sec-ch-ua-mobile":    "?0",
        "sec-ch-ua-platform":  '"Windows"',
        "sec-fetch-dest":      "empty",
        "sec-fetch-mode":      "cors",
        "sec-fetch-site":      "same-origin",
    }
    if mfa_token:
        h["X-Discord-MFA-Authorization"] = mfa_token
    return h


def _cj(obj) -> str:
    return json.dumps(obj, separators=(",", ":"))


# ── Core functions ─────────────────────────────────────────────────────────────

def enable_2fa(email: str, password: str, token: str,
               proxy: str = None) -> dict | None:
    """
    Enable TOTP 2FA on a Discord account.
    Returns {"token": new_token, "secret": secret, "backups": [...]} or None.
    """
    secret = pyotp.random_base32(32)
    totp   = pyotp.TOTP(secret)

    proxies = {"https": proxy, "http": proxy} if proxy else None

    with Session(impersonate="chrome", proxies=proxies) as s:

        # ── Attempt 1: try enabling directly (accounts without 2FA) ───────────
        code = totp.now()
        r = s.post(
            "https://discord.com/api/v10/users/@me/mfa/totp/enable",
            data=_cj({"code": code, "secret": secret}),
            headers=_headers(token),
        )

        if r.status_code == 200:
            data    = r.json()
            backups = [b["code"] for b in data.get("backup_codes", [])]
            return {"token": data.get("token", token), "secret": secret, "backups": backups}

        if r.status_code == 429:
            ra = r.json().get("retry_after", 5)
            time.sleep(float(ra) + 0.5)
            return enable_2fa(email, password, token, proxy)

        d = r.json()
        if r.status_code != 401 or "mfa" not in d:
            return None  # unexpected error

        # ── Need MFA ticket (account already requires password confirm) ────────
        ticket = d["mfa"]["ticket"]

        # Confirm with password
        r2 = s.post(
            "https://discord.com/api/v10/mfa/finish",
            data=_cj({"ticket": ticket, "mfa_type": "password", "data": password}),
            headers=_headers(token),
        )
        if r2.status_code != 200 or "token" not in r2.json():
            return None

        mfa_token = r2.json()["token"]

        # ── Attempt 2: enable with MFA token ──────────────────────────────────
        code = totp.now()
        r3 = s.post(
            "https://discord.com/api/v10/users/@me/mfa/totp/enable",
            data=_cj({"code": code, "secret": secret}),
            headers=_headers(token, mfa_token=mfa_token),
        )

        # TOTP code expired — wait for next window and retry once
        if r3.status_code == 400 and r3.json().get("code") == 60008:
            time.sleep(31)
            code = totp.now()
            r3 = s.post(
                "https://discord.com/api/v10/users/@me/mfa/totp/enable",
                data=_cj({"code": code, "secret": secret}),
                headers=_headers(token, mfa_token=mfa_token),
            )

        if r3.status_code == 429:
            ra = r3.json().get("retry_after", 5)
            time.sleep(float(ra) + 0.5)
            return enable_2fa(email, password, token, proxy)

        if r3.status_code != 200:
            return None

        data    = r3.json()
        backups = [b["code"] for b in data.get("backup_codes", [])]
        return {"token": data.get("token", token), "secret": secret, "backups": backups}


def disable_2fa(token: str, secret: str, proxy: str = None) -> str | None:
    """
    Disable TOTP 2FA using the TOTP secret.
    Returns the new token string, or None on failure.
    """
    totp    = pyotp.TOTP(secret)
    proxies = {"https": proxy, "http": proxy} if proxy else None

    with Session(impersonate="chrome", proxies=proxies) as s:

        # ── Step 1: trigger disable → get MFA ticket ──────────────────────────
        r = s.post(
            "https://discord.com/api/v10/users/@me/mfa/totp/disable",
            data=_cj({}),
            headers=_headers(token),
        )

        if r.status_code == 200:
            return r.json().get("token", token)

        if r.status_code == 429:
            ra = r.json().get("retry_after", 5)
            time.sleep(float(ra) + 0.5)
            return disable_2fa(token, secret, proxy)

        d = r.json()
        if r.status_code != 401 or "mfa" not in d or "ticket" not in d["mfa"]:
            return None

        ticket = d["mfa"]["ticket"]

        # ── Step 2: authenticate with TOTP code ───────────────────────────────
        mfa_token = None
        for attempt in range(3):
            code = totp.now()
            r2 = s.post(
                "https://discord.com/api/v10/mfa/finish",
                data=_cj({"ticket": ticket, "mfa_type": "totp", "data": code}),
                headers=_headers(token),
            )
            if r2.status_code == 200:
                mfa_token = r2.json().get("token")
                break
            if r2.status_code == 400 and r2.json().get("code") == 60008:
                # Code expired, wait for next 30s window
                time.sleep(31)
                continue
            if r2.status_code == 429:
                ra = r2.json().get("retry_after", 5)
                time.sleep(float(ra) + 0.5)
                continue
            break   # any other error — stop retrying

        if not mfa_token:
            return None

        # ── Step 3: disable with MFA token ────────────────────────────────────
        r3 = s.post(
            "https://discord.com/api/v10/users/@me/mfa/totp/disable",
            data=_cj({}),
            headers=_headers(token, mfa_token=mfa_token),
        )

        if r3.status_code == 429:
            ra = r3.json().get("retry_after", 5)
            time.sleep(float(ra) + 0.5)
            return disable_2fa(token, secret, proxy)

        if r3.status_code == 200:
            return r3.json().get("token", token)

        return None


# ── High-level cycle ───────────────────────────────────────────────────────────

def tfa_cycle(raw_line: str, proxy: str = None) -> dict | None:
    """
    Full enable → disable cycle from a raw token line.

    Accepted formats:
      email:password:token
      token  (skipped — no credentials to confirm password step)

    Returns:
      {"new_token": str, "email": str, "password": str}  on success
      None on failure / skipped
    """
    line = raw_line.strip()
    if not line:
        return None

    parts = line.split(":")
    if len(parts) >= 3:
        email    = parts[0]
        password = parts[1]
        token    = ":".join(parts[2:])
    else:
        # plain token — cannot do password confirmation, skip
        return None

    # ── Enable ────────────────────────────────────────────────────────────────
    import logger as _L
    short = token[:20] + "..."

    _L.info("", f"2FA enabling → {short}")
    enable_result = enable_2fa(email, password, token, proxy=proxy)
    if not enable_result:
        _L.error("", f"2FA enable failed → {short}")
        return None

    mid_token = enable_result["token"]
    secret    = enable_result["secret"]
    _L.success("", f"2FA enabled → new token: {mid_token[:20]}...")

    # Brief pause between enable and disable
    time.sleep(random.uniform(1.0, 2.5))

    # ── Disable ───────────────────────────────────────────────────────────────
    _L.info("", f"2FA disabling → {mid_token[:20]}...")
    new_token = disable_2fa(mid_token, secret, proxy=proxy)
    if not new_token:
        _L.error("", f"2FA disable failed → {mid_token[:20]}...")
        return None

    _L.success("", f"2FA disabled → final token: {new_token[:20]}...")
    return {"new_token": new_token, "email": email, "password": password}
