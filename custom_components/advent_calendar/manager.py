"""State manager for Advent Calendar: persistence + business rules."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import random
import time
from datetime import date
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .calendar_logic import (
    build_days,
    days_in_family,
    door_available,
    family_for_design,
)
from .const import (
    CONF_PIN_HASH,
    DEFAULT_SETTINGS,
    DESIGNS,
    EVENT_DOOR_OPENED,
    EVENT_UPDATED,
    MAX_ACTIVITIES,
    MAX_EMOJI,
    MAX_MESSAGE,
    MAX_TITLE,
    ORDERS,
    PIN_LOCKOUT_SECONDS,
    PIN_MAX_FAILS,
    SIZES,
    STORAGE_KEY,
    STORAGE_VERSION,
)


def hash_pin(pin: str) -> str:
    """Salted scrypt hash, stored as 'salt$hash' (hex)."""
    salt = os.urandom(16)
    return salt.hex() + "$" + hashlib.scrypt(pin.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def check_pin_hash(pin: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        digest = hashlib.scrypt(pin.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


class AdventManager:
    """Owns persisted state and enforces the rules."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry | None = None) -> None:
        self.hass = hass
        self.entry = entry
        self._fails = 0
        self._locked_until = 0.0
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {}

    # ---- lifecycle -------------------------------------------------
    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.data = {
            "settings": {**DEFAULT_SETTINGS, **stored.get("settings", {})},
            # {"advent:2026": [1,2,3], "menorah:2026": [1]}
            "opened": stored.get("opened", {}),
            # {"advent:5": {"title":..., "message":..., "emoji":...}}
            "custom": stored.get("custom", {}),
            # {"advent": ["Hot cocoa break!", ...]} ; a family with no entry uses the built-in activities
            "activities": stored.get("activities", {}),
        }

    async def _save_and_notify(self) -> None:
        await self._store.async_save(self.data)
        self.hass.bus.async_fire(EVENT_UPDATED, {})

    # ---- parent PIN ------------------------------------------------
    async def async_verify_pin(self, pin: str) -> None:
        """Raise ValueError('locked' | 'invalid_pin') unless the parent PIN matches.

        Enforced server-side for every parent action, so it works for any HA account.
        Global lockout after repeated failures to slow down guessing by kids.
        """
        if time.monotonic() < self._locked_until:
            raise ValueError("locked")
        stored = (self.entry.data.get(CONF_PIN_HASH) if self.entry else None) or ""
        ok = bool(stored) and await self.hass.async_add_executor_job(check_pin_hash, pin, stored)
        if not ok:
            self._fails += 1
            if self._fails >= PIN_MAX_FAILS:
                self._fails = 0
                self._locked_until = time.monotonic() + PIN_LOCKOUT_SECONDS
            raise ValueError("invalid_pin")
        self._fails = 0

    # ---- helpers ---------------------------------------------------
    def today(self) -> date:
        from homeassistant.util import dt as dt_util

        return dt_util.now().date()

    @staticmethod
    def _opened_key(family: str, year: int) -> str:
        return f"{family}:{year}"

    @staticmethod
    def _custom_key(family: str, day: int) -> str:
        return f"{family}:{day}"

    def _opened_list(self, family: str, year: int) -> list[int]:
        return self.data["opened"].get(self._opened_key(family, year), [])

    # ---- reads -----------------------------------------------------
    def get_state(self, is_parent: bool, today: date | None = None) -> dict[str, Any]:
        today = today or self.today()
        settings = self.data["settings"]
        family = family_for_design(settings["design"])
        year = today.year
        opened = set(self._opened_list(family, year))
        days = []
        for d in build_days(family, year):
            n = d["day"]
            custom = self.data["custom"].get(self._custom_key(family, n))
            item: dict[str, Any] = {
                **d,
                "opened": n in opened,
                "available": door_available(d["date"], today),
                "has_custom": custom is not None,
            }
            # Never send surprise content for unopened doors unless the parent PIN was verified.
            if custom is not None and (n in opened or is_parent):
                item["custom"] = custom
            days.append(item)
        return {
            "settings": settings,
            "activities": {f: self.data["activities"].get(f) for f in ("advent", "menorah")},
            "family": family,
            "year": year,
            "today": today.isoformat(),
            "days": days,
            "is_parent": is_parent,
        }

    # ---- writes ----------------------------------------------------
    async def async_open_door(self, day: int, today: date | None = None) -> dict[str, Any]:
        today = today or self.today()
        settings = self.data["settings"]
        family = family_for_design(settings["design"])
        year = today.year
        if not 1 <= day <= days_in_family(family):
            raise ValueError("invalid_day")
        door = next(d for d in build_days(family, year) if d["day"] == day)
        if not door_available(door["date"], today):
            raise ValueError("not_yet")
        key = self._opened_key(family, year)
        lst = self.data["opened"].setdefault(key, [])
        newly = day not in lst
        if newly:
            lst.append(day)
            lst.sort()
            await self._save_and_notify()
            custom = self.data["custom"].get(self._custom_key(family, day))
            self.hass.bus.async_fire(
                EVENT_DOOR_OPENED,
                {
                    "day": day,
                    "family": family,
                    "design": settings["design"],
                    "date": door["date"],
                    "custom": custom is not None,
                    "title": (custom or {}).get("title"),
                    "finale": day == days_in_family(family),
                },
            )
        return {"newly_opened": newly}

    async def async_set_settings(self, **changes: Any) -> None:
        s = self.data["settings"]
        if "design" in changes:
            if changes["design"] not in DESIGNS:
                raise ValueError("invalid_design")
            s["design"] = changes["design"]
        if "order" in changes:
            if changes["order"] not in ORDERS:
                raise ValueError("invalid_order")
            s["order"] = changes["order"]
        if "sizes" in changes:
            if changes["sizes"] not in SIZES:
                raise ValueError("invalid_sizes")
            s["sizes"] = changes["sizes"]
        if "title" in changes:
            s["title"] = str(changes["title"])[:MAX_TITLE]
        if changes.get("reshuffle"):
            s["shuffle_seed"] = random.randint(1, 2**31 - 1)
        await self._save_and_notify()

    async def async_set_custom(
        self, family: str, day: int, title: str, message: str, emoji: str
    ) -> None:
        if not 1 <= day <= days_in_family(family):
            raise ValueError("invalid_day")
        self.data["custom"][self._custom_key(family, day)] = {
            "title": title.strip()[:MAX_TITLE],
            "message": message.strip()[:MAX_MESSAGE],
            "emoji": emoji.strip()[:MAX_EMOJI] or "🎁",
        }
        await self._save_and_notify()

    async def async_set_activities(self, family: str, activities: list[str] | None) -> None:
        """Replace a family's activity list (None restores the built-in defaults)."""
        if activities is None:
            self.data["activities"].pop(family, None)
        else:
            cleaned = [a.strip()[:MAX_MESSAGE] for a in activities if a.strip()]
            limit = days_in_family(family) - 1  # the last door is always the finale
            if len(cleaned) > min(limit, MAX_ACTIVITIES):
                raise ValueError("too_many_activities")
            self.data["activities"][family] = cleaned
        await self._save_and_notify()

    async def async_delete_custom(self, family: str, day: int) -> None:
        self.data["custom"].pop(self._custom_key(family, day), None)
        await self._save_and_notify()

    async def async_reset_opened(self, today: date | None = None) -> None:
        """Clear opened doors for the current year (all families)."""
        year = (today or self.today()).year
        for key in [k for k in self.data["opened"] if k.endswith(f":{year}")]:
            del self.data["opened"][key]
        await self._save_and_notify()
