"""Device triggers: pick them from the Advent Calendar device when building an automation."""
from __future__ import annotations

from datetime import date

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HassJob, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, EVENT_DOOR_OPENED

CONF_DAY = "day"
CONF_DATE = "date"
T_ANY = "door_opened"
T_DAY = "door_opened_day"
T_FINALE = "finale_opened"
T_CUSTOM = "custom_door_opened"
T_OPENED_DATE = "door_opened_on_date"      # the door dated <date> has been opened
T_WAITING_DATE = "door_waiting_on_date"    # the door dated <date> has just become available (waiting to be opened)
TRIGGER_TYPES = (T_ANY, T_DAY, T_FINALE, T_CUSTOM, T_OPENED_DATE, T_WAITING_DATE)
DATE_TYPES = (T_OPENED_DATE, T_WAITING_DATE)


def _iso_date(value) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as err:
        raise vol.Invalid("Enter a valid date") from err


TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Optional(CONF_DAY): vol.All(vol.Coerce(int), vol.Range(min=1, max=25)),
        vol.Optional(CONF_DATE): _iso_date,
    }
)


async def async_validate_trigger_config(hass: HomeAssistant, config: ConfigType) -> ConfigType:
    config = TRIGGER_SCHEMA(config)
    if config[CONF_TYPE] == T_DAY and CONF_DAY not in config:
        raise vol.Invalid("A day number is required for this trigger")
    if config[CONF_TYPE] in DATE_TYPES and CONF_DATE not in config:
        raise vol.Invalid("A date is required for this trigger")
    return config


async def async_get_triggers(hass: HomeAssistant, device_id: str) -> list[dict]:
    device = dr.async_get(hass).async_get(device_id)
    if device is None or not any(i[0] == DOMAIN for i in device.identifiers):
        return []
    return [
        {CONF_PLATFORM: "device", CONF_DOMAIN: DOMAIN, CONF_DEVICE_ID: device_id, CONF_TYPE: t}
        for t in TRIGGER_TYPES
    ]


async def async_get_trigger_capabilities(hass: HomeAssistant, config: ConfigType) -> dict[str, vol.Schema]:
    if config[CONF_TYPE] == T_DAY:
        return {"extra_fields": vol.Schema({vol.Required(CONF_DAY, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=25))})}
    if config[CONF_TYPE] in DATE_TYPES:
        return {"extra_fields": vol.Schema({vol.Required(CONF_DATE): selector.DateSelector()})}
    return {}


async def async_attach_trigger(
    hass: HomeAssistant, config: ConfigType, action: TriggerActionType, trigger_info: TriggerInfo
) -> CALLBACK_TYPE:
    t = config[CONF_TYPE]
    if t == T_WAITING_DATE:
        return _attach_waiting(hass, config, action, trigger_info)

    data: dict = {}
    if t == T_DAY:
        data = {CONF_DAY: int(config[CONF_DAY])}
    elif t == T_FINALE:
        data = {"finale": True}
    elif t == T_CUSTOM:
        data = {"custom": True}
    elif t == T_OPENED_DATE:
        data = {CONF_DATE: config[CONF_DATE]}
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_DOOR_OPENED,
            event_trigger.CONF_EVENT_DATA: data,
        }
    )
    return await event_trigger.async_attach_trigger(hass, event_config, action, trigger_info, platform_type="device")


def _attach_waiting(hass: HomeAssistant, config: ConfigType, action: TriggerActionType, trigger_info: TriggerInfo) -> CALLBACK_TYPE:
    """Fire just after midnight on <date>, when that date's door becomes available."""
    target = config[CONF_DATE]
    job = HassJob(action, f"advent_calendar waiting trigger {target}")
    trigger_data = trigger_info["trigger_data"]

    @callback
    def _tick(now) -> None:
        if now.date().isoformat() != target:
            return
        mgr = hass.data.get(DOMAIN)
        if mgr is None:
            return
        state = mgr.get_state(False)
        door = next((d for d in state["days"] if d["date"] == target), None)
        if door is None:
            return  # the active calendar has no door on that date
        hass.async_run_hass_job(
            job,
            {
                "trigger": {
                    **trigger_data,
                    CONF_PLATFORM: "device",
                    CONF_DOMAIN: DOMAIN,
                    CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                    CONF_TYPE: T_WAITING_DATE,
                    CONF_DATE: target,
                    CONF_DAY: door["day"],
                    "family": state["family"],
                    "description": f"Advent Calendar door {door['day']} is waiting ({target})",
                }
            },
        )

    return async_track_time_change(hass, _tick, hour=0, minute=0, second=1)
