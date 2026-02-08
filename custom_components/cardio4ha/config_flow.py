"""Config flow for Cardio4HA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er, area_registry as ar
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    CONF_BATTERY_CRITICAL,
    CONF_BATTERY_WARNING,
    CONF_BATTERY_LOW,
    CONF_LINKQUALITY_WARNING,
    CONF_RSSI_WARNING,
    CONF_UNAVAILABLE_WARNING,
    CONF_UNAVAILABLE_CRITICAL,
    CONF_EXCLUDE_ENTITY_WILDCARDS,
    CONF_EXCLUDE_INTEGRATIONS,
    CONF_EXCLUDE_AREAS,
    CONF_MONITOR_ZIGBEE2MQTT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_BATTERY_CRITICAL,
    DEFAULT_BATTERY_WARNING,
    DEFAULT_BATTERY_LOW,
    DEFAULT_LINKQUALITY_WARNING,
    DEFAULT_RSSI_WARNING,
    DEFAULT_UNAVAILABLE_WARNING,
    DEFAULT_UNAVAILABLE_CRITICAL,
    DEFAULT_EXCLUDE_ENTITY_WILDCARDS,
    DEFAULT_EXCLUDE_INTEGRATIONS,
    DEFAULT_EXCLUDE_AREAS,
    DEFAULT_MONITOR_ZIGBEE2MQTT,
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
                    CONF_LINKQUALITY_WARNING: DEFAULT_LINKQUALITY_WARNING,
                    CONF_RSSI_WARNING: DEFAULT_RSSI_WARNING,
                    CONF_UNAVAILABLE_WARNING: DEFAULT_UNAVAILABLE_WARNING,
                    CONF_UNAVAILABLE_CRITICAL: DEFAULT_UNAVAILABLE_CRITICAL,
                    CONF_EXCLUDE_ENTITY_WILDCARDS: DEFAULT_EXCLUDE_ENTITY_WILDCARDS,
                    CONF_EXCLUDE_INTEGRATIONS: DEFAULT_EXCLUDE_INTEGRATIONS,
                    CONF_EXCLUDE_AREAS: DEFAULT_EXCLUDE_AREAS,
                    CONF_MONITOR_ZIGBEE2MQTT: DEFAULT_MONITOR_ZIGBEE2MQTT,
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
            # Convert comma-separated wildcards string to list
            if CONF_EXCLUDE_ENTITY_WILDCARDS in user_input:
                wildcards_str = user_input[CONF_EXCLUDE_ENTITY_WILDCARDS]
                if wildcards_str:
                    user_input[CONF_EXCLUDE_ENTITY_WILDCARDS] = [
                        w.strip() for w in wildcards_str.split(",") if w.strip()
                    ]
                else:
                    user_input[CONF_EXCLUDE_ENTITY_WILDCARDS] = []

            return self.async_create_entry(title="", data=user_input)

        # Get current values
        options = self.config_entry.options

        # Basic settings
        current_interval = options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        # Battery thresholds
        current_critical = options.get(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL)
        current_warning = options.get(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING)
        current_low = options.get(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW)

        # Signal thresholds
        current_linkquality = options.get(CONF_LINKQUALITY_WARNING, DEFAULT_LINKQUALITY_WARNING)
        current_rssi = options.get(CONF_RSSI_WARNING, DEFAULT_RSSI_WARNING)

        # Unavailable thresholds
        current_unavail_warn = options.get(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING)
        current_unavail_crit = options.get(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL)

        # Exclusions
        current_wildcards = options.get(CONF_EXCLUDE_ENTITY_WILDCARDS, DEFAULT_EXCLUDE_ENTITY_WILDCARDS)
        current_integrations = options.get(CONF_EXCLUDE_INTEGRATIONS, DEFAULT_EXCLUDE_INTEGRATIONS)
        current_areas = options.get(CONF_EXCLUDE_AREAS, DEFAULT_EXCLUDE_AREAS)
        current_monitor_z2m = options.get(CONF_MONITOR_ZIGBEE2MQTT, DEFAULT_MONITOR_ZIGBEE2MQTT)

        # Convert wildcards list to comma-separated string for UI
        wildcards_str = ", ".join(current_wildcards) if current_wildcards else ""

        # Get available integrations and areas
        entity_reg = er.async_get(self.hass)
        area_reg = ar.async_get(self.hass)

        # Get unique integration platforms
        integrations = sorted(set(
            entry.platform for entry in entity_reg.entities.values() if entry.platform
        ))

        # Get area names
        areas = sorted([area.name for area in area_reg.async_list_areas()])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    # Basic Settings
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                        description={"suggested_value": current_interval},
                    ): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),

                    # Battery Thresholds
                    vol.Optional(
                        CONF_BATTERY_CRITICAL,
                        default=current_critical,
                        description={"suggested_value": current_critical},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_BATTERY_WARNING,
                        default=current_warning,
                        description={"suggested_value": current_warning},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_BATTERY_LOW,
                        default=current_low,
                        description={"suggested_value": current_low},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),

                    # Signal Thresholds
                    vol.Optional(
                        CONF_LINKQUALITY_WARNING,
                        default=current_linkquality,
                        description={"suggested_value": current_linkquality},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=255)),
                    vol.Optional(
                        CONF_RSSI_WARNING,
                        default=current_rssi,
                        description={"suggested_value": current_rssi},
                    ): vol.All(vol.Coerce(int), vol.Range(min=-100, max=0)),

                    # Unavailable Thresholds (in seconds)
                    vol.Optional(
                        CONF_UNAVAILABLE_WARNING,
                        default=current_unavail_warn,
                        description={"suggested_value": current_unavail_warn},
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_UNAVAILABLE_CRITICAL,
                        default=current_unavail_crit,
                        description={"suggested_value": current_unavail_crit},
                    ): cv.positive_int,

                    # Exclusions
                    vol.Optional(
                        CONF_EXCLUDE_ENTITY_WILDCARDS,
                        default=wildcards_str,
                        description={"suggested_value": wildcards_str},
                    ): str,
                    vol.Optional(
                        CONF_EXCLUDE_INTEGRATIONS,
                        default=current_integrations,
                        description={"suggested_value": current_integrations},
                    ): cv.multi_select(dict.fromkeys(integrations)),
                    vol.Optional(
                        CONF_EXCLUDE_AREAS,
                        default=current_areas,
                        description={"suggested_value": current_areas},
                    ): cv.multi_select(dict.fromkeys(areas)),
                    vol.Optional(
                        CONF_MONITOR_ZIGBEE2MQTT,
                        default=current_monitor_z2m,
                        description={"suggested_value": current_monitor_z2m},
                    ): bool,
                }
            ),
        )
