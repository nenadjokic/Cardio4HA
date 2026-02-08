# Changelog

All notable changes to Cardio4HA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2026-02-08

### Added
- **Phase 2: Advanced Exclusion System**
  - **Wildcard pattern exclusions**: Visual UI to add wildcard patterns for entity exclusion (e.g., `sensor.temp_*`, `*_battery`)
  - **Integration-based exclusions**: Multi-select to exclude entire integrations/platforms from monitoring
  - **Area-based exclusions**: Multi-select to exclude all entities in specific areas
  - **Zigbee2MQTT Override**: Special toggle to always monitor Zigbee2MQTT entities (enabled by default)
    - Even if excluded by other rules, Zigbee2MQTT entities will be monitored since they commonly lose signals in practice
- **Customizable Thresholds per Category**
  - **Signal strength thresholds**: Separate configuration for Zigbee linkquality and WiFi RSSI warnings
  - **Unavailable duration thresholds**: Configure both warning and critical thresholds for unavailable devices
  - All thresholds now configurable in Options UI

### Improved
- Enhanced configuration UI with organized settings sections
- Better wildcard matching using fnmatch for more flexible patterns
- Smarter exclusion logic that respects Zigbee2MQTT override

### Technical Details
- Added fnmatch support for advanced wildcard pattern matching
- Extended config_flow with multi-select dropdowns for integrations and areas
- Dynamically populated integration and area lists from entity/area registries
- Exclusion evaluation order: Zigbee2MQTT override → domain → integration → area → wildcards

## [0.1.6] - 2026-02-08

### Fixed
- **Smart unavailable detection**: Device is now only marked as unavailable if ALL its entities are unavailable
  - Example: If iPad has 10 sensors and 9 are unavailable but 1 is available, iPad is NOT marked as unavailable
  - This prevents false positives where a device appears unavailable when it's actually functioning
  - Greatly improves accuracy of unavailable device tracking
- **Filter out Cardio4HA's own sensors**: Integration now excludes its own sensors from all tracking categories
  - Fixes bug where "Cardio4HA - 9.0%" appeared in low battery devices
  - Prevents self-tracking circular references

### Technical Details
- Implemented two-pass device entity counting algorithm
- Added device_entity_counts tracking structure to count total vs unavailable entities per device
- Added integration platform filtering to exclude DOMAIN sensors

## [0.1.5] - 2026-02-08

### Changed
- **MAJOR: Device-level tracking instead of sensor-level tracking**
  - Now tracks devices, not individual sensors
  - When a device has multiple sensors (e.g., iPad with 10+ sensors), only the device appears once in unavailable/battery/signal lists
  - Significantly reduces clutter and makes monitoring more intuitive
  - Example: Instead of showing "iPad sensor 1", "iPad sensor 2", etc., now shows just "iPad"
  - Applies to all categories: unavailable devices, low battery, and weak signal
  - Standalone entities (without parent devices) are still tracked individually

### Technical Details
- Added device deduplication using `device_id` tracking sets
- Prioritizes device name over sensor name when displaying results
- Maintains backward compatibility for entities without associated devices

## [0.1.4] - 2026-02-08

### Fixed
- **Entity naming (FINAL FIX)**: Complete rewrite of entity naming strategy
  - Now uses device_info with has_entity_name pattern (Home Assistant best practice)
  - Sensors are grouped under "Cardio4HA" device in Devices page
  - Entity IDs are correctly: `sensor.cardio4ha_unavailable_devices`, `sensor.cardio4ha_low_battery_devices`, etc.
  - Sensor friendly names simplified (no "Cardio4HA" prefix needed in name)
  - **REQUIRES: Delete and re-add integration for existing installations**

## [0.1.3] - 2026-02-08

### Fixed
- **Entity ID consistency**: Explicitly set `object_id` for all sensors to guarantee correct entity IDs
  - Ensures entity IDs are always: `sensor.cardio4ha_unavailable_devices`, `sensor.cardio4ha_low_battery_devices`, etc.
  - Prevents auto-generated entity_id mismatches

### Improved
- Simplified README by removing confusing custom card section
- All dashboard examples now work out-of-the-box without custom cards

## [0.1.2] - 2026-02-08

### Changed
- **Improved sensor naming**: All sensor names now include "Cardio4HA" prefix for easier identification in large Home Assistant installations
  - Example: "Unavailable Devices" → "Cardio4HA Unavailable Devices"
  - Entity IDs remain consistent: `sensor.cardio4ha_unavailable_devices`, etc.

### Fixed
- Updated README dashboard card examples with correct entity names
- Fixed markdown card example to display actual sensor values instead of "unknown"
- Added working template-based markdown card example

## [0.1.1] - 2026-02-08

### Fixed
- **Critical bug fix**: Corrected registry access to use proper imports (`er.async_get()`, `dr.async_get()`, `ar.async_get()`) instead of `self.hass.helpers.entity_registry.async_get()` which was causing `'HomeAssistant' object has no attribute 'helpers'` error on integration setup
- Fixed "Config flow could not be loaded: 500 Internal Server Error" during integration installation

## [0.1.0] - 2026-02-08

### Added
- Initial release of Cardio4HA
- Core device health monitoring functionality
- Unavailable device tracking with persistence across HA restarts
- Battery level monitoring with severity classification
- Signal strength detection (Zigbee LQI, WiFi RSSI)
- 7 sensor entities for device health metrics:
  - Unavailable Devices Count
  - Low Battery Devices Count
  - Weak Signal Devices Count
  - Critical Issues Count
  - Warning Issues Count
  - Healthy Devices Count
  - Last Scan Duration
- Simple one-click setup via Config Flow (no YAML required!)
- Options flow for customizing thresholds
- Automatic exclusion of non-monitored domains (sun, weather, updater)
- Performance optimized for 200+ devices (<5 second scans)
- Comprehensive logging for debugging

### Technical Details
- Uses DataUpdateCoordinator pattern for efficient updates
- Implements Home Assistant Store for data persistence
- Smart battery detection via device_class and entity_id keywords
- Automatic sorting: unavailable by duration, batteries by level
- Full async/await implementation
- Type hints throughout codebase

[Unreleased]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.7...HEAD
[0.1.7]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nenadjokic/Cardio4HA/releases/tag/v0.1.0
