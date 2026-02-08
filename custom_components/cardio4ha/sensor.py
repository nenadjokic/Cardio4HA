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

        # Device info - connects sensors to integration
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Cardio4HA",
            "manufacturer": "Cardio4HA",
            "model": "Device Health Monitor",
            "sw_version": "0.1.5",
        }

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
