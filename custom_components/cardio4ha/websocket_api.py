"""WebSocket API for Cardio4HA panel."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    CURRENT_VERSION,
    CONF_BATTERY_CRITICAL,
    CONF_BATTERY_WARNING,
    CONF_BATTERY_LOW,
    CONF_LINKQUALITY_WARNING,
    CONF_RSSI_WARNING,
    CONF_UNAVAILABLE_WARNING,
    CONF_UNAVAILABLE_CRITICAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BATTERY_CRITICAL,
    DEFAULT_BATTERY_WARNING,
    DEFAULT_BATTERY_LOW,
    DEFAULT_LINKQUALITY_WARNING,
    DEFAULT_RSSI_WARNING,
    DEFAULT_UNAVAILABLE_WARNING,
    DEFAULT_UNAVAILABLE_CRITICAL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register WebSocket API commands."""
    websocket_api.async_register_command(hass, websocket_subscribe)
    websocket_api.async_register_command(hass, websocket_force_scan)
    websocket_api.async_register_command(hass, websocket_set_maintenance)
    websocket_api.async_register_command(hass, websocket_clear_maintenance)
    websocket_api.async_register_command(hass, websocket_clear_history)
    websocket_api.async_register_command(hass, websocket_get_device_timeline)
    websocket_api.async_register_command(hass, websocket_set_ignore)
    websocket_api.async_register_command(hass, websocket_clear_ignore)
    websocket_api.async_register_command(hass, websocket_update_config)


def _get_coordinator(hass: HomeAssistant):
    """Get the first available coordinator."""
    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        return None
    from .coordinator import Cardio4HACoordinator
    for coordinator in domain_data.values():
        if isinstance(coordinator, Cardio4HACoordinator):
            return coordinator
    return None


def _serialize_value(v: Any) -> Any:
    """Recursively serialize values for JSON transport."""
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, timedelta):
        return v.total_seconds()
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_serialize_value(item) for item in v]
    if isinstance(v, set):
        return list(v)
    return v


def _build_payload(hass: HomeAssistant, coordinator) -> dict:
    """Build the full data payload for the panel."""
    data = coordinator.data or {}

    entry = coordinator.entry
    def _cfg(key, default):
        return entry.options.get(key, entry.data.get(key, default))

    config = {
        "battery_critical": _cfg(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL),
        "battery_warning": _cfg(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING),
        "battery_low": _cfg(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW),
        "linkquality_warning": _cfg(CONF_LINKQUALITY_WARNING, DEFAULT_LINKQUALITY_WARNING),
        "rssi_warning": _cfg(CONF_RSSI_WARNING, DEFAULT_RSSI_WARNING),
        "unavailable_warning": _cfg(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING),
        "unavailable_critical": _cfg(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL),
        "update_interval": _cfg(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    }

    payload = {
        "unavailable": data.get("unavailable", []),
        "low_battery": data.get("low_battery", []),
        "weak_signal": data.get("weak_signal", []),
        "summary": data.get("summary", {
            "total_entities": 0,
            "unavailable_count": 0,
            "low_battery_count": 0,
            "weak_signal_count": 0,
            "healthy_count": 0,
            "critical_count": 0,
            "warning_count": 0,
            "flaky_count": 0,
            "health_score": 100,
        }),
        "health_score": data.get("health_score", 100),
        "flaky_devices": data.get("flaky_devices", []),
        "flaky_device_keys": data.get("flaky_device_keys", set()),
        "battery_predictions": data.get("battery_predictions", {}),
        "maintenance": coordinator.maintenance_devices,
        "ignored_devices": coordinator.ignored_devices,
        "config": config,
        "current_version": CURRENT_VERSION,
        "update_available": coordinator.update_available,
        "latest_version": coordinator._latest_version,
        "update_url": coordinator._update_url,
        "last_update": data.get("last_update"),
        "scan_duration": data.get("scan_duration", 0),
        "startup_remaining": coordinator.startup_remaining,
    }

    return _serialize_value(payload)


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/subscribe",
})
@websocket_api.async_response
async def websocket_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe to Cardio4HA data updates."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Cardio4HA coordinator not found")
        return

    @callback
    def async_on_update():
        """Forward coordinator updates to the WebSocket client."""
        try:
            payload = _build_payload(hass, coordinator)
            connection.send_message(
                websocket_api.event_message(msg["id"], payload)
            )
        except Exception:
            _LOGGER.exception("Error sending WebSocket update")

    unsub = coordinator.async_add_listener(async_on_update)
    connection.subscriptions[msg["id"]] = unsub

    connection.send_result(msg["id"])
    if coordinator.data:
        payload = _build_payload(hass, coordinator)
        connection.send_message(
            websocket_api.event_message(msg["id"], payload)
        )


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/force_scan",
})
@websocket_api.async_response
async def websocket_force_scan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Force an immediate scan."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    await coordinator.async_refresh()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/set_maintenance",
    vol.Optional("device_key"): str,
    vol.Optional("entity_id"): str,
    vol.Optional("duration", default=3600): int,
    vol.Optional("name", default=""): str,
    vol.Optional("area", default=""): str,
})
@websocket_api.async_response
async def websocket_set_maintenance(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Set a device as under maintenance."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    device_key = msg.get("device_key") or msg.get("entity_id")
    if not device_key:
        connection.send_error(msg["id"], "invalid_format", "device_key is required")
        return

    coordinator.set_maintenance(device_key, msg["duration"], msg.get("name", ""), msg.get("area", ""))
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/clear_maintenance",
    vol.Optional("device_key"): str,
    vol.Optional("entity_id"): str,
})
@websocket_api.async_response
async def websocket_clear_maintenance(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Clear maintenance status."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    device_key = msg.get("device_key") or msg.get("entity_id")
    if device_key:
        coordinator.clear_maintenance(device_key)
    else:
        coordinator.clear_all_maintenance()

    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/clear_history",
    vol.Optional("entity_id"): str,
})
@websocket_api.async_response
async def websocket_clear_history(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Clear unavailable tracking history."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    entity_id = msg.get("entity_id")
    if entity_id:
        coordinator.unavailable_tracking.pop(entity_id, None)
        coordinator.device_history.clear_device(entity_id)
    else:
        coordinator.unavailable_tracking = {}
        coordinator.device_history.clear_all()

    await coordinator.async_save_unavailable_data()
    await coordinator.device_history.async_save()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/get_device_timeline",
    vol.Required("device_key"): str,
    vol.Optional("days", default=30): int,
})
@websocket_api.async_response
async def websocket_get_device_timeline(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Get timeline data for a specific device."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    device_key = msg["device_key"]
    days = msg.get("days", 30)

    timeline = coordinator.device_history.get_device_timeline(device_key, days)
    battery_readings = coordinator.device_history.get_battery_readings(device_key, days)
    signal_readings = coordinator.device_history.get_signal_readings(device_key, days)
    battery_prediction = coordinator.device_history.predict_battery_days(device_key)

    connection.send_result(msg["id"], {
        "device_key": device_key,
        "timeline": timeline,
        "battery_readings": battery_readings,
        "signal_readings": signal_readings,
        "battery_prediction": battery_prediction,
    })


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/set_ignore",
    vol.Required("device_key"): str,
    vol.Optional("name", default=""): str,
    vol.Optional("area", default=""): str,
})
@websocket_api.async_response
async def websocket_set_ignore(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Permanently ignore a device."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    coordinator.set_ignore(msg["device_key"], msg.get("name", ""), msg.get("area", ""))
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/clear_ignore",
    vol.Optional("device_key"): str,
})
@websocket_api.async_response
async def websocket_clear_ignore(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Clear ignore status for a device or all devices."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    device_key = msg.get("device_key")
    if device_key:
        coordinator.clear_ignore(device_key)
    else:
        coordinator.clear_all_ignored()

    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): "cardio4ha/update_config",
    vol.Optional(CONF_BATTERY_CRITICAL): int,
    vol.Optional(CONF_BATTERY_WARNING): int,
    vol.Optional(CONF_BATTERY_LOW): int,
    vol.Optional(CONF_LINKQUALITY_WARNING): int,
    vol.Optional(CONF_RSSI_WARNING): int,
    vol.Optional(CONF_UNAVAILABLE_WARNING): int,
    vol.Optional(CONF_UNAVAILABLE_CRITICAL): int,
    vol.Optional(CONF_UPDATE_INTERVAL): int,
})
@websocket_api.async_response
async def websocket_update_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Update configuration thresholds from the panel."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    entry = coordinator.entry
    new_options = dict(entry.options)

    config_keys = [
        CONF_BATTERY_CRITICAL, CONF_BATTERY_WARNING, CONF_BATTERY_LOW,
        CONF_LINKQUALITY_WARNING, CONF_RSSI_WARNING,
        CONF_UNAVAILABLE_WARNING, CONF_UNAVAILABLE_CRITICAL,
        CONF_UPDATE_INTERVAL,
    ]

    for key in config_keys:
        if key in msg:
            new_options[key] = msg[key]

    hass.config_entries.async_update_entry(entry, options=new_options)
    connection.send_result(msg["id"], {"success": True})
