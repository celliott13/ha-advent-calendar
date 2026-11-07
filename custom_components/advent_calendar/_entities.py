"""Shared entity base: one Device per config entry, refreshed whenever the calendar changes."""
from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, EVENT_UPDATED, VERSION
from .manager import AdventManager


def device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Advent Calendar",
        manufacturer="Community",
        model="Advent / Hanukkah Calendar",
        sw_version=VERSION,
        entry_type=DeviceEntryType.SERVICE,
    )


class AdventEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str) -> None:
        self._mgr: AdventManager = hass.data[DOMAIN]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = device_info(entry)

    async def async_added_to_hass(self) -> None:
        @callback
        def _changed(*_args) -> None:
            self.async_write_ha_state()

        self.async_on_remove(self.hass.bus.async_listen(EVENT_UPDATED, _changed))
        # the "today" side of the state changes at midnight
        self.async_on_remove(async_track_time_change(self.hass, _changed, hour=0, minute=0, second=5))

    def _days(self) -> list[dict]:
        return self._mgr.get_state(False)["days"]
