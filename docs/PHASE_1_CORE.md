# Phase 1: Core Monitoring Implementation

## 🎯 Goal
Implement the core device health monitoring logic with three main tracking systems:
1. Unavailable devices (sorted by duration)
2. Low battery devices (sorted by level)
3. Weak signal devices (sorted by strength)

## ✅ Success Criteria
- [ ] Coordinator scans all entities successfully
- [ ] Unavailable tracking persists across HA restarts
- [ ] Battery levels correctly identified and sorted
- [ ] Signal strengths properly detected
- [ ] Sensor entities created and updating
- [ ] Performance target: < 5 seconds for 200 devices

---

## 📝 Step 1: Project Setup

### 1.1 Create manifest.json
```json
{
  "domain": "cardio4ha",
  "name": "Cardio4HA - Device Health Monitor",
  "codeowners": ["@your-github-username"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/your-username/cardio4ha",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/your-username/cardio4ha/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

### 1.2 Create const.py
```python
"""Constants for Cardio4HA integration."""
from datetime import timedelta

DOMAIN = "cardio4ha"
NAME = "Cardio4HA"

# Configuration
CONF_UPDATE_INTERVAL = "update_interval"
CONF_BATTERY_CRITICAL = "battery_critical"
CONF_BATTERY_WARNING = "battery_warning"
CONF_BATTERY_LOW = "battery_low"
CONF_LINKQUALITY_WARNING = "linkquality_warning"
CONF_RSSI_WARNING = "rssi_warning"
CONF_UNAVAILABLE_WARNING = "unavailable_warning"
CONF_UNAVAILABLE_CRITICAL = "unavailable_critical"
CONF_EXCLUDE_DOMAINS = "exclude_domains"
CONF_EXCLUDE_ENTITIES = "exclude_entities"
CONF_INCLUDE_DISABLED = "include_disabled"

# Defaults
DEFAULT_UPDATE_INTERVAL = 60
DEFAULT_BATTERY_CRITICAL = 15
DEFAULT_BATTERY_WARNING = 30
DEFAULT_BATTERY_LOW = 50
DEFAULT_LINKQUALITY_WARNING = 100
DEFAULT_RSSI_WARNING = -70
DEFAULT_UNAVAILABLE_WARNING = 3600  # 1 hour
DEFAULT_UNAVAILABLE_CRITICAL = 21600  # 6 hours
DEFAULT_EXCLUDE_DOMAINS = ["sun", "weather", "updater"]
DEFAULT_EXCLUDE_ENTITIES = []
DEFAULT_INCLUDE_DISABLED = False

# Sensor types
SENSOR_UNAVAILABLE_COUNT = "unavailable_count"
SENSOR_LOW_BATTERY_COUNT = "low_battery_count"
SENSOR_WEAK_SIGNAL_COUNT = "weak_signal_count"
SENSOR_CRITICAL_COUNT = "critical_count"
SENSOR_WARNING_COUNT = "warning_count"
SENSOR_HEALTHY_COUNT = "healthy_count"
SENSOR_LAST_SCAN_DURATION = "last_scan_duration"

# Storage
STORAGE_KEY = f"{DOMAIN}.unavailable_tracking"
STORAGE_VERSION = 1

# Severity levels
SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_LOW = "low"
SEVERITY_OK = "ok"

# Signal types
SIGNAL_TYPE_ZIGBEE = "zigbee"
SIGNAL_TYPE_WIFI = "wifi"

# Update interval limits
MIN_UPDATE_INTERVAL = 30
MAX_UPDATE_INTERVAL = 300

# States to track as unavailable
UNAVAILABLE_STATES = ["unavailable", "unknown"]

# Battery detection keywords
BATTERY_KEYWORDS = ["battery", "batt"]
```

---

## 📝 Step 2: Initialize Integration

### 2.1 Create __init__.py
```python
"""The Cardio4HA integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .coordinator import Cardio4HACoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cardio4HA from a config entry."""
    _LOGGER.info("Setting up Cardio4HA integration")
    
    # Get configuration
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL, 
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )
    
    # Create coordinator
    coordinator = Cardio4HACoordinator(
        hass,
        entry,
        update_interval=timedelta(seconds=update_interval)
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Setup options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    _LOGGER.info("Cardio4HA integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Cardio4HA integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Save any pending data
        await coordinator.async_save_unavailable_data()
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
```

---

## 📝 Step 3: Core Coordinator Logic

### 3.1 Create coordinator.py

This is the HEART of Cardio4HA. Focus on this file!

```python
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
            entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)
            device_registry = self.hass.helpers.device_registry.async_get(self.hass)
            
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
                            area_registry = self.hass.helpers.area_registry.async_get(self.hass)
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
```

---

## 📝 Step 4: Sensor Entities

### 4.1 Create sensor.py

```python
"""Sensor platform for Cardio4HA."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_UNAVAILABLE_COUNT,
    SENSOR_LOW_BATTERY_COUNT,
    SENSOR_WEAK_SIGNAL_COUNT,
    SENSOR_CRITICAL_COUNT,
    SENSOR_WARNING_COUNT,
    SENSOR_HEALTHY_COUNT,
    SENSOR_LAST_SCAN_DURATION,
)
from .coordinator import Cardio4HACoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cardio4HA sensors."""
    coordinator: Cardio4HACoordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        Cardio4HASensor(coordinator, SENSOR_UNAVAILABLE_COUNT),
        Cardio4HASensor(coordinator, SENSOR_LOW_BATTERY_COUNT),
        Cardio4HASensor(coordinator, SENSOR_WEAK_SIGNAL_COUNT),
        Cardio4HASensor(coordinator, SENSOR_CRITICAL_COUNT),
        Cardio4HASensor(coordinator, SENSOR_WARNING_COUNT),
        Cardio4HASensor(coordinator, SENSOR_HEALTHY_COUNT),
        Cardio4HASensor(coordinator, SENSOR_LAST_SCAN_DURATION),
    ]
    
    async_add_entities(sensors)


class Cardio4HASensor(CoordinatorEntity, SensorEntity):
    """Cardio4HA Sensor."""

    def __init__(self, coordinator: Cardio4HACoordinator, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"
        self._attr_has_entity_name = True
        
        # Set sensor properties based on type
        if sensor_type == SENSOR_UNAVAILABLE_COUNT:
            self._attr_name = "Unavailable Devices"
            self._attr_icon = "mdi:alert-circle-outline"
        elif sensor_type == SENSOR_LOW_BATTERY_COUNT:
            self._attr_name = "Low Battery Devices"
            self._attr_icon = "mdi:battery-alert"
        elif sensor_type == SENSOR_WEAK_SIGNAL_COUNT:
            self._attr_name = "Weak Signal Devices"
            self._attr_icon = "mdi:signal-off"
        elif sensor_type == SENSOR_CRITICAL_COUNT:
            self._attr_name = "Critical Issues"
            self._attr_icon = "mdi:alert"
        elif sensor_type == SENSOR_WARNING_COUNT:
            self._attr_name = "Warning Issues"
            self._attr_icon = "mdi:alert-outline"
        elif sensor_type == SENSOR_HEALTHY_COUNT:
            self._attr_name = "Healthy Devices"
            self._attr_icon = "mdi:check-circle"
        elif sensor_type == SENSOR_LAST_SCAN_DURATION:
            self._attr_name = "Last Scan Duration"
            self._attr_icon = "mdi:timer-outline"
            self._attr_native_unit_of_measurement = "s"
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        if self._sensor_type == SENSOR_UNAVAILABLE_COUNT:
            return self.coordinator.data["summary"]["unavailable_count"]
        elif self._sensor_type == SENSOR_LOW_BATTERY_COUNT:
            return self.coordinator.data["summary"]["low_battery_count"]
        elif self._sensor_type == SENSOR_WEAK_SIGNAL_COUNT:
            return self.coordinator.data["summary"]["weak_signal_count"]
        elif self._sensor_type == SENSOR_CRITICAL_COUNT:
            return self.coordinator.data["summary"]["critical_count"]
        elif self._sensor_type == SENSOR_WARNING_COUNT:
            return self.coordinator.data["summary"]["warning_count"]
        elif self._sensor_type == SENSOR_HEALTHY_COUNT:
            return self.coordinator.data["summary"]["healthy_count"]
        elif self._sensor_type == SENSOR_LAST_SCAN_DURATION:
            return round(self.coordinator.data.get("scan_duration", 0), 2)
        
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        
        if self._sensor_type == SENSOR_UNAVAILABLE_COUNT:
            devices = self.coordinator.data["unavailable"][:10]  # Top 10
            return {
                "devices": devices,
                "count": len(self.coordinator.data["unavailable"]),
            }
        elif self._sensor_type == SENSOR_LOW_BATTERY_COUNT:
            devices = self.coordinator.data["low_battery"][:10]  # Top 10
            return {
                "devices": devices,
                "count": len(self.coordinator.data["low_battery"]),
            }
        elif self._sensor_type == SENSOR_WEAK_SIGNAL_COUNT:
            devices = self.coordinator.data["weak_signal"][:10]  # Top 10
            return {
                "devices": devices,
                "count": len(self.coordinator.data["weak_signal"]),
            }
        
        return {}
```

---

## ✅ Phase 1 Checklist

- [ ] manifest.json created with correct metadata
- [ ] const.py with all constants defined
- [ ] __init__.py with integration setup
- [ ] coordinator.py with full scanning logic
- [ ] sensor.py with all count sensors
- [ ] Storage system for unavailable tracking
- [ ] Proper sorting (unavailable by duration, battery by level)
- [ ] Performance acceptable (<5s for 200 devices)
- [ ] Logging implemented (INFO, DEBUG, ERROR)
- [ ] Error handling in place

## 🧪 Testing Phase 1

1. Install integration via HACS (or copy to custom_components)
2. Add integration via UI
3. Check sensors are created
4. Verify unavailable device tracking
5. Verify battery monitoring
6. Restart HA and check persistence
7. Check performance (scan duration sensor)

---

**Next**: Phase 2 for Config Flow and UI improvements
