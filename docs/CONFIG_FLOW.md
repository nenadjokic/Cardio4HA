# Config Flow Implementation Guide

## 🎯 Goal
Create a user-friendly configuration interface for Cardio4HA that allows users to:
- Configure thresholds for battery, signal, and unavailable durations
- Exclude specific domains and entities
- Set update intervals
- Modify settings after installation

---

## 📝 config_flow.py Implementation

```python
"""Config flow for Cardio4HA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
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
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_DISABLED,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_BATTERY_CRITICAL,
    DEFAULT_BATTERY_WARNING,
    DEFAULT_BATTERY_LOW,
    DEFAULT_LINKQUALITY_WARNING,
    DEFAULT_RSSI_WARNING,
    DEFAULT_UNAVAILABLE_WARNING,
    DEFAULT_UNAVAILABLE_CRITICAL,
    DEFAULT_EXCLUDE_DOMAINS,
    DEFAULT_INCLUDE_DISABLED,
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
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate input
            if not self._validate_thresholds(user_input):
                errors["base"] = "invalid_thresholds"
            else:
                # Create entry
                return self.async_create_entry(
                    title="Cardio4HA",
                    data={},
                    options=user_input,
                )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=DEFAULT_UPDATE_INTERVAL,
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def _validate_thresholds(user_input: dict[str, Any]) -> bool:
        """Validate threshold values."""
        # Battery thresholds must be in order: critical < warning < low
        battery_critical = user_input.get(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL)
        battery_warning = user_input.get(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING)
        battery_low = user_input.get(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW)

        if not (battery_critical < battery_warning < battery_low <= 100):
            return False

        # Unavailable thresholds: warning < critical
        unavailable_warning = user_input.get(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING)
        unavailable_critical = user_input.get(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL)

        if not (unavailable_warning < unavailable_critical):
            return False

        return True

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
        return await self.async_step_thresholds()

    async def async_step_thresholds(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure thresholds."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate thresholds
            if not self._validate_thresholds(user_input):
                errors["base"] = "invalid_thresholds"
            else:
                # Save and move to next step
                self.options = user_input
                return await self.async_step_filters()

        # Get current values
        current = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=current.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)),
                vol.Optional(
                    CONF_BATTERY_CRITICAL,
                    default=current.get(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_BATTERY_WARNING,
                    default=current.get(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_BATTERY_LOW,
                    default=current.get(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_LINKQUALITY_WARNING,
                    default=current.get(CONF_LINKQUALITY_WARNING, DEFAULT_LINKQUALITY_WARNING),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
                vol.Optional(
                    CONF_RSSI_WARNING,
                    default=current.get(CONF_RSSI_WARNING, DEFAULT_RSSI_WARNING),
                ): vol.All(vol.Coerce(int), vol.Range(min=-100, max=0)),
                vol.Optional(
                    CONF_UNAVAILABLE_WARNING,
                    default=current.get(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),  # Max 24 hours
                vol.Optional(
                    CONF_UNAVAILABLE_CRITICAL,
                    default=current.get(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=604800)),  # Max 7 days
            }
        )

        return self.async_show_form(
            step_id="thresholds",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "update_interval_desc": f"Scan interval in seconds ({MIN_UPDATE_INTERVAL}-{MAX_UPDATE_INTERVAL})",
                "battery_desc": "Battery thresholds: Critical < Warning < Low",
                "unavailable_desc": "Unavailable duration in seconds",
            },
        )

    async def async_step_filters(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure filters."""
        if user_input is not None:
            # Merge with threshold options
            self.options.update(user_input)
            
            # Create options entry
            return self.async_create_entry(title="", data=self.options)

        # Get current values
        current = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_EXCLUDE_DOMAINS,
                    default=",".join(current.get(CONF_EXCLUDE_DOMAINS, DEFAULT_EXCLUDE_DOMAINS)),
                ): cv.string,
                vol.Optional(
                    CONF_EXCLUDE_ENTITIES,
                    default=",".join(current.get(CONF_EXCLUDE_ENTITIES, [])),
                ): cv.string,
                vol.Optional(
                    CONF_INCLUDE_DISABLED,
                    default=current.get(CONF_INCLUDE_DISABLED, DEFAULT_INCLUDE_DISABLED),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="filters",
            data_schema=data_schema,
            description_placeholders={
                "exclude_domains_desc": "Comma-separated list of domains to exclude (e.g., sun,weather)",
                "exclude_entities_desc": "Comma-separated list of entity patterns to exclude (e.g., sensor.sun_*,weather.*)",
                "include_disabled_desc": "Include disabled entities in monitoring",
            },
        )

    @staticmethod
    def _validate_thresholds(user_input: dict[str, Any]) -> bool:
        """Validate threshold values."""
        battery_critical = user_input.get(CONF_BATTERY_CRITICAL, DEFAULT_BATTERY_CRITICAL)
        battery_warning = user_input.get(CONF_BATTERY_WARNING, DEFAULT_BATTERY_WARNING)
        battery_low = user_input.get(CONF_BATTERY_LOW, DEFAULT_BATTERY_LOW)

        if not (battery_critical < battery_warning < battery_low <= 100):
            return False

        unavailable_warning = user_input.get(CONF_UNAVAILABLE_WARNING, DEFAULT_UNAVAILABLE_WARNING)
        unavailable_critical = user_input.get(CONF_UNAVAILABLE_CRITICAL, DEFAULT_UNAVAILABLE_CRITICAL)

        if not (unavailable_warning < unavailable_critical):
            return False

        return True
```

---

## 📝 strings.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Configure Cardio4HA",
        "description": "Set up device health monitoring",
        "data": {
          "update_interval": "Update Interval (seconds)"
        }
      }
    },
    "error": {
      "invalid_thresholds": "Invalid threshold configuration. Ensure battery thresholds are in order (critical < warning < low) and unavailable warning < critical."
    }
  },
  "options": {
    "step": {
      "thresholds": {
        "title": "Configure Thresholds",
        "description": "Set warning levels for device health issues",
        "data": {
          "update_interval": "Update Interval (seconds)",
          "battery_critical": "Battery Critical Threshold (%)",
          "battery_warning": "Battery Warning Threshold (%)",
          "battery_low": "Battery Low Threshold (%)",
          "linkquality_warning": "Zigbee Link Quality Warning",
          "rssi_warning": "WiFi RSSI Warning (dBm)",
          "unavailable_warning": "Unavailable Warning (seconds)",
          "unavailable_critical": "Unavailable Critical (seconds)"
        },
        "data_description": {
          "update_interval": "How often to scan for device issues (30-300 seconds)",
          "battery_critical": "Battery level below this triggers critical alert",
          "battery_warning": "Battery level below this triggers warning",
          "battery_low": "Battery level below this is considered low",
          "linkquality_warning": "Zigbee link quality below this triggers warning",
          "rssi_warning": "WiFi signal below this triggers warning (more negative = worse)",
          "unavailable_warning": "Time until device unavailable triggers warning",
          "unavailable_critical": "Time until device unavailable triggers critical alert"
        }
      },
      "filters": {
        "title": "Configure Filters",
        "description": "Exclude specific domains or entities from monitoring",
        "data": {
          "exclude_domains": "Excluded Domains",
          "exclude_entities": "Excluded Entity Patterns",
          "include_disabled": "Include Disabled Entities"
        },
        "data_description": {
          "exclude_domains": "Comma-separated list (e.g., sun,weather,updater)",
          "exclude_entities": "Comma-separated patterns with * wildcard (e.g., sensor.sun_*,weather.*)",
          "include_disabled": "Monitor entities that are currently disabled"
        }
      }
    },
    "error": {
      "invalid_thresholds": "Invalid threshold configuration. Battery thresholds must be: critical < warning < low. Unavailable thresholds must be: warning < critical."
    }
  }
}
```

---

## 🎨 Configuration UI Flow

### Initial Setup Flow
```
1. User adds integration via UI
   ↓
2. Shows basic config (update interval only)
   ↓
3. User clicks Submit
   ↓
4. Integration creates with defaults
   ↓
5. User can configure via Options
```

### Options Flow (Multi-Step)
```
1. User clicks Configure on integration
   ↓
2. Step 1: Thresholds
   - Update interval
   - Battery thresholds (critical, warning, low)
   - Signal thresholds (LQI, RSSI)
   - Unavailable thresholds (warning, critical)
   ↓
3. Step 2: Filters
   - Exclude domains
   - Exclude entities (patterns)
   - Include disabled entities toggle
   ↓
4. Save configuration
   ↓
5. Integration reloads with new settings
```

---

## 🧪 Testing Config Flow

### Manual Tests
1. **Initial Setup**
   ```
   - Add integration
   - Verify defaults applied
   - Check sensors created
   ```

2. **Threshold Validation**
   ```
   - Try invalid battery order (warning > low)
   - Try invalid unavailable (critical < warning)
   - Verify error message shows
   ```

3. **Options Flow**
   ```
   - Change update interval
   - Modify thresholds
   - Add exclusions
   - Verify integration reloads
   - Check new values applied
   ```

4. **Edge Cases**
   ```
   - Empty exclusions
   - Invalid entity patterns
   - Extreme threshold values
   ```

---

## 💡 Advanced Configuration Examples

### Exclude Multiple Domains
```yaml
exclude_domains: "sun,weather,updater,zone,automation,script"
```

### Exclude Entity Patterns
```yaml
exclude_entities: "sensor.sun_*,weather.*,binary_sensor.updater,sensor.time*"
```

### Strict Battery Monitoring
```yaml
battery_critical: 10   # Alert immediately below 10%
battery_warning: 20    # Warn below 20%
battery_low: 35        # Track below 35%
```

### Quick Unavailable Detection
```yaml
unavailable_warning: 1800    # 30 minutes
unavailable_critical: 3600   # 1 hour
```

### Performance Tuning
```yaml
update_interval: 120   # Check every 2 minutes (less load)
```

---

## 🎯 Best Practices

1. **Start with Defaults**: Let users install with defaults first
2. **Clear Descriptions**: Explain what each threshold means
3. **Validation**: Prevent invalid configurations
4. **Examples**: Show example values in placeholders
5. **Reload Smoothly**: Ensure changes apply without issues

---

## 🐛 Common Config Issues

### Issue: Thresholds Rejected
**Cause**: Battery thresholds not in correct order
**Solution**: Ensure critical < warning < low

### Issue: Exclusions Not Working
**Cause**: Incorrect pattern syntax
**Solution**: Use * for wildcards, comma-separate patterns

### Issue: Changes Not Applied
**Cause**: Integration not reloading
**Solution**: Ensure `add_update_listener` in __init__.py

---

**Next**: Implement binary sensors and services
