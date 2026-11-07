"""Target-based triggers.

These show up in the automation editor's "Add trigger" list: type "Advent" in the search box (or expand the
Advent Calendar device under "By target") and pick the trigger. They fire on the same events as the older
device triggers in device_trigger.py, which are kept so existing automations keep working.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_OPTIONS, CONF_TARGET
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.trigger import Trigger, TriggerActionRunner, TriggerConfig
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, EVENT_DOOR_OPENED

_TARGET_SCHEMA = vol.Schema(cv.TARGET_FIELDS)
_DAY = vol.All(vol.Coerce(int), vol.Range(min=1, max=25))


def _iso_date(value: Any) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as err:
        raise vol.Invalid("Enter a valid date") from err


class _AdventTrigger(Trigger):
    """Common bits. The target only exists so the editor can list the trigger under the Advent Calendar device."""

    OPTIONS: dict = {}

    @classmethod
    async def async_validate_config(cls, hass: HomeAssistant, config: ConfigType) -> ConfigType:
        return vol.Schema(
            {
                vol.Optional(CONF_TARGET): _TARGET_SCHEMA,
                vol.Optional(CONF_OPTIONS, default=dict): cls.OPTIONS,
            }
        )(config)

    def __init__(self, hass: HomeAssistant, config: TriggerConfig) -> None:
        super().__init__(hass, config)
        self._options = config.options or {}


class _OpenedTrigger(_AdventTrigger):
    """Fires when a door is opened (optionally only a certain one)."""

    def _matches(self, data: dict) -> bool:
        return True

    async def async_attach_runner(self, run_action: TriggerActionRunner, did_not_trigger=None) -> CALLBACK_TYPE:
        @callback
        def _on_open(event: Event) -> None:
            data = event.data
            if not self._matches(data):
                return
            run_action(
                {k: data.get(k) for k in ("day", "date", "family", "design", "custom", "title", "finale")},
                f"Advent Calendar door {data.get('day')} opened",
                event.context,
            )

        return self._hass.bus.async_listen(EVENT_DOOR_OPENED, _on_open)


class DoorOpened(_OpenedTrigger):
    """Any door is opened."""


class DoorOpenedDay(_OpenedTrigger):
    OPTIONS = {vol.Required("day"): _DAY}

    def _matches(self, data: dict) -> bool:
        return data.get("day") == int(self._options["day"])


class DoorOpenedOnDate(_OpenedTrigger):
    """The door dated <date> is opened, on that date or any later day (catch-up opens count)."""

    OPTIONS = {vol.Required("date"): _iso_date}

    def _matches(self, data: dict) -> bool:
        return data.get("date") == self._options["date"]


class FinaleOpened(_OpenedTrigger):
    def _matches(self, data: dict) -> bool:
        return bool(data.get("finale"))


class CustomDoorOpened(_OpenedTrigger):
    def _matches(self, data: dict) -> bool:
        return bool(data.get("custom"))


class DoorWaitingOnDate(_AdventTrigger):
    """Fires just after midnight on <date>, when that date's door becomes available."""

    OPTIONS = {vol.Required("date"): _iso_date}

    async def async_attach_runner(self, run_action: TriggerActionRunner, did_not_trigger=None) -> CALLBACK_TYPE:
        target = self._options["date"]

        @callback
        def _tick(now) -> None:
            if now.date().isoformat() != target:
                return
            mgr = self._hass.data.get(DOMAIN)
            if mgr is None:
                return
            state = mgr.get_state(False)
            door = next((d for d in state["days"] if d["date"] == target), None)
            if door is None:
                return  # the active calendar has no door on that date
            run_action(
                {"day": door["day"], "date": target, "family": state["family"]},
                f"Advent Calendar door {door['day']} is waiting ({target})",
            )

        return async_track_time_change(self._hass, _tick, hour=0, minute=0, second=1)


async def async_get_triggers(hass: HomeAssistant) -> dict[str, type[Trigger]]:
    return {
        "door_opened": DoorOpened,
        "door_opened_day": DoorOpenedDay,
        "door_opened_on_date": DoorOpenedOnDate,
        "door_waiting_on_date": DoorWaitingOnDate,
        "finale_opened": FinaleOpened,
        "custom_door_opened": CustomDoorOpened,
    }
