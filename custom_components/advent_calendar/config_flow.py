"""Config flow: single instance. The parent PIN is set here and changed via options."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

from .const import CONF_PIN_HASH, DOMAIN, PIN_MAX, PIN_MIN
from .manager import hash_pin

CONF_PIN = "pin"


def _pin_schema(default: str | None = None) -> vol.Schema:
    return vol.Schema({vol.Required(CONF_PIN): str})


def _valid(pin: str) -> bool:
    return pin.isdigit() and PIN_MIN <= len(pin) <= PIN_MAX


class AdventCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return AdventOptionsFlow()

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            pin = user_input[CONF_PIN].strip()
            if _valid(pin):
                hashed = await self.hass.async_add_executor_job(hash_pin, pin)
                return self.async_create_entry(title="Advent Calendar", data={CONF_PIN_HASH: hashed})
            errors[CONF_PIN] = "invalid_pin"
        return self.async_show_form(step_id="user", data_schema=_pin_schema(), errors=errors)


class AdventOptionsFlow(OptionsFlow):
    """Change the parent PIN (Home Assistant admins only, as with all options flows)."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            pin = user_input[CONF_PIN].strip()
            if _valid(pin):
                hashed = await self.hass.async_add_executor_job(hash_pin, pin)
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data={**self.config_entry.data, CONF_PIN_HASH: hashed}
                )
                return self.async_create_entry(data={})
            errors[CONF_PIN] = "invalid_pin"
        return self.async_show_form(step_id="init", data_schema=_pin_schema(), errors=errors)
