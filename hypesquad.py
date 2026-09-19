"""
hypesquad.py — Random Hypesquad badge equipping for Discord accounts

Hypesquad badges available:
  1 = House of Brilliance
  2 = House of Bravery
  3 = House of Balance
  
Safe and conservative implementation for account protection.
"""

import random
import time
import asyncio
import aiohttp
from typing import Optional, Tuple

# Hypesquad house IDs
HYPESQUAD_HOUSES = [1, 2, 3]
HYPESQUAD_NAMES = {
    1: "House of Brilliance",
    2: "House of Bravery", 
    3: "House of Balance"
}


async def equip_random_hypesquad(token: str, max_retries: int = 2) -> Tuple[bool, Optional[str]]:
    """
    Equip random Hypesquad badge on account.
    
    Args:
        token: Discord user token
        max_retries: Max attempts before giving up (conservative for account safety)
    
    Returns:
        (success: bool, house_name: str or None)
    """
    house_id = random.choice(HYPESQUAD_HOUSES)
    house_name = HYPESQUAD_NAMES[house_id]
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {"house_id": house_id}
    
    attempt = 0
    while attempt < max_retries:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://discord.com/api/v10/hypesquad/online",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    
                    if resp.status in (200, 204):
                        return True, house_name
                    
                    elif resp.status == 429:
                        # Rate limited - wait and retry
                        try:
                            body = await resp.json()
                            ra = float(body.get("retry_after", 2))
                        except:
                            ra = 2.0
                        
                        await asyncio.sleep(ra + 0.5)
                        attempt += 1
                        continue
                    
                    elif resp.status == 401:
                        return False, "Invalid token"
                    
                    elif resp.status == 403:
                        return False, "Account locked/restricted"
                    
                    elif resp.status in (400, 422):
                        try:
                            err = await resp.json()
                            msg = err.get("message", f"HTTP {resp.status}")
                        except:
                            msg = f"HTTP {resp.status}"
                        return False, msg
                    
                    else:
                        attempt += 1
                        if attempt < max_retries:
                            await asyncio.sleep(1 + random.uniform(0, 1))
                            continue
                        return False, f"HTTP {resp.status}"
        
        except asyncio.TimeoutError:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    return False, "Max retries exceeded"


async def ask_equip_hypesquad() -> bool:
    """
    Ask user if they want to equip Hypesquad badges.
    
    Returns:
        True if user wants to equip, False to skip
    """
    while True:
        user_input = input(
            "\n[?] Equip random Hypesquad badge on accounts? (y/n): "
        ).strip().lower()
        
        if user_input in ('y', 'yes'):
            return True
        elif user_input in ('n', 'no'):
            return False
        else:
            print("    [!] Please enter 'y' or 'n'")
