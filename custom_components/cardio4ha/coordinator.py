"""DataUpdateCoordinator for Cardio4HA."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_BATTERY_CRITICAL,
    CONF_BATTERY_WARNING,
    CONF_BATTERY_LOW,
    CONF_LINKQUALITY_WARNING,
    CONF_RSSI_WARNING,
    CONF_UNAVAILABLE_WARNING,
    CONF_UNAVAILABLE_CRITICAL,
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_DISABLED,
    DEFAULT_BATTERY_CRITICAL,
    DEFAULT_BATTERY_WARNING,
    DEFAULT_BATTERY_LOW,
    DEFAULT_LINKQUALITY_WARNING,
    DEFAULT_RSSI_WARNING,
    DEFAULT_UNAVAILABLE_WARNING,
    DEFAULT_UNAVAILABLE_CRITICAL,
    DEFAULT_EXCLUDE_DOMAINS,
    DEFAULT_EXCLUDE_ENTITIES,
    DEFAULT_INCLUDE_DISABLED,
    UNAVAILABLE_STATES,
    BATTERY_KEYWORDS,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    SEVERITY_LOW,
    SEVERITY_OK,
    SIGNAL_TYPE_ZIGBEE,
    SIGNAL_TYPE_WIFI,
)

_LOGGER = logging.getLogger(__name__)


class Cardio4HACoordinator(DataUpdateCoordinator):
    """Class to manage fetching Cardio4HA data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.entry = entry
        self.unavailable_tracking: dict[str, dict[str, Any]] = {}
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

        # Load saved data
        hass.async_create_task(self._async_load_unavailable_data())

    async def _async_load_unavailable_data(self) -> None:
        """Load unavailable tracking data from storage."""
        try:
            data = await self._store.async_load()
            if data is not None:
                self.unavailable_tracking = data.get("tracking", {})
                # Convert ISO strings back to datetime
                for entity_id, info in self.unavailable_tracking.items():
                    if isinstance(info.get("since"), str):
                        info["since"] = dt_util.parse_datetime(info["since"])
                _LOGGER.info(
                    "Loaded %d unavailable device(s) from storage",
                    len(self.unavailable_tracking)
                )
        except Exception as err:
            _LOGGER.error("Error loading unavailable tracking data: %s", err)
            self.unavailable_tracking = {}

    async def async_save_unavailable_data(self) -> None:
        """Save unavailable tracking data to storage."""
        try:
            # Convert datetime to ISO string for JSON serialization
            save_data = {}
            for entity_id, info in self.unavailable_tracking.items():
                save_data[entity_id] = {
                    **info,
                    "since": info["since"].isoformat() if isinstance(info["since"], datetime) else info["since"]
                }

            await self._store.async_save({"tracking": save_data})
            _LOGGER.debug("Saved unavailable tracking data")
        except Exception as err:
            _LOGGER.error("Error saving unavailable tracking data: %s", err)

    def _get_config_value(self, key: str, default: Any) -> Any:
        """Get configuration value from options or data."""
        return self.entry.options.get(
            key, self.entry.data.get(key, default)
        )

    @staticmethod
    def _format_duration(duration: timedelta) -> str:
        """Format duration to human-readable string."""
        total_seconds = int(duration.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @staticmethod
    def _get_battery_severity(level: float, critical: int, warning: int, low: int) -> str:
        """Determine battery severity level."""
        if level < critical:
            return SEVERITY_CRITICAL
        elif level < warning:
            return SEVERITY_WARNING
        elif level < low:
            return SEVERITY_LOW
        return SEVERITY_OK

    @staticmethod
    def _get_signal_severity(signal_type: str, value: float, threshold: float) -> str:
        """Determine signal severity level."""
        if signal_type == SIGNAL_TYPE_ZIGBEE:
            # Zigbee: lower is worse
            if value < threshold / 2:
                return SEVERITY_CRITICAL
            elif value < threshold:
                return SEVERITY_WARNING
        elif signal_type == SIGNAL_TYPE_WIFI:
            # WiFi RSSI: more negative is worse
            if value < threshold - 10:
                return SEVERITY_CRITICAL
            elif value < threshold:
                return SEVERITY_WARNING
        return SEVERITY_LOW

    def _should_exclude_entity(self, entity_id: str, domain: str) -> bool:
        """Check if entity should be excluded."""
        exclude_domains = self._get_config_value(CONF_EXCLUDE_DOMAINS, DEFAULT_EXCLUDE_DOMAINS)
        exclude_entities = self._get_config_value(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES)

        # Check domain exclusion
        if domain in exclude_domains:
            return True

        # Check entity pattern exclusion
        for pattern in exclude_entities:
            if pattern.endswith("*"):
                if entity_id.startswith(pattern[:-1]):
                    return True
            elif entity_id == pattern:
                return True

        return False

    @staticmethod
    def _is_battery_entity(entity_id: str, attributes: dict) -> bool:
        """Check if entity is a battery sensor."""
        # Check device_class
        if attributes.get("device_class") == "battery":
            return True

        # Check entity_id keywords
        lower_id = entity_id.lower()
        return any(keyword in lower_id for keyword in BATTERY_KEYWORDS)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Home Assistant."""
        start_time = dt_util.utcnow()

        try:
            # Get configuration
            battery_critical = self._get_config_value(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL)
            battery_warning = self._get_config_value(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING)
            battery_low = self._get_config_value(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW)
            linkquality_warning = self._get_config_value(CONF_LINKQUALITY_WARNING, DEFAULT_LINKQUALITY_WARNING)
            rssi_warning = self._get_config_value(CONF_RSSI_WARNING, DEFAULT_RSSI_WARNING)
            unavailable_warning = self._get_config_value(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING)
            unavailable_critical = self._get_config_value(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL)
            include_disabled = self._get_config_value(CONF_INCLUDE_DISABLED, DEFAULT_INCLUDE_DISABLED)

            # Initialize result containers
            unavailable_devices = []
            low_battery_devices = []
            weak_signal_devices = []

            # Scan all entities
            entity_registry = er.async_get(self.hass)
            device_registry = dr.async_get(self.hass)
            area_registry = ar.async_get(self.hass)

            for entity_id in self.hass.states.async_entity_ids():
                state = self.hass.states.get(entity_id)
                if not state:
                    continue

                domain = entity_id.split(".")[0]

                # Skip excluded entities
                if self._should_exclude_entity(entity_id, domain):
                    continue

                # Get entity registry entry
                entity_entry = entity_registry.async_get(entity_id)

                # Skip disabled entities unless configured to include them
                if entity_entry and entity_entry.disabled and not include_disabled:
                    continue

                # Get device and area information
                device_name = None
                area_name = None

                if entity_entry and entity_entry.device_id:
                    device_entry = device_registry.async_get(entity_entry.device_id)
                    if device_entry:
                        device_name = device_entry.name_by_user or device_entry.name
                        if device_entry.area_id:
                            area_entry = area_registry.async_get_area(device_entry.area_id)
                            if area_entry:
                                area_name = area_entry.name

                # 1. CHECK UNAVAILABLE STATUS
                if state.state in UNAVAILABLE_STATES:
                    now = dt_util.utcnow()

                    # Track when it became unavailable
                    if entity_id not in self.unavailable_tracking:
                        self.unavailable_tracking[entity_id] = {
                            "since": now,
                            "entity_id": entity_id,
                            "name": state.name or entity_id,
                            "domain": domain,
                        }

                    # Calculate duration
                    since = self.unavailable_tracking[entity_id]["since"]
                    duration = now - since
                    duration_seconds = duration.total_seconds()

                    # Determine severity
                    if duration_seconds >= unavailable_critical:
                        severity = SEVERITY_CRITICAL
                    elif duration_seconds >= unavailable_warning:
                        severity = SEVERITY_WARNING
                    else:
                        severity = SEVERITY_LOW

                    unavailable_devices.append({
                        "entity_id": entity_id,
                        "name": state.name or entity_id,
                        "domain": domain,
                        "area": area_name,
                        "device": device_name,
                        "since": since,
                        "duration_seconds": duration_seconds,
                        "duration_human": self._format_duration(duration),
                        "last_seen": since,
                        "severity": severity,
                        "integration": entity_entry.platform if entity_entry else "unknown",
                    })
                else:
                    # Remove from tracking if it's back online
                    self.unavailable_tracking.pop(entity_id, None)

                # 2. CHECK BATTERY LEVEL
                if self._is_battery_entity(entity_id, state.attributes):
                    try:
                        battery_level = float(state.state)
                        if 0 <= battery_level <= 100 and battery_level < battery_low:
                            severity = self._get_battery_severity(
                                battery_level, battery_critical, battery_warning, battery_low
                            )
                            low_battery_devices.append({
                                "entity_id": entity_id,
                                "name": state.name or entity_id,
                                "battery_level": battery_level,
                                "severity": severity,
                                "area": area_name,
                                "device": device_name,
                                "last_updated": state.last_updated,
                            })
                    except (ValueError, TypeError):
                        pass

                # 3. CHECK SIGNAL STRENGTH
                # Zigbee linkquality
                linkquality = state.attributes.get("linkquality")
                if linkquality is not None:
                    try:
                        lqi = float(linkquality)
                        if lqi < linkquality_warning:
                            severity = self._get_signal_severity(SIGNAL_TYPE_ZIGBEE, lqi, linkquality_warning)
                            weak_signal_devices.append({
                                "entity_id": entity_id,
                                "name": state.name or entity_id,
                                "signal_type": SIGNAL_TYPE_ZIGBEE,
                                "linkquality": lqi,
                                "rssi": None,
                                "severity": severity,
                                "area": area_name,
                                "device": device_name,
                            })
                    except (ValueError, TypeError):
                        pass

                # WiFi RSSI
                rssi = state.attributes.get("rssi") or state.attributes.get("wifi_signal")
                if rssi is not None:
                    try:
                        rssi_value = float(rssi)
                        if rssi_value < rssi_warning:
                            severity = self._get_signal_severity(SIGNAL_TYPE_WIFI, rssi_value, rssi_warning)
                            weak_signal_devices.append({
                                "entity_id": entity_id,
                                "name": state.name or entity_id,
                                "signal_type": SIGNAL_TYPE_WIFI,
                                "linkquality": None,
                                "rssi": rssi_value,
                                "severity": severity,
                                "area": area_name,
                                "device": device_name,
                            })
                    except (ValueError, TypeError):
                        pass

            # Sort results
            unavailable_devices.sort(key=lambda x: x["duration_seconds"], reverse=True)
            low_battery_devices.sort(key=lambda x: x["battery_level"])
            weak_signal_devices.sort(
                key=lambda x: x["linkquality"] if x["signal_type"] == SIGNAL_TYPE_ZIGBEE else x["rssi"]
            )

            # Calculate summary statistics
            total_entities = len(list(self.hass.states.async_entity_ids()))
            unavailable_count = len(unavailable_devices)
            low_battery_count = len(low_battery_devices)
            weak_signal_count = len(weak_signal_devices)

            critical_count = sum(
                1 for d in unavailable_devices if d["severity"] == SEVERITY_CRITICAL
            ) + sum(
                1 for d in low_battery_devices if d["severity"] == SEVERITY_CRITICAL
            ) + sum(
                1 for d in weak_signal_devices if d["severity"] == SEVERITY_CRITICAL
            )

            warning_count = sum(
                1 for d in unavailable_devices if d["severity"] == SEVERITY_WARNING
            ) + sum(
                1 for d in low_battery_devices if d["severity"] == SEVERITY_WARNING
            ) + sum(
                1 for d in weak_signal_devices if d["severity"] == SEVERITY_WARNING
            )

            healthy_count = total_entities - unavailable_count

            # Calculate scan duration
            end_time = dt_util.utcnow()
            scan_duration = (end_time - start_time).total_seconds()

            # Save unavailable tracking data
            await self.async_save_unavailable_data()

            _LOGGER.info(
                "Scan complete: %d unavailable, %d low battery, %d weak signal (scan took %.2fs)",
                unavailable_count, low_battery_count, weak_signal_count, scan_duration
            )

            return {
                "unavailable": unavailable_devices,
                "low_battery": low_battery_devices,
                "weak_signal": weak_signal_devices,
                "summary": {
                    "total_entities": total_entities,
                    "unavailable_count": unavailable_count,
                    "low_battery_count": low_battery_count,
                    "weak_signal_count": weak_signal_count,
                    "healthy_count": healthy_count,
                    "critical_count": critical_count,
                    "warning_count": warning_count,
                },
                "last_update": end_time,
                "scan_duration": scan_duration,
            }

        except Exception as err:
            _LOGGER.error("Error updating Cardio4HA data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error updating Cardio4HA data: {err}") from err
