"""Config flow for Cardio4HA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_BATTERY_CRITICAL,
    CONF_BATTERY_WARNING,
    CONF_BATTERY_LOW,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_BATTERY_CRITICAL,
    DEFAULT_BATTERY_WARNING,
    DEFAULT_BATTERY_LOW,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class Cardio4HAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cardio4HA."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # Create entry with default values for simplicity
            return self.async_create_entry(
                title="Device Health Monitor",
                data={},
                options={
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                    CONF_BATTERY_CRITICAL: DEFAULT_BATTERY_CRITICAL,
                    CONF_BATTERY_WARNING: DEFAULT_BATTERY_WARNING,
                    CONF_BATTERY_LOW: DEFAULT_BATTERY_LOW,
                },
            )

        # Show simple confirmation form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": "Cardio4HA will monitor all your devices automatically!"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> Cardio4HAOptionsFlow:
        """Get the options flow for this handler."""
        return Cardio4HAOptionsFlow(config_entry)


class Cardio4HAOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Cardio4HA."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values
        options = self.config_entry.options
        current_interval = options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        current_critical = options.get(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL)
        current_warning = options.get(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING)
        current_low = options.get(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_BATTERY_CRITICAL,
                        default=current_critical,
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_BATTERY_WARNING,
                        default=current_warning,
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_BATTERY_LOW,
                        default=current_low,
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),
                }
            ),
        )
