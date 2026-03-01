"""The Cardio4HA integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    SERVICE_MARK_AS_MAINTENANCE,
    SERVICE_CLEAR_HISTORY,
    SERVICE_FORCE_SCAN,
    SERVICE_CLEAR_DEVICE_HISTORY,
    SERVICE_SET_IGNORE,
    SERVICE_CLEAR_IGNORE,
)
from .coordinator import Cardio4HACoordinator
from .notifications import NotificationEngine
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Frontend paths - sidebar panel only (Lovelace card removed in v1.0.0)
PANEL_JS_URL = f"/{DOMAIN}/cardio4ha-panel.js"
PANEL_JS_PATH = Path(__file__).parent / "panel" / "cardio4ha-panel.js"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cardio4HA from a config entry."""
    _LOGGER.info("Setting up Cardio4HA v1.1.0")

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

    # Create notification engine
    notification_engine = NotificationEngine(hass, coordinator._get_config_value)
    coordinator.notification_engine = notification_engine

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register frontend (sidebar panel only)
    await _async_register_frontend(hass)

    # Register WebSocket API
    async_register_websocket_api(hass)

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Setup services
    await _async_setup_services(hass)

    # Setup options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Cardio4HA v1.1.0 setup complete")
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register the sidebar panel."""
    if hass.data.get(f"{DOMAIN}_frontend"):
        return

    # Register sidebar panel JS
    await hass.http.async_register_static_paths([
        StaticPathConfig(PANEL_JS_URL, str(PANEL_JS_PATH), cache_headers=False),
    ])

    # Register sidebar panel
    try:
        await async_register_panel(
            hass,
            frontend_url_path=DOMAIN,
            webcomponent_name="cardio4ha-panel",
            sidebar_title="Cardio4HA",
            sidebar_icon="mdi:heart-pulse",
            module_url=PANEL_JS_URL,
            require_admin=False,
            config={},
        )
        _LOGGER.info("Registered Cardio4HA sidebar panel")
    except Exception:
        _LOGGER.exception("Failed to register sidebar panel")

    hass.data[f"{DOMAIN}_frontend"] = True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Cardio4HA integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_save_unavailable_data()
        await coordinator.async_save_ignore_data()
        await coordinator.device_history.async_save()
        if coordinator.notification_engine:
            coordinator.notification_engine.unload()

    # Remove sidebar panel if no more entries
    if not hass.data.get(DOMAIN):
        try:
            async_remove_panel(hass, DOMAIN)
        except Exception:
            pass
        hass.data.pop(f"{DOMAIN}_frontend", None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _get_coordinator(hass: HomeAssistant) -> Cardio4HACoordinator | None:
    """Get the first available coordinator."""
    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        return None
    for coordinator in domain_data.values():
        if isinstance(coordinator, Cardio4HACoordinator):
            return coordinator
    return None


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Cardio4HA."""

    async def handle_mark_as_maintenance(call) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        device_key = call.data.get("device_key") or call.data.get("entity_id")
        duration = call.data.get("duration", 3600)
        name = call.data.get("name", "")
        if device_key:
            coordinator.set_maintenance(device_key, duration, name)

    async def handle_clear_history(call) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        entity_id = call.data.get("entity_id")
        if entity_id:
            coordinator.unavailable_tracking.pop(entity_id, None)
            await coordinator.async_save_unavailable_data()
        else:
            coordinator.unavailable_tracking = {}
            await coordinator.async_save_unavailable_data()

    async def handle_force_scan(call) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        coordinator.force_scan()

    async def handle_clear_device_history(call) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        device_key = call.data.get("device_key")
        if device_key:
            coordinator.device_history.clear_device(device_key)
        else:
            coordinator.device_history.clear_all()
        await coordinator.device_history.async_save()

    async def handle_set_ignore(call) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        device_key = call.data.get("device_key")
        name = call.data.get("name", "")
        if device_key:
            coordinator.set_ignore(device_key, name)

    async def handle_clear_ignore(call) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        device_key = call.data.get("device_key")
        if device_key:
            coordinator.clear_ignore(device_key)
        else:
            coordinator.clear_all_ignored()

    if not hass.services.has_service(DOMAIN, SERVICE_MARK_AS_MAINTENANCE):
        hass.services.async_register(DOMAIN, SERVICE_MARK_AS_MAINTENANCE, handle_mark_as_maintenance)
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_HISTORY):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_HISTORY, handle_clear_history)
    if not hass.services.has_service(DOMAIN, SERVICE_FORCE_SCAN):
        hass.services.async_register(DOMAIN, SERVICE_FORCE_SCAN, handle_force_scan)
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_DEVICE_HISTORY):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_DEVICE_HISTORY, handle_clear_device_history)
    if not hass.services.has_service(DOMAIN, SERVICE_SET_IGNORE):
        hass.services.async_register(DOMAIN, SERVICE_SET_IGNORE, handle_set_ignore)
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_IGNORE):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR_IGNORE, handle_clear_ignore)
