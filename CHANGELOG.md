# Changelog

All notable changes to Cardio4HA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nenadjokic/Cardio4HA/releases/tag/v0.1.0
