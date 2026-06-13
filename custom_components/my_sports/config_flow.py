"""Config flow for MySports integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from requests.exceptions import RequestException

from .mysports_api import MySportsAPI
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_CALENDAR_SCAN_INTERVAL,
    DEFAULT_CALENDAR_SCAN_INTERVAL,
    MIN_CALENDAR_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MySports."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = MySportsAPI(user_input["username"], user_input["password"])
            try:
                await self.hass.async_add_executor_job(api.login)
                studios = await self.hass.async_add_executor_job(api.get_studios)

                if not studios:
                    errors["base"] = "no_studios_found"
                else:
                    await self.async_set_unique_id(user_input["username"])
                    self._abort_if_unique_id_configured()

                    data = {**user_input, "studios": studios}
                    return self.async_create_entry(
                        title=user_input["username"],
                        data=data,
                        options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
                    )
            except ValueError:
                errors["base"] = "invalid_auth"
            except RequestException:
                errors["base"] = "cannot_connect"
            except (RuntimeError, HomeAssistantError):
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauthentication dialog."""
        errors: dict[str, str] = {}
        entry = self._reauth_entry

        if user_input is not None:
            api = MySportsAPI(user_input["username"], user_input["password"])
            try:
                await self.hass.async_add_executor_job(api.login)
                studios = await self.hass.async_add_executor_job(api.get_studios)

                if not studios:
                    errors["base"] = "no_studios_found"
                else:
                    # Update entry data with new credentials and studios
                    new_data = dict(entry.data)
                    new_data.update(user_input)
                    new_data["studios"] = studios
                    self.hass.config_entries.async_update_entry(entry, data=new_data)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
            except ValueError:
                errors["base"] = "invalid_auth"
            except RequestException:
                errors["base"] = "cannot_connect"
            except (RuntimeError, HomeAssistantError):
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required("username", default=entry.data["username"]): str,
                vol.Required("password"): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle MySports options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_calendar_interval = self._entry.options.get(
            CONF_CALENDAR_SCAN_INTERVAL, DEFAULT_CALENDAR_SCAN_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                ),
                vol.Required(
                    CONF_CALENDAR_SCAN_INTERVAL, default=current_calendar_interval
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_CALENDAR_SCAN_INTERVAL)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
