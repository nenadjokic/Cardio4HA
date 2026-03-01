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
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_INSTANT_ENABLED,
    CONF_NOTIFY_OFFLINE_MINUTES,
    CONF_NOTIFY_BATTERY_CRITICAL_LEVEL,
    CONF_NOTIFY_MASS_OFFLINE_THRESHOLD,
    CONF_NOTIFY_DAILY_DIGEST,
    CONF_NOTIFY_DAILY_DIGEST_TIME,
    CONF_NOTIFY_RECOVERY_ENABLED,
    CONF_NOTIFY_RATE_LIMIT,
    CONF_NOTIFY_DEVICE_COOLDOWN,
    CONF_HISTORY_RETENTION_DAYS,
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
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_NOTIFY_INSTANT_ENABLED,
    DEFAULT_NOTIFY_OFFLINE_MINUTES,
    DEFAULT_NOTIFY_BATTERY_CRITICAL_LEVEL,
    DEFAULT_NOTIFY_MASS_OFFLINE_THRESHOLD,
    DEFAULT_NOTIFY_DAILY_DIGEST,
    DEFAULT_NOTIFY_DAILY_DIGEST_TIME,
    DEFAULT_NOTIFY_RECOVERY_ENABLED,
    DEFAULT_NOTIFY_RATE_LIMIT,
    DEFAULT_NOTIFY_DEVICE_COOLDOWN,
    DEFAULT_HISTORY_RETENTION_DAYS,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class Cardio4HAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cardio4HA."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
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
                    CONF_NOTIFY_SERVICE: DEFAULT_NOTIFY_SERVICE,
                    CONF_NOTIFY_INSTANT_ENABLED: DEFAULT_NOTIFY_INSTANT_ENABLED,
                    CONF_NOTIFY_OFFLINE_MINUTES: DEFAULT_NOTIFY_OFFLINE_MINUTES,
                    CONF_NOTIFY_BATTERY_CRITICAL_LEVEL: DEFAULT_NOTIFY_BATTERY_CRITICAL_LEVEL,
                    CONF_NOTIFY_MASS_OFFLINE_THRESHOLD: DEFAULT_NOTIFY_MASS_OFFLINE_THRESHOLD,
                    CONF_NOTIFY_DAILY_DIGEST: DEFAULT_NOTIFY_DAILY_DIGEST,
                    CONF_NOTIFY_DAILY_DIGEST_TIME: DEFAULT_NOTIFY_DAILY_DIGEST_TIME,
                    CONF_NOTIFY_RECOVERY_ENABLED: DEFAULT_NOTIFY_RECOVERY_ENABLED,
                    CONF_NOTIFY_RATE_LIMIT: DEFAULT_NOTIFY_RATE_LIMIT,
                    CONF_NOTIFY_DEVICE_COOLDOWN: DEFAULT_NOTIFY_DEVICE_COOLDOWN,
                    CONF_HISTORY_RETENTION_DAYS: DEFAULT_HISTORY_RETENTION_DAYS,
                },
            )

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

    @staticmethod
    async def async_migrate_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
        """Migrate config entry from older version."""
        _LOGGER.info("Migrating Cardio4HA config from version %s to 2", config_entry.version)

        if config_entry.version < 2:
            new_options = {**config_entry.options}
            # Set defaults for all new v1.0.0 notification/history options
            new_options.setdefault(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)
            new_options.setdefault(CONF_NOTIFY_INSTANT_ENABLED, DEFAULT_NOTIFY_INSTANT_ENABLED)
            new_options.setdefault(CONF_NOTIFY_OFFLINE_MINUTES, DEFAULT_NOTIFY_OFFLINE_MINUTES)
            new_options.setdefault(CONF_NOTIFY_BATTERY_CRITICAL_LEVEL, DEFAULT_NOTIFY_BATTERY_CRITICAL_LEVEL)
            new_options.setdefault(CONF_NOTIFY_MASS_OFFLINE_THRESHOLD, DEFAULT_NOTIFY_MASS_OFFLINE_THRESHOLD)
            new_options.setdefault(CONF_NOTIFY_DAILY_DIGEST, DEFAULT_NOTIFY_DAILY_DIGEST)
            new_options.setdefault(CONF_NOTIFY_DAILY_DIGEST_TIME, DEFAULT_NOTIFY_DAILY_DIGEST_TIME)
            new_options.setdefault(CONF_NOTIFY_RECOVERY_ENABLED, DEFAULT_NOTIFY_RECOVERY_ENABLED)
            new_options.setdefault(CONF_NOTIFY_RATE_LIMIT, DEFAULT_NOTIFY_RATE_LIMIT)
            new_options.setdefault(CONF_NOTIFY_DEVICE_COOLDOWN, DEFAULT_NOTIFY_DEVICE_COOLDOWN)
            new_options.setdefault(CONF_HISTORY_RETENTION_DAYS, DEFAULT_HISTORY_RETENTION_DAYS)

            config_entry.version = 2
            hass.config_entries.async_update_entry(
                config_entry,
                options=new_options,
            )

        _LOGGER.info("Migration to version 2 complete")
        return True


class Cardio4HAOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Cardio4HA."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Thresholds & Exclusions."""
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

            # Store step 1 data and proceed to notifications step
            self._step1_data = user_input
            return await self.async_step_notifications()

        options = self.config_entry.options

        current_interval = options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        current_critical = options.get(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL)
        current_warning = options.get(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING)
        current_low = options.get(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW)
        current_linkquality = options.get(CONF_LINKQUALITY_WARNING, DEFAULT_LINKQUALITY_WARNING)
        current_rssi = options.get(CONF_RSSI_WARNING, DEFAULT_RSSI_WARNING)
        current_unavail_warn = options.get(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING)
        current_unavail_crit = options.get(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL)
        current_wildcards = options.get(CONF_EXCLUDE_ENTITY_WILDCARDS, DEFAULT_EXCLUDE_ENTITY_WILDCARDS)
        current_integrations = options.get(CONF_EXCLUDE_INTEGRATIONS, DEFAULT_EXCLUDE_INTEGRATIONS)
        current_areas = options.get(CONF_EXCLUDE_AREAS, DEFAULT_EXCLUDE_AREAS)
        current_monitor_z2m = options.get(CONF_MONITOR_ZIGBEE2MQTT, DEFAULT_MONITOR_ZIGBEE2MQTT)

        wildcards_str = ", ".join(current_wildcards) if current_wildcards else ""

        entity_reg = er.async_get(self.hass)
        area_reg = ar.async_get(self.hass)

        integrations = sorted(set(
            entry.platform for entry in entity_reg.entities.values() if entry.platform
        ))
        areas = sorted([area.name for area in area_reg.async_list_areas()])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                        description={"suggested_value": current_interval},
                    ): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
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

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Notification settings."""
        if user_input is not None:
            # Merge step 1 + step 2 data
            merged = {**self._step1_data, **user_input}
            return self.async_create_entry(title="", data=merged)

        options = self.config_entry.options

        current_service = options.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)
        current_instant = options.get(CONF_NOTIFY_INSTANT_ENABLED, DEFAULT_NOTIFY_INSTANT_ENABLED)
        current_offline_min = options.get(CONF_NOTIFY_OFFLINE_MINUTES, DEFAULT_NOTIFY_OFFLINE_MINUTES)
        current_batt_crit = options.get(CONF_NOTIFY_BATTERY_CRITICAL_LEVEL, DEFAULT_NOTIFY_BATTERY_CRITICAL_LEVEL)
        current_mass = options.get(CONF_NOTIFY_MASS_OFFLINE_THRESHOLD, DEFAULT_NOTIFY_MASS_OFFLINE_THRESHOLD)
        current_digest = options.get(CONF_NOTIFY_DAILY_DIGEST, DEFAULT_NOTIFY_DAILY_DIGEST)
        current_digest_time = options.get(CONF_NOTIFY_DAILY_DIGEST_TIME, DEFAULT_NOTIFY_DAILY_DIGEST_TIME)
        current_recovery = options.get(CONF_NOTIFY_RECOVERY_ENABLED, DEFAULT_NOTIFY_RECOVERY_ENABLED)
        current_rate = options.get(CONF_NOTIFY_RATE_LIMIT, DEFAULT_NOTIFY_RATE_LIMIT)
        current_cooldown = options.get(CONF_NOTIFY_DEVICE_COOLDOWN, DEFAULT_NOTIFY_DEVICE_COOLDOWN)
        current_retention = options.get(CONF_HISTORY_RETENTION_DAYS, DEFAULT_HISTORY_RETENTION_DAYS)

        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NOTIFY_SERVICE,
                        default=current_service,
                        description={"suggested_value": current_service},
                    ): str,
                    vol.Optional(
                        CONF_NOTIFY_INSTANT_ENABLED,
                        default=current_instant,
                        description={"suggested_value": current_instant},
                    ): bool,
                    vol.Optional(
                        CONF_NOTIFY_OFFLINE_MINUTES,
                        default=current_offline_min,
                        description={"suggested_value": current_offline_min},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=1440)),
                    vol.Optional(
                        CONF_NOTIFY_BATTERY_CRITICAL_LEVEL,
                        default=current_batt_crit,
                        description={"suggested_value": current_batt_crit},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=50)),
                    vol.Optional(
                        CONF_NOTIFY_MASS_OFFLINE_THRESHOLD,
                        default=current_mass,
                        description={"suggested_value": current_mass},
                    ): vol.All(cv.positive_int, vol.Range(min=2, max=50)),
                    vol.Optional(
                        CONF_NOTIFY_DAILY_DIGEST,
                        default=current_digest,
                        description={"suggested_value": current_digest},
                    ): bool,
                    vol.Optional(
                        CONF_NOTIFY_DAILY_DIGEST_TIME,
                        default=current_digest_time,
                        description={"suggested_value": current_digest_time},
                    ): str,
                    vol.Optional(
                        CONF_NOTIFY_RECOVERY_ENABLED,
                        default=current_recovery,
                        description={"suggested_value": current_recovery},
                    ): bool,
                    vol.Optional(
                        CONF_NOTIFY_RATE_LIMIT,
                        default=current_rate,
                        description={"suggested_value": current_rate},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=100)),
                    vol.Optional(
                        CONF_NOTIFY_DEVICE_COOLDOWN,
                        default=current_cooldown,
                        description={"suggested_value": current_cooldown},
                    ): vol.All(cv.positive_int, vol.Range(min=5, max=1440)),
                    vol.Optional(
                        CONF_HISTORY_RETENTION_DAYS,
                        default=current_retention,
                        description={"suggested_value": current_retention},
                    ): vol.All(cv.positive_int, vol.Range(min=1, max=90)),
                }
            ),
        )
