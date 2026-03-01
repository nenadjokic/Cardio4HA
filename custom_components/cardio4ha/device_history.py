"""Device history tracking for Cardio4HA with persistent storage."""
from __future__ import annotations

import logging
import math
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEVICE_HISTORY_STORAGE_KEY,
    DEVICE_HISTORY_STORAGE_VERSION,
    BATTERY_READING_INTERVAL,
    MIN_BATTERY_READINGS_FOR_PREDICTION,
    DEFAULT_HISTORY_RETENTION_DAYS,
)

_LOGGER = logging.getLogger(__name__)


class DeviceHistory:
    """Manages persistent device event history using HA Store API."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize device history."""
        self._hass = hass
        self._store = Store(hass, DEVICE_HISTORY_STORAGE_VERSION, DEVICE_HISTORY_STORAGE_KEY)
        self._data: dict[str, dict[str, Any]] = {}
        self._dirty = False

    async def async_load(self) -> None:
        """Load history data from storage."""
        try:
            stored = await self._store.async_load()
            if stored and isinstance(stored, dict):
                self._data = stored.get("devices", {})
                _LOGGER.info("Loaded device history for %d devices", len(self._data))
            else:
                self._data = {}
        except Exception as err:
            _LOGGER.error("Error loading device history: %s", err)
            self._data = {}

    async def async_save(self) -> None:
        """Save history data to storage if dirty."""
        if not self._dirty:
            return
        try:
            await self._store.async_save({"devices": self._data})
            self._dirty = False
            _LOGGER.debug("Saved device history for %d devices", len(self._data))
        except Exception as err:
            _LOGGER.error("Error saving device history: %s", err)

    def _ensure_device(self, device_key: str) -> dict:
        """Ensure device entry exists and return it."""
        if device_key not in self._data:
            self._data[device_key] = {
                "events": [],
                "battery_readings": [],
                "signal_readings": [],
            }
        return self._data[device_key]

    def record_offline_event(self, device_key: str) -> None:
        """Record a device going offline."""
        device = self._ensure_device(device_key)
        now = time.time()
        # Avoid duplicate offline events (check last event)
        events = device["events"]
        if events and events[-1]["type"] == "offline":
            return
        events.append({"type": "offline", "ts": now})
        self._dirty = True

    def record_online_event(self, device_key: str) -> None:
        """Record a device coming back online."""
        device = self._ensure_device(device_key)
        now = time.time()
        events = device["events"]
        if events and events[-1]["type"] == "online":
            return
        events.append({"type": "online", "ts": now})
        self._dirty = True

    def record_battery_reading(self, device_key: str, level: int) -> None:
        """Record a battery level reading. Deduplicates: only if level changed or >1hr since last."""
        device = self._ensure_device(device_key)
        readings = device["battery_readings"]
        now = time.time()

        if readings:
            last = readings[-1]
            if last["level"] == level and (now - last["ts"]) < BATTERY_READING_INTERVAL:
                return

        readings.append({"ts": now, "level": level})
        self._dirty = True

    def record_signal_reading(self, device_key: str, value: float) -> None:
        """Record a signal strength reading. Throttled to 1/hr/device."""
        device = self._ensure_device(device_key)
        readings = device["signal_readings"]
        now = time.time()

        if readings and (now - readings[-1]["ts"]) < BATTERY_READING_INTERVAL:
            return

        readings.append({"ts": now, "value": value})
        self._dirty = True

    def get_device_timeline(self, device_key: str, days: int = 30) -> list[dict]:
        """Get daily uptime percentages for timeline visualization.

        Returns list of {date: "YYYY-MM-DD", uptime_pct: float, events: int}
        for each day in the range.
        """
        device = self._data.get(device_key)
        if not device:
            return []

        now = time.time()
        cutoff = now - (days * 86400)
        events = [e for e in device["events"] if e["ts"] >= cutoff]

        if not events:
            # No events = fully online for the period
            return self._generate_empty_timeline(days)

        # Build per-day stats
        timeline = {}
        for day_offset in range(days):
            day_start = now - ((days - day_offset) * 86400)
            day_end = day_start + 86400
            date_str = self._ts_to_date(day_start)

            day_events = [e for e in events if day_start <= e["ts"] < day_end]
            event_count = len(day_events)

            # Calculate offline seconds for this day
            offline_seconds = self._calc_offline_seconds(events, day_start, day_end)
            uptime_pct = max(0.0, min(100.0, 100.0 * (1.0 - offline_seconds / 86400.0)))

            timeline[date_str] = {
                "date": date_str,
                "uptime_pct": round(uptime_pct, 1),
                "events": event_count,
            }

        return list(timeline.values())

    def _calc_offline_seconds(self, events: list[dict], day_start: float, day_end: float) -> float:
        """Calculate total offline seconds within a time window."""
        offline_seconds = 0.0
        # Find state at day_start by looking at events before this window
        is_offline = False
        for e in events:
            if e["ts"] >= day_start:
                break
            is_offline = (e["type"] == "offline")

        current_time = day_start
        for e in events:
            if e["ts"] >= day_end:
                break
            if e["ts"] < day_start:
                continue

            if is_offline:
                offline_seconds += e["ts"] - current_time

            current_time = e["ts"]
            is_offline = (e["type"] == "offline")

        # Handle remainder of day
        if is_offline:
            offline_seconds += min(day_end, time.time()) - current_time

        return offline_seconds

    def _generate_empty_timeline(self, days: int) -> list[dict]:
        """Generate timeline with 100% uptime for all days."""
        now = time.time()
        result = []
        for day_offset in range(days):
            day_start = now - ((days - day_offset) * 86400)
            result.append({
                "date": self._ts_to_date(day_start),
                "uptime_pct": 100.0,
                "events": 0,
            })
        return result

    @staticmethod
    def _ts_to_date(ts: float) -> str:
        """Convert timestamp to YYYY-MM-DD string."""
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    def get_offline_event_count(self, device_key: str, days: int = 30) -> int:
        """Count offline events in the last N days."""
        device = self._data.get(device_key)
        if not device:
            return 0
        cutoff = time.time() - (days * 86400)
        return sum(1 for e in device["events"] if e["ts"] >= cutoff and e["type"] == "offline")

    def get_battery_readings(self, device_key: str, days: int = 30) -> list[dict]:
        """Get battery readings for the last N days."""
        device = self._data.get(device_key)
        if not device:
            return []
        cutoff = time.time() - (days * 86400)
        return [r for r in device["battery_readings"] if r["ts"] >= cutoff]

    def get_signal_readings(self, device_key: str, days: int = 30) -> list[dict]:
        """Get signal readings for the last N days."""
        device = self._data.get(device_key)
        if not device:
            return []
        cutoff = time.time() - (days * 86400)
        return [r for r in device["signal_readings"] if r["ts"] >= cutoff]

    def predict_battery_days(self, device_key: str) -> int | None:
        """Predict days until battery reaches 0% using linear regression.

        Returns None if insufficient data.
        """
        device = self._data.get(device_key)
        if not device:
            return None

        readings = device["battery_readings"]
        if len(readings) < MIN_BATTERY_READINGS_FOR_PREDICTION:
            return None

        # Use last 30 days of readings
        cutoff = time.time() - (30 * 86400)
        recent = [r for r in readings if r["ts"] >= cutoff]
        if len(recent) < MIN_BATTERY_READINGS_FOR_PREDICTION:
            return None

        # Linear regression: level = slope * time + intercept
        times = [r["ts"] for r in recent]
        levels = [r["level"] for r in recent]

        n = len(times)
        t_mean = sum(times) / n
        v_mean = sum(levels) / n

        numerator = sum((t - t_mean) * (v - v_mean) for t, v in zip(times, levels))
        denominator = sum((t - t_mean) ** 2 for t in times)

        if denominator == 0:
            return None

        slope = numerator / denominator  # level change per second

        if slope >= 0:
            # Battery not draining
            return None

        # Current level (use last reading)
        current_level = recent[-1]["level"]
        if current_level <= 0:
            return 0

        # Time to reach 0
        seconds_remaining = -current_level / slope
        days_remaining = int(seconds_remaining / 86400)

        # Sanity check: cap at 365 days
        return min(days_remaining, 365)

    def purge_old_data(self, retention_days: int = DEFAULT_HISTORY_RETENTION_DAYS) -> None:
        """Remove events older than retention period."""
        cutoff = time.time() - (retention_days * 86400)
        keys_to_remove = []

        for device_key, device in self._data.items():
            device["events"] = [e for e in device["events"] if e["ts"] >= cutoff]
            device["battery_readings"] = [r for r in device["battery_readings"] if r["ts"] >= cutoff]
            device["signal_readings"] = [r for r in device["signal_readings"] if r["ts"] >= cutoff]

            # Remove device entry if no data left
            if not device["events"] and not device["battery_readings"] and not device["signal_readings"]:
                keys_to_remove.append(device_key)

        for key in keys_to_remove:
            del self._data[key]

        if keys_to_remove:
            self._dirty = True
            _LOGGER.debug("Purged history for %d devices with no recent data", len(keys_to_remove))

    def clear_device(self, device_key: str) -> None:
        """Clear all history for a specific device."""
        if device_key in self._data:
            del self._data[device_key]
            self._dirty = True

    def clear_all(self) -> None:
        """Clear all device history."""
        self._data = {}
        self._dirty = True
