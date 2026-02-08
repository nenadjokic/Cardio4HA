# Changelog

All notable changes to Cardio4HA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/nenadjokic/Cardio4HA/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nenadjokic/Cardio4HA/releases/tag/v0.1.0
