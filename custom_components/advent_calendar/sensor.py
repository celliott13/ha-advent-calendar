"""Sensor: how many doors have been opened."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass

from ._entities import AdventEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DoorsOpenedSensor(hass, entry, "doors_opened")])


class DoorsOpenedSensor(AdventEntity, SensorEntity):
    _attr_icon = "mdi:gift-open"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        return sum(1 for d in self._days() if d["opened"])

    @property
    def extra_state_attributes(self) -> dict:
        st = self._mgr.get_state(False)
        days = st["days"]
        return {
            "calendar": st["family"],
            "design": st["settings"]["design"],
            "total_doors": len(days),
            "opened_days": [d["day"] for d in days if d["opened"]],
        }
