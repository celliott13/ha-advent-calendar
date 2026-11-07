"""Advent Calendar: a family-dashboard advent / Hanukkah calendar for Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CARD_FILE,
    MAX_ACTIVITIES,
    DESIGNS,
    DOMAIN,
    FAMILIES,
    MAX_EMOJI,
    MAX_MESSAGE,
    PIN_MAX,
    MAX_TITLE,
    ORDERS,
    SIZES,
    URL_BASE,
    VERSION,
)
from .manager import AdventManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static card file + websocket API once per HA run."""
    www = Path(__file__).parent / "www"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(www), cache_headers=False)]
    )
    frontend.add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={VERSION}")

    websocket_api.async_register_command(hass, ws_get_state)
    websocket_api.async_register_command(hass, ws_verify_pin)
    websocket_api.async_register_command(hass, ws_open_door)
    websocket_api.async_register_command(hass, ws_set_settings)
    websocket_api.async_register_command(hass, ws_set_custom)
    websocket_api.async_register_command(hass, ws_delete_custom)
    websocket_api.async_register_command(hass, ws_set_activities)
    websocket_api.async_register_command(hass, ws_reset)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager = AdventManager(hass, entry)
    await manager.async_load()
    hass.data[DOMAIN] = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN, None)
    return unloaded


PIN = vol.All(str, vol.Length(min=1, max=PIN_MAX))
_PIN_ERRORS = {"invalid_pin": "Incorrect PIN", "locked": "Too many attempts. Try again in a few minutes."}


def _mgr(hass: HomeAssistant, connection, msg) -> AdventManager | None:
    mgr = hass.data.get(DOMAIN)
    if mgr is None:
        connection.send_error(msg["id"], "not_loaded", "Advent Calendar is not set up")
    return mgr


async def _parent(hass, connection, msg) -> AdventManager | None:
    """Return the manager only if the parent PIN in the message verifies (any HA account may try)."""
    if (mgr := _mgr(hass, connection, msg)) is None:
        return None
    try:
        await mgr.async_verify_pin(msg["pin"])
    except ValueError as err:
        connection.send_error(msg["id"], str(err), _PIN_ERRORS.get(str(err), str(err)))
        return None
    return mgr


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_state", vol.Optional("pin"): PIN})
@websocket_api.async_response
async def ws_get_state(hass, connection, msg):
    if "pin" in msg:
        if (mgr := await _parent(hass, connection, msg)) is None:
            return
        connection.send_result(msg["id"], mgr.get_state(True))
        return
    if (mgr := _mgr(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], mgr.get_state(False))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/verify_pin", vol.Required("pin"): PIN})
@websocket_api.async_response
async def ws_verify_pin(hass, connection, msg):
    if await _parent(hass, connection, msg) is not None:
        connection.send_result(msg["id"], {"ok": True})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/open_door", vol.Required("day"): vol.All(int, vol.Range(min=1, max=25))}
)
@websocket_api.async_response
async def ws_open_door(hass, connection, msg):
    if (mgr := _mgr(hass, connection, msg)) is None:
        return
    try:
        result = await mgr.async_open_door(msg["day"])
    except ValueError as err:
        connection.send_error(msg["id"], str(err), str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_settings",
        vol.Required("pin"): PIN,
        vol.Optional("design"): vol.In(DESIGNS),
        vol.Optional("order"): vol.In(ORDERS),
        vol.Optional("sizes"): vol.In(SIZES),
        vol.Optional("title"): vol.All(str, vol.Length(max=MAX_TITLE)),
        vol.Optional("reshuffle"): bool,
    }
)
@websocket_api.async_response
async def ws_set_settings(hass, connection, msg):
    if (mgr := await _parent(hass, connection, msg)) is None:
        return
    changes = {k: v for k, v in msg.items() if k not in ("id", "type", "pin")}
    try:
        await mgr.async_set_settings(**changes)
    except ValueError as err:
        connection.send_error(msg["id"], str(err), str(err))
        return
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_custom",
        vol.Required("pin"): PIN,
        vol.Required("family"): vol.In(FAMILIES),
        vol.Required("day"): vol.All(int, vol.Range(min=1, max=25)),
        vol.Optional("title", default=""): vol.All(str, vol.Length(max=MAX_TITLE)),
        vol.Required("message"): vol.All(str, vol.Length(min=1, max=MAX_MESSAGE)),
        vol.Optional("emoji", default=""): vol.All(str, vol.Length(max=MAX_EMOJI)),
    }
)
@websocket_api.async_response
async def ws_set_custom(hass, connection, msg):
    if (mgr := await _parent(hass, connection, msg)) is None:
        return
    try:
        await mgr.async_set_custom(msg["family"], msg["day"], msg["title"], msg["message"], msg["emoji"])
    except ValueError as err:
        connection.send_error(msg["id"], str(err), str(err))
        return
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_custom",
        vol.Required("pin"): PIN,
        vol.Required("family"): vol.In(FAMILIES),
        vol.Required("day"): vol.All(int, vol.Range(min=1, max=25)),
    }
)
@websocket_api.async_response
async def ws_delete_custom(hass, connection, msg):
    if (mgr := await _parent(hass, connection, msg)) is None:
        return
    await mgr.async_delete_custom(msg["family"], msg["day"])
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/reset", vol.Required("pin"): PIN})
@websocket_api.async_response
async def ws_reset(hass, connection, msg):
    if (mgr := await _parent(hass, connection, msg)) is None:
        return
    await mgr.async_reset_opened()
    connection.send_result(msg["id"], {})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_activities",
        vol.Required("pin"): PIN,
        vol.Required("family"): vol.In(FAMILIES),
        # null restores the built-in activities
        vol.Required("activities"): vol.Any(None, vol.All([vol.All(str, vol.Length(max=MAX_MESSAGE))], vol.Length(max=MAX_ACTIVITIES))),
    }
)
@websocket_api.async_response
async def ws_set_activities(hass, connection, msg):
    if (mgr := await _parent(hass, connection, msg)) is None:
        return
    try:
        await mgr.async_set_activities(msg["family"], msg["activities"])
    except ValueError as err:
        connection.send_error(msg["id"], str(err), str(err))
        return
    connection.send_result(msg["id"], {})
