"""Binary sensor: ON while at least one available door has not been opened yet."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from ._entities import AdventEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DoorWaitingSensor(hass, entry, "door_waiting")])


class DoorWaitingSensor(AdventEntity, BinarySensorEntity):
    _attr_icon = "mdi:door-closed"

    def _waiting(self) -> list[int]:
        return [d["day"] for d in self._days() if d["available"] and not d["opened"]]

    @property
    def is_on(self) -> bool:
        return bool(self._waiting())

    @property
    def extra_state_attributes(self) -> dict:
        return {"waiting_days": self._waiting()}
