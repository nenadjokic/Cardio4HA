"""Smart notification engine for Cardio4HA."""
from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
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
    NOTIFY_TYPE_DEVICE_OFFLINE,
    NOTIFY_TYPE_BATTERY_CRITICAL,
    NOTIFY_TYPE_MASS_OFFLINE,
    NOTIFY_TYPE_DEVICE_RECOVERED,
    NOTIFY_TYPE_DAILY_DIGEST,
    MASS_OFFLINE_WINDOW,
    SEVERITY_CRITICAL,
)

_LOGGER = logging.getLogger(__name__)


class NotificationEngine:
    """Smart notification engine with rate limiting and grouping."""

    def __init__(self, hass: HomeAssistant, config_getter) -> None:
        """Initialize notification engine.

        config_getter: callable(key, default) -> value
        """
        self._hass = hass
        self._get_config = config_getter

        # Rate limiting state
        self._hourly_timestamps: deque[float] = deque()
        self._device_cooldowns: dict[str, float] = {}  # device_key -> last_notify_ts

        # Mass offline detection
        self._recent_offline_ts: list[float] = []
        self._mass_offline_sent_ts: float = 0

        # Previous scan state for detecting transitions
        self._previous_unavailable_keys: set[str] = set()
        self._previous_critical_battery_keys: set[str] = set()

        # Notification history (last 50 for panel display)
        self.notification_history: list[dict[str, Any]] = []

        # Daily digest scheduler
        self._digest_unsub = None
        self._schedule_daily_digest()

        # Latest scan data for digest
        self._last_scan_data: dict[str, Any] | None = None

    def _cfg(self, key: str, default: Any) -> Any:
        """Get config value."""
        return self._get_config(key, default)

    def _schedule_daily_digest(self) -> None:
        """Schedule daily digest notification."""
        if self._digest_unsub:
            self._digest_unsub()
            self._digest_unsub = None

        if not self._cfg(CONF_NOTIFY_DAILY_DIGEST, DEFAULT_NOTIFY_DAILY_DIGEST):
            return

        time_str = self._cfg(CONF_NOTIFY_DAILY_DIGEST_TIME, DEFAULT_NOTIFY_DAILY_DIGEST_TIME)
        try:
            hour, minute = map(int, time_str.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 7, 0

        @callback
        def _daily_digest_callback(now: datetime) -> None:
            """Handle daily digest trigger."""
            self._hass.async_create_task(self._send_daily_digest())

        self._digest_unsub = async_track_time_change(
            self._hass, _daily_digest_callback, hour=hour, minute=minute, second=0
        )

    async def process_scan_results(self, data: dict[str, Any]) -> None:
        """Process scan results and trigger appropriate notifications."""
        self._last_scan_data = data

        instant_enabled = self._cfg(CONF_NOTIFY_INSTANT_ENABLED, DEFAULT_NOTIFY_INSTANT_ENABLED)
        recovery_enabled = self._cfg(CONF_NOTIFY_RECOVERY_ENABLED, DEFAULT_NOTIFY_RECOVERY_ENABLED)
        offline_minutes = self._cfg(CONF_NOTIFY_OFFLINE_MINUTES, DEFAULT_NOTIFY_OFFLINE_MINUTES)
        battery_critical_level = self._cfg(CONF_NOTIFY_BATTERY_CRITICAL_LEVEL, DEFAULT_NOTIFY_BATTERY_CRITICAL_LEVEL)
        mass_threshold = self._cfg(CONF_NOTIFY_MASS_OFFLINE_THRESHOLD, DEFAULT_NOTIFY_MASS_OFFLINE_THRESHOLD)

        # Current state
        current_unavailable_keys = set()
        for d in data.get("unavailable", []):
            dk = d.get("device_key")
            if dk and d.get("duration_seconds", 0) >= offline_minutes * 60:
                current_unavailable_keys.add(dk)

        current_critical_battery_keys = set()
        for d in data.get("low_battery", []):
            dk = d.get("device_key")
            if dk and d.get("battery_level", 100) < battery_critical_level:
                current_critical_battery_keys.add(dk)

        # ── Mass offline detection ──
        newly_offline = current_unavailable_keys - self._previous_unavailable_keys
        now = time.time()

        if newly_offline:
            self._recent_offline_ts.extend([now] * len(newly_offline))
            # Clean old entries
            self._recent_offline_ts = [
                ts for ts in self._recent_offline_ts
                if now - ts < MASS_OFFLINE_WINDOW
            ]

            if (len(self._recent_offline_ts) >= mass_threshold
                    and now - self._mass_offline_sent_ts > MASS_OFFLINE_WINDOW):
                # Mass offline event
                self._mass_offline_sent_ts = now
                if instant_enabled:
                    names = []
                    for d in data.get("unavailable", []):
                        if d.get("device_key") in newly_offline:
                            names.append(d.get("name", "Unknown"))
                    await self._send_notification(
                        NOTIFY_TYPE_MASS_OFFLINE,
                        f"Mass Offline Alert: {len(newly_offline)} devices",
                        f"{len(newly_offline)} devices went offline simultaneously:\n"
                        + "\n".join(f"- {n}" for n in names[:10])
                        + (f"\n... and {len(names) - 10} more" if len(names) > 10 else ""),
                    )
                # Clear recent tracking after grouped alert
                self._recent_offline_ts.clear()
                newly_offline = set()  # Don't send individual alerts

        # ── Individual offline alerts ──
        if instant_enabled and newly_offline:
            for dk in newly_offline:
                if not self._check_device_cooldown(dk):
                    continue
                dev_info = self._find_device(data.get("unavailable", []), dk)
                if dev_info:
                    await self._send_notification(
                        NOTIFY_TYPE_DEVICE_OFFLINE,
                        f"Device Offline: {dev_info.get('name', 'Unknown')}",
                        f"{dev_info.get('name', 'Unknown')} has been offline for "
                        f"{dev_info.get('duration_human', 'unknown')}."
                        + (f"\nArea: {dev_info['area']}" if dev_info.get("area") else ""),
                        device_key=dk,
                    )

        # ── Battery critical alerts ──
        if instant_enabled:
            newly_critical = current_critical_battery_keys - self._previous_critical_battery_keys
            for dk in newly_critical:
                if not self._check_device_cooldown(dk):
                    continue
                dev_info = self._find_device(data.get("low_battery", []), dk)
                if dev_info:
                    level = dev_info.get("battery_level", "?")
                    days_str = ""
                    days_remaining = dev_info.get("days_remaining")
                    if days_remaining is not None:
                        days_str = f"\nEstimated {days_remaining} days remaining."
                    await self._send_notification(
                        NOTIFY_TYPE_BATTERY_CRITICAL,
                        f"Critical Battery: {dev_info.get('name', 'Unknown')} ({level}%)",
                        f"{dev_info.get('name', 'Unknown')} battery is critically low at {level}%."
                        + days_str
                        + (f"\nArea: {dev_info['area']}" if dev_info.get("area") else ""),
                        device_key=dk,
                    )

        # ── Recovery notifications ──
        if recovery_enabled:
            recovered = self._previous_unavailable_keys - current_unavailable_keys
            for dk in recovered:
                if not self._check_device_cooldown(dk):
                    continue
                # Try to find name from previous data
                await self._send_notification(
                    NOTIFY_TYPE_DEVICE_RECOVERED,
                    f"Device Recovered: {dk}",
                    f"Device {dk} is back online.",
                    device_key=dk,
                )

        # Update previous state
        self._previous_unavailable_keys = current_unavailable_keys
        self._previous_critical_battery_keys = current_critical_battery_keys

    async def _send_daily_digest(self) -> None:
        """Send daily digest if there are critical issues."""
        if not self._last_scan_data:
            return

        data = self._last_scan_data
        summary = data.get("summary", {})
        critical = summary.get("critical_count", 0)
        warning = summary.get("warning_count", 0)
        health = summary.get("health_score", 100)
        unavail = summary.get("unavailable_count", 0)
        low_batt = summary.get("low_battery_count", 0)
        weak_sig = summary.get("weak_signal_count", 0)
        flaky = summary.get("flaky_count", 0)

        # Only send if there are issues
        if critical == 0 and warning == 0:
            return

        lines = [
            f"Health Score: {health}/100",
            f"Unavailable: {unavail}",
            f"Low Battery: {low_batt}",
            f"Weak Signal: {weak_sig}",
            f"Flaky Devices: {flaky}",
            f"Critical: {critical}, Warnings: {warning}",
        ]

        # Top critical devices
        top = []
        for d in data.get("unavailable", [])[:3]:
            if d.get("severity") == SEVERITY_CRITICAL:
                top.append(f"- {d['name']} (offline {d.get('duration_human', '?')})")
        for d in data.get("low_battery", [])[:3]:
            if d.get("severity") == SEVERITY_CRITICAL:
                top.append(f"- {d['name']} ({d.get('battery_level', '?')}%)")

        if top:
            lines.append("\nTop issues:")
            lines.extend(top[:5])

        await self._send_notification(
            NOTIFY_TYPE_DAILY_DIGEST,
            f"Cardio4HA Daily Digest - Health: {health}/100",
            "\n".join(lines),
        )

    async def _send_notification(
        self,
        notify_type: str,
        title: str,
        message: str,
        device_key: str | None = None,
    ) -> None:
        """Send a notification via configured service."""
        if not self._check_rate_limit():
            _LOGGER.debug("Rate limit reached, skipping notification: %s", title)
            return

        service = self._cfg(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)

        try:
            if service == "persistent_notification":
                await self._hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": title,
                        "message": message,
                        "notification_id": f"cardio4ha_{notify_type}_{device_key or 'system'}",
                    },
                    blocking=False,
                )
            else:
                await self._hass.services.async_call(
                    "notify",
                    service,
                    {"title": title, "message": message},
                    blocking=False,
                )

            # Record to history
            self._record_history(notify_type, title, message, device_key)

            # Update device cooldown
            if device_key:
                self._device_cooldowns[device_key] = time.time()

            _LOGGER.info("Notification sent: %s", title)
        except Exception as err:
            _LOGGER.error("Error sending notification: %s", err)

    def _check_rate_limit(self) -> bool:
        """Check if we're within the global rate limit."""
        rate_limit = self._cfg(CONF_NOTIFY_RATE_LIMIT, DEFAULT_NOTIFY_RATE_LIMIT)
        now = time.time()
        cutoff = now - 3600

        # Clean old timestamps
        while self._hourly_timestamps and self._hourly_timestamps[0] < cutoff:
            self._hourly_timestamps.popleft()

        if len(self._hourly_timestamps) >= rate_limit:
            return False

        self._hourly_timestamps.append(now)
        return True

    def _check_device_cooldown(self, device_key: str) -> bool:
        """Check if device is within cooldown period."""
        cooldown_minutes = self._cfg(CONF_NOTIFY_DEVICE_COOLDOWN, DEFAULT_NOTIFY_DEVICE_COOLDOWN)
        last_ts = self._device_cooldowns.get(device_key)
        if last_ts is None:
            return True
        return (time.time() - last_ts) >= (cooldown_minutes * 60)

    def _record_history(
        self, notify_type: str, title: str, message: str, device_key: str | None
    ) -> None:
        """Record notification to history list."""
        self.notification_history.append({
            "type": notify_type,
            "title": title,
            "message": message,
            "device_key": device_key,
            "ts": dt_util.utcnow().isoformat(),
        })
        # Keep last 50
        if len(self.notification_history) > 50:
            self.notification_history = self.notification_history[-50:]

    @staticmethod
    def _find_device(device_list: list[dict], device_key: str) -> dict | None:
        """Find device info by device_key in a list."""
        for d in device_list:
            if d.get("device_key") == device_key:
                return d
        return None

    def unload(self) -> None:
        """Clean up on unload."""
        if self._digest_unsub:
            self._digest_unsub()
            self._digest_unsub = None
