"""DataUpdateCoordinator for Cardio4HA."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import fnmatch
import logging
import math
import statistics
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
    MAINTENANCE_STORAGE_KEY,
    MAINTENANCE_STORAGE_VERSION,
    IGNORE_STORAGE_KEY,
    IGNORE_STORAGE_VERSION,
    STARTUP_DELAY,
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
    CONF_EXCLUDE_ENTITY_WILDCARDS,
    CONF_EXCLUDE_INTEGRATIONS,
    CONF_EXCLUDE_AREAS,
    CONF_MONITOR_ZIGBEE2MQTT,
    CONF_HISTORY_RETENTION_DAYS,
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
    DEFAULT_EXCLUDE_ENTITY_WILDCARDS,
    DEFAULT_EXCLUDE_INTEGRATIONS,
    DEFAULT_EXCLUDE_AREAS,
    DEFAULT_MONITOR_ZIGBEE2MQTT,
    DEFAULT_HISTORY_RETENTION_DAYS,
    UNAVAILABLE_STATES,
    BATTERY_KEYWORDS,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    SEVERITY_LOW,
    SEVERITY_OK,
    SIGNAL_TYPE_ZIGBEE,
    SIGNAL_TYPE_WIFI,
    HEALTH_WEIGHT_UNAVAILABLE,
    HEALTH_WEIGHT_BATTERY,
    HEALTH_WEIGHT_SIGNAL,
    HEALTH_WEIGHT_FLAKY,
    FLAKY_MIN_EVENTS,
    FLAKY_STDDEV_MULTIPLIER,
)
from .device_history import DeviceHistory

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
        self._maintenance_store = Store(hass, MAINTENANCE_STORAGE_VERSION, MAINTENANCE_STORAGE_KEY)
        self.maintenance_devices: dict[str, dict[str, Any]] = {}
        self._ignore_store = Store(hass, IGNORE_STORAGE_VERSION, IGNORE_STORAGE_KEY)
        self.ignored_devices: dict[str, dict[str, Any]] = {}
        self.unavailable_devices: list[dict[str, Any]] = []
        self.low_battery_devices: list[dict[str, Any]] = []
        self.weak_signal_devices: list[dict[str, Any]] = []

        # v1.0.0: Device history for timeline, flaky detection, battery prediction
        self.device_history = DeviceHistory(hass)

        # v1.0.0: Track previous unavailable keys for state transition detection
        self._previous_unavailable_keys: set[str] = set()

        # v1.0.0: Notification engine (set by __init__.py after creation)
        self.notification_engine = None

        # v1.1.0: Startup delay - wait for HA to fully initialize
        self._startup_time = dt_util.utcnow()
        self._startup_delay = STARTUP_DELAY

        # Load saved data
        hass.async_create_task(self._async_load_all_data())

    async def _async_load_all_data(self) -> None:
        """Load all persistent data."""
        await asyncio.gather(
            self._async_load_unavailable_data(),
            self._async_load_maintenance_data(),
            self._async_load_ignore_data(),
            self.device_history.async_load(),
        )

    async def _async_load_unavailable_data(self) -> None:
        """Load unavailable tracking data from storage."""
        try:
            data = await self._store.async_load()
            if data is not None:
                self.unavailable_tracking = data.get("tracking", {})
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

    async def _async_load_maintenance_data(self) -> None:
        """Load maintenance devices data from storage."""
        try:
            data = await self._maintenance_store.async_load()
            if data is not None:
                self.maintenance_devices = data.get("devices", {})
                _LOGGER.info(
                    "Loaded %d maintenance device(s) from storage",
                    len(self.maintenance_devices)
                )
        except Exception as err:
            _LOGGER.error("Error loading maintenance data: %s", err)
            self.maintenance_devices = {}

    async def async_save_unavailable_data(self) -> None:
        """Save unavailable tracking data to storage."""
        try:
            save_data = {}
            for entity_id, info in self.unavailable_tracking.items():
                save_data[entity_id] = {
                    **info,
                    "since": info["since"].isoformat() if isinstance(info["since"], datetime) else info["since"]
                }
            await self._store.async_save({"tracking": save_data})
        except Exception as err:
            _LOGGER.error("Error saving unavailable tracking data: %s", err)

    async def async_save_maintenance_data(self) -> None:
        """Save maintenance devices data to storage."""
        try:
            await self._maintenance_store.async_save({"devices": self.maintenance_devices})
        except Exception as err:
            _LOGGER.error("Error saving maintenance data: %s", err)

    async def _async_load_ignore_data(self) -> None:
        """Load ignored devices data from storage."""
        try:
            data = await self._ignore_store.async_load()
            if data is not None:
                self.ignored_devices = data.get("devices", {})
                _LOGGER.info(
                    "Loaded %d ignored device(s) from storage",
                    len(self.ignored_devices)
                )
        except Exception as err:
            _LOGGER.error("Error loading ignore data: %s", err)
            self.ignored_devices = {}

    async def async_save_ignore_data(self) -> None:
        """Save ignored devices data to storage."""
        try:
            await self._ignore_store.async_save({"devices": self.ignored_devices})
        except Exception as err:
            _LOGGER.error("Error saving ignore data: %s", err)

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
            if value < threshold / 2:
                return SEVERITY_CRITICAL
            elif value < threshold:
                return SEVERITY_WARNING
        elif signal_type == SIGNAL_TYPE_WIFI:
            if value < threshold - 10:
                return SEVERITY_CRITICAL
            elif value < threshold:
                return SEVERITY_WARNING
        return SEVERITY_LOW

    def _is_under_maintenance(self, key: str) -> bool:
        """Check if key (entity_id or device_key) is under maintenance."""
        if key in self.maintenance_devices:
            maintenance_info = self.maintenance_devices[key]
            if maintenance_info.get("expires_at"):
                expires_at = dt_util.parse_datetime(maintenance_info["expires_at"])
                if expires_at and dt_util.utcnow() < expires_at:
                    return True
        return False

    def _should_exclude_entity(
        self,
        entity_id: str,
        domain: str,
        entity_entry: er.RegistryEntry | None = None,
        area_name: str | None = None,
        device_id: str | None = None,
    ) -> bool:
        """Check if entity should be excluded."""
        device_key = self._get_device_key(device_id, entity_id)

        # Check maintenance by entity_id (backward compat) and device_key
        if self._is_under_maintenance(entity_id) or self._is_under_maintenance(device_key):
            return True

        # Check if device is permanently ignored
        if device_key in self.ignored_devices:
            return True

        # Zigbee2MQTT Override
        monitor_z2m = self._get_config_value(CONF_MONITOR_ZIGBEE2MQTT, DEFAULT_MONITOR_ZIGBEE2MQTT)
        if monitor_z2m and entity_entry and entity_entry.platform == "mqtt":
            if any(z2m in entity_id.lower() for z2m in ["zigbee", "z2m", "0x"]):
                return False

        exclude_domains = self._get_config_value(CONF_EXCLUDE_DOMAINS, DEFAULT_EXCLUDE_DOMAINS)
        exclude_entities = self._get_config_value(CONF_EXCLUDE_ENTITIES, DEFAULT_EXCLUDE_ENTITIES)
        exclude_wildcards = self._get_config_value(CONF_EXCLUDE_ENTITY_WILDCARDS, DEFAULT_EXCLUDE_ENTITY_WILDCARDS)
        exclude_integrations = self._get_config_value(CONF_EXCLUDE_INTEGRATIONS, DEFAULT_EXCLUDE_INTEGRATIONS)
        exclude_areas = self._get_config_value(CONF_EXCLUDE_AREAS, DEFAULT_EXCLUDE_AREAS)

        if domain in exclude_domains:
            return True
        if entity_entry and entity_entry.platform and entity_entry.platform in exclude_integrations:
            return True
        if area_name and area_name in exclude_areas:
            return True

        for pattern in exclude_entities:
            if pattern.endswith("*"):
                if entity_id.startswith(pattern[:-1]):
                    return True
            elif entity_id == pattern:
                return True

        for pattern in exclude_wildcards:
            if fnmatch.fnmatch(entity_id, pattern):
                return True

        return False

    @staticmethod
    def _is_battery_entity(entity_id: str, attributes: dict) -> bool:
        """Check if entity is a battery sensor."""
        if attributes.get("device_class") == "battery":
            return True
        lower_id = entity_id.lower()
        return any(keyword in lower_id for keyword in BATTERY_KEYWORDS)

    def _get_device_key(self, device_id: str | None, entity_id: str) -> str:
        """Get a stable key for device history tracking."""
        return device_id or entity_id

    @property
    def startup_remaining(self) -> int:
        """Seconds remaining in startup delay."""
        elapsed = (dt_util.utcnow() - self._startup_time).total_seconds()
        remaining = self._startup_delay - elapsed
        return max(0, int(remaining))

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Home Assistant."""
        # v1.1.0: Startup delay - wait for HA to fully start
        remaining = self.startup_remaining
        if remaining > 0:
            _LOGGER.debug(
                "Startup delay: %d seconds remaining before first scan", remaining
            )
            return {
                "unavailable": [],
                "low_battery": [],
                "weak_signal": [],
                "summary": {
                    "total_entities": 0,
                    "unavailable_count": 0,
                    "low_battery_count": 0,
                    "weak_signal_count": 0,
                    "healthy_count": 0,
                    "critical_count": 0,
                    "warning_count": 0,
                    "flaky_count": 0,
                    "health_score": 100,
                },
                "health_score": 100,
                "flaky_devices": [],
                "flaky_device_keys": set(),
                "flaky_count": 0,
                "battery_predictions": {},
                "last_update": dt_util.utcnow(),
                "scan_duration": 0,
                "startup_remaining": remaining,
            }

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
            retention_days = self._get_config_value(CONF_HISTORY_RETENTION_DAYS, DEFAULT_HISTORY_RETENTION_DAYS)

            # Result containers
            unavailable_devices = []
            low_battery_devices = []
            weak_signal_devices = []

            # Device-level dedup
            low_battery_device_ids = set()
            weak_signal_device_ids = set()

            # Track device entity counts for smart unavailable detection
            device_entity_counts = {}

            # Track all monitored device count for health score
            all_monitored_device_keys = set()

            # Track current unavailable keys for state transition detection
            current_unavailable_keys = set()

            # Registries
            entity_registry = er.async_get(self.hass)
            device_registry = dr.async_get(self.hass)
            area_registry = ar.async_get(self.hass)

            # ====== MAIN SCAN LOOP ======
            for entity_id in self.hass.states.async_entity_ids():
                state = self.hass.states.get(entity_id)
                if not state:
                    continue

                domain = entity_id.split(".")[0]
                entity_entry = entity_registry.async_get(entity_id)

                # Skip Cardio4HA's own sensors
                if entity_entry and entity_entry.platform == DOMAIN:
                    continue

                # Skip disabled entities unless configured
                if entity_entry and entity_entry.disabled and not include_disabled:
                    continue

                # Get device and area info
                device_name = None
                area_name = None
                device_id = entity_entry.device_id if entity_entry else None

                if entity_entry and entity_entry.device_id:
                    device_entry = device_registry.async_get(entity_entry.device_id)
                    if device_entry:
                        device_name = device_entry.name_by_user or device_entry.name
                        if device_entry.area_id:
                            area_entry = area_registry.async_get_area(device_entry.area_id)
                            if area_entry:
                                area_name = area_entry.name

                # Exclusion check
                if self._should_exclude_entity(entity_id, domain, entity_entry, area_name, device_id):
                    continue

                device_key = self._get_device_key(device_id, entity_id)
                all_monitored_device_keys.add(device_key)

                # ── 1. TRACK DEVICE ENTITY COUNTS ──
                if device_id:
                    if device_id not in device_entity_counts:
                        device_entity_counts[device_id] = {
                            "total": 0,
                            "unavailable": 0,
                            "device_name": device_name,
                            "area_name": area_name,
                            "entities": [],
                        }
                    device_entity_counts[device_id]["total"] += 1

                    if state.state in UNAVAILABLE_STATES:
                        device_entity_counts[device_id]["unavailable"] += 1
                        device_entity_counts[device_id]["entities"].append({
                            "entity_id": entity_id,
                            "name": state.name or entity_id,
                            "domain": domain,
                            "state": state.state,
                        })

                # ── 2. STANDALONE ENTITY UNAVAILABILITY ──
                if not device_id and state.state in UNAVAILABLE_STATES:
                    now = dt_util.utcnow()
                    if entity_id not in self.unavailable_tracking:
                        self.unavailable_tracking[entity_id] = {
                            "since": now,
                            "entity_id": entity_id,
                            "name": state.name or entity_id,
                            "domain": domain,
                        }

                    since = self.unavailable_tracking[entity_id]["since"]
                    duration = now - since
                    duration_seconds = duration.total_seconds()

                    if duration_seconds >= unavailable_critical:
                        severity = SEVERITY_CRITICAL
                    elif duration_seconds >= unavailable_warning:
                        severity = SEVERITY_WARNING
                    else:
                        severity = SEVERITY_LOW

                    current_unavailable_keys.add(device_key)

                    unavailable_devices.append({
                        "entity_id": entity_id,
                        "name": state.name or entity_id,
                        "domain": domain,
                        "area": area_name,
                        "device": device_name,
                        "device_id": None,
                        "device_key": device_key,
                        "since": since,
                        "duration_seconds": duration_seconds,
                        "duration_human": self._format_duration(duration),
                        "last_seen": since,
                        "severity": severity,
                        "integration": entity_entry.platform if entity_entry else "unknown",
                    })
                elif not device_id:
                    self.unavailable_tracking.pop(entity_id, None)

                # ── 3. BATTERY LEVEL ──
                if self._is_battery_entity(entity_id, state.attributes):
                    try:
                        battery_level = float(state.state)
                        if 0 <= battery_level <= 100:
                            # Record battery reading for history
                            self.device_history.record_battery_reading(device_key, int(battery_level))

                            if battery_level < battery_low:
                                severity = self._get_battery_severity(
                                    battery_level, battery_critical, battery_warning, battery_low
                                )
                                dev_id = entity_entry.device_id if entity_entry else None
                                if dev_id:
                                    if dev_id not in low_battery_device_ids:
                                        low_battery_device_ids.add(dev_id)
                                        low_battery_devices.append({
                                            "entity_id": entity_id,
                                            "name": device_name or state.name or entity_id,
                                            "battery_level": battery_level,
                                            "severity": severity,
                                            "area": area_name,
                                            "device": device_name,
                                            "device_id": dev_id,
                                            "device_key": device_key,
                                            "last_updated": state.last_updated,
                                        })
                                else:
                                    low_battery_devices.append({
                                        "entity_id": entity_id,
                                        "name": state.name or entity_id,
                                        "battery_level": battery_level,
                                        "severity": severity,
                                        "area": area_name,
                                        "device": device_name,
                                        "device_id": None,
                                        "device_key": device_key,
                                        "last_updated": state.last_updated,
                                    })
                    except (ValueError, TypeError):
                        pass

                # ── 4. SIGNAL STRENGTH ──
                linkquality = state.attributes.get("linkquality")
                if linkquality is not None:
                    try:
                        lqi = float(linkquality)
                        # Record signal reading for history
                        self.device_history.record_signal_reading(device_key, lqi)

                        if lqi < linkquality_warning:
                            severity = self._get_signal_severity(SIGNAL_TYPE_ZIGBEE, lqi, linkquality_warning)
                            dev_id = entity_entry.device_id if entity_entry else None
                            if dev_id:
                                if dev_id not in weak_signal_device_ids:
                                    weak_signal_device_ids.add(dev_id)
                                    weak_signal_devices.append({
                                        "entity_id": entity_id,
                                        "name": device_name or state.name or entity_id,
                                        "signal_type": SIGNAL_TYPE_ZIGBEE,
                                        "linkquality": lqi,
                                        "rssi": None,
                                        "severity": severity,
                                        "area": area_name,
                                        "device": device_name,
                                        "device_id": dev_id,
                                        "device_key": device_key,
                                    })
                            else:
                                weak_signal_devices.append({
                                    "entity_id": entity_id,
                                    "name": state.name or entity_id,
                                    "signal_type": SIGNAL_TYPE_ZIGBEE,
                                    "linkquality": lqi,
                                    "rssi": None,
                                    "severity": severity,
                                    "area": area_name,
                                    "device": device_name,
                                    "device_id": None,
                                    "device_key": device_key,
                                })
                    except (ValueError, TypeError):
                        pass

                rssi = state.attributes.get("rssi") or state.attributes.get("wifi_signal")
                if rssi is not None:
                    try:
                        rssi_value = float(rssi)
                        self.device_history.record_signal_reading(device_key, rssi_value)

                        if rssi_value < rssi_warning:
                            severity = self._get_signal_severity(SIGNAL_TYPE_WIFI, rssi_value, rssi_warning)
                            dev_id = entity_entry.device_id if entity_entry else None
                            if dev_id:
                                if dev_id not in weak_signal_device_ids:
                                    weak_signal_device_ids.add(dev_id)
                                    weak_signal_devices.append({
                                        "entity_id": entity_id,
                                        "name": device_name or state.name or entity_id,
                                        "signal_type": SIGNAL_TYPE_WIFI,
                                        "linkquality": None,
                                        "rssi": rssi_value,
                                        "severity": severity,
                                        "area": area_name,
                                        "device": device_name,
                                        "device_id": dev_id,
                                        "device_key": device_key,
                                    })
                            else:
                                weak_signal_devices.append({
                                    "entity_id": entity_id,
                                    "name": state.name or entity_id,
                                    "signal_type": SIGNAL_TYPE_WIFI,
                                    "linkquality": None,
                                    "rssi": rssi_value,
                                    "severity": severity,
                                    "area": area_name,
                                    "device": device_name,
                                    "device_id": None,
                                    "device_key": device_key,
                                })
                    except (ValueError, TypeError):
                        pass

            # ====== DEVICE-LEVEL UNAVAILABILITY ======
            now = dt_util.utcnow()
            for device_id, device_info in device_entity_counts.items():
                if device_info["unavailable"] == device_info["total"] and device_info["unavailable"] > 0:
                    first_entity = device_info["entities"][0] if device_info["entities"] else None
                    if first_entity:
                        entity_id = first_entity["entity_id"]
                        device_key = device_id

                        if entity_id not in self.unavailable_tracking:
                            self.unavailable_tracking[entity_id] = {
                                "since": now,
                                "entity_id": entity_id,
                                "name": first_entity["name"],
                                "domain": first_entity["domain"],
                            }

                        since = self.unavailable_tracking[entity_id]["since"]
                        duration = now - since
                        duration_seconds = duration.total_seconds()

                        if duration_seconds >= unavailable_critical:
                            severity = SEVERITY_CRITICAL
                        elif duration_seconds >= unavailable_warning:
                            severity = SEVERITY_WARNING
                        else:
                            severity = SEVERITY_LOW

                        current_unavailable_keys.add(device_key)

                        unavailable_devices.append({
                            "entity_id": entity_id,
                            "name": device_info["device_name"] or first_entity["name"],
                            "domain": first_entity["domain"],
                            "area": device_info["area_name"],
                            "device": device_info["device_name"],
                            "device_id": device_id,
                            "device_key": device_key,
                            "since": since,
                            "duration_seconds": duration_seconds,
                            "duration_human": self._format_duration(duration),
                            "last_seen": since,
                            "severity": severity,
                            "integration": "multiple",
                            "unavailable_count": device_info["unavailable"],
                            "total_count": device_info["total"],
                        })
                else:
                    for entity_info in device_info["entities"]:
                        self.unavailable_tracking.pop(entity_info["entity_id"], None)

            # ====== RECORD HISTORY EVENTS ======
            newly_offline = current_unavailable_keys - self._previous_unavailable_keys
            newly_online = self._previous_unavailable_keys - current_unavailable_keys

            for key in newly_offline:
                self.device_history.record_offline_event(key)
            for key in newly_online:
                self.device_history.record_online_event(key)

            self._previous_unavailable_keys = current_unavailable_keys

            # ====== FLAKY DEVICE DETECTION ======
            flaky_devices = []
            flaky_device_keys = set()
            offline_counts = {}

            for device_key in all_monitored_device_keys:
                count = self.device_history.get_offline_event_count(device_key, 30)
                if count > 0:
                    offline_counts[device_key] = count

            if offline_counts:
                counts = list(offline_counts.values())
                mean_count = statistics.mean(counts)
                stddev_count = statistics.pstdev(counts) if len(counts) > 1 else 0.0
                threshold = mean_count + FLAKY_STDDEV_MULTIPLIER * stddev_count

                for device_key, count in offline_counts.items():
                    if count > threshold and count >= FLAKY_MIN_EVENTS:
                        flaky_device_keys.add(device_key)
                        # Find device info from unavailable list or create entry
                        device_info = None
                        for d in unavailable_devices:
                            if d.get("device_key") == device_key:
                                device_info = d
                                break
                        flaky_devices.append({
                            "device_key": device_key,
                            "offline_count_30d": count,
                            "name": device_info["name"] if device_info else device_key,
                            "area": device_info.get("area") if device_info else None,
                        })

            # ====== BATTERY PREDICTIONS ======
            battery_predictions = {}
            for dev in low_battery_devices:
                dk = dev.get("device_key")
                if dk:
                    days = self.device_history.predict_battery_days(dk)
                    if days is not None:
                        battery_predictions[dk] = days
                        dev["days_remaining"] = days

            # ====== HEALTH SCORE ======
            total_monitored = len(all_monitored_device_keys)
            if total_monitored > 0:
                unavailable_ratio = len(current_unavailable_keys) / total_monitored
                low_battery_ratio = len(low_battery_devices) / total_monitored
                weak_signal_ratio = len(weak_signal_devices) / total_monitored
                flaky_ratio = len(flaky_device_keys) / total_monitored
            else:
                unavailable_ratio = low_battery_ratio = weak_signal_ratio = flaky_ratio = 0.0

            health_score = 100.0
            health_score -= unavailable_ratio * 100 * HEALTH_WEIGHT_UNAVAILABLE
            health_score -= low_battery_ratio * 100 * HEALTH_WEIGHT_BATTERY
            health_score -= weak_signal_ratio * 100 * HEALTH_WEIGHT_SIGNAL
            health_score -= flaky_ratio * 100 * HEALTH_WEIGHT_FLAKY
            health_score = max(0, round(health_score))

            # ====== SORT RESULTS ======
            unavailable_devices.sort(key=lambda x: x["duration_seconds"], reverse=True)
            low_battery_devices.sort(key=lambda x: x["battery_level"])
            weak_signal_devices.sort(
                key=lambda x: x["linkquality"] if x["signal_type"] == SIGNAL_TYPE_ZIGBEE else x["rssi"]
            )

            # Store for access
            self.unavailable_devices = unavailable_devices
            self.low_battery_devices = low_battery_devices
            self.weak_signal_devices = weak_signal_devices

            # ====== SUMMARY STATS ======
            total_entities = len(list(self.hass.states.async_entity_ids()))
            unavailable_count = len(unavailable_devices)
            low_battery_count = len(low_battery_devices)
            weak_signal_count = len(weak_signal_devices)
            flaky_count = len(flaky_devices)

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

            end_time = dt_util.utcnow()
            scan_duration = (end_time - start_time).total_seconds()

            # ====== BUILD RESULT ======
            result = {
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
                    "flaky_count": flaky_count,
                    "health_score": health_score,
                },
                "health_score": health_score,
                "flaky_devices": flaky_devices,
                "flaky_device_keys": flaky_device_keys,
                "flaky_count": flaky_count,
                "battery_predictions": battery_predictions,
                "last_update": end_time,
                "scan_duration": scan_duration,
            }

            # ====== PERSIST DATA ======
            await self.async_save_unavailable_data()
            self.device_history.purge_old_data(retention_days)
            await self.device_history.async_save()

            # ====== TRIGGER NOTIFICATIONS ======
            if self.notification_engine:
                try:
                    await self.notification_engine.process_scan_results(result)
                except Exception as err:
                    _LOGGER.error("Error processing notifications: %s", err)

            _LOGGER.info(
                "Scan complete: %d unavailable, %d low battery, %d weak signal, "
                "%d flaky, health=%d (%.2fs)",
                unavailable_count, low_battery_count, weak_signal_count,
                flaky_count, health_score, scan_duration
            )

            return result

        except Exception as err:
            _LOGGER.error("Error updating Cardio4HA data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error updating Cardio4HA data: {err}") from err

    # ==================== Maintenance Mode ====================

    def set_maintenance(self, device_key: str, duration_seconds: int = 3600, name: str = "", area: str = "") -> None:
        """Mark a device as under maintenance."""
        expires_at = dt_util.utcnow() + timedelta(seconds=duration_seconds)
        self.maintenance_devices[device_key] = {
            "expires_at": expires_at.isoformat(),
            "duration": duration_seconds,
            "set_at": dt_util.utcnow().isoformat(),
            "name": name,
            "area": area,
        }
        _LOGGER.info(
            "Device %s marked as maintenance for %d seconds (until %s)",
            device_key, duration_seconds, expires_at.isoformat()
        )
        self.hass.async_create_task(self._async_save_maintenance_and_refresh())

    def clear_maintenance(self, device_key: str) -> None:
        """Clear maintenance status for a device."""
        if device_key in self.maintenance_devices:
            del self.maintenance_devices[device_key]
            _LOGGER.info("Device %s maintenance status cleared", device_key)
            self.hass.async_create_task(self._async_save_maintenance_and_refresh())

    def clear_all_maintenance(self) -> None:
        """Clear all maintenance status."""
        self.maintenance_devices = {}
        _LOGGER.info("All maintenance status cleared")
        self.hass.async_create_task(self._async_save_maintenance_and_refresh())

    async def _async_save_maintenance_and_refresh(self) -> None:
        """Save maintenance data and trigger a rescan."""
        await self.async_save_maintenance_data()
        await self.async_refresh()

    # ==================== Ignore Mode ====================

    def set_ignore(self, device_key: str, name: str = "", area: str = "") -> None:
        """Permanently ignore a device."""
        self.ignored_devices[device_key] = {
            "ignored_since": dt_util.utcnow().isoformat(),
            "name": name,
            "area": area,
        }
        _LOGGER.info("Device %s permanently ignored", device_key)
        self.hass.async_create_task(self._async_save_ignore_and_refresh())

    def clear_ignore(self, device_key: str) -> None:
        """Clear ignore status for a device."""
        if device_key in self.ignored_devices:
            del self.ignored_devices[device_key]
            _LOGGER.info("Device %s ignore status cleared", device_key)
            self.hass.async_create_task(self._async_save_ignore_and_refresh())

    def clear_all_ignored(self) -> None:
        """Clear all ignored devices."""
        self.ignored_devices = {}
        _LOGGER.info("All ignored devices cleared")
        self.hass.async_create_task(self._async_save_ignore_and_refresh())

    async def _async_save_ignore_and_refresh(self) -> None:
        """Save ignore data and trigger a rescan."""
        await self.async_save_ignore_data()
        await self.async_refresh()

    def force_scan(self) -> None:
        """Force an immediate scan."""
        _LOGGER.info("Force scan initiated")
        self.hass.async_create_task(self.async_refresh())
