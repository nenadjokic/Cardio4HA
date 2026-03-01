# Cardio4HA - Device Health Monitor

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/nenadjokic/Cardio4HA.svg)](https://github.com/nenadjokic/Cardio4HA/releases)
[![License](https://img.shields.io/github/license/nenadjokic/Cardio4HA.svg)](LICENSE)

> **Your smart home's cardiologist** - Monitor the health of all your devices in one place!

Cardio4HA is a Home Assistant custom integration that acts like a doctor for your smart home. It continuously monitors all your devices, scores your network health, predicts battery failures, detects flaky devices, and sends smart notifications - all from a beautiful sidebar panel.

## Why Cardio4HA?

If you have **dozens or hundreds** of smart devices, you know the pain:
- Devices go offline and you don't notice for days
- Batteries die without warning
- Weak signals cause random failures
- Some devices are "flaky" - constantly dropping and reconnecting
- No easy way to see what needs attention

**Cardio4HA solves all of this** with zero configuration.

## Features

### Health Score (0-100)
A single number that tells you how healthy your smart home is. Weighted across four factors:
- Unavailable devices (40%)
- Low batteries (25%)
- Weak signals (20%)
- Flaky devices (15%)

### Flaky Device Detection
Statistically identifies devices that frequently go offline and come back. These "unstable" devices are flagged with a purple badge across all views so you can focus on fixing the root cause.

### Battery Prediction
Uses linear regression on 30 days of battery readings to predict when each battery will die. See "X days left" for every low-battery device.

### 30-Day Device History
Every device gets a timeline showing daily uptime over the past 30 days (Statuspage.io style). Expand any device row to see its history, trend charts, and details.

### Smart Notifications
- **Instant alerts** - Device offline, battery critically low, mass offline events
- **Recovery notifications** - When devices come back online
- **Daily digest** - Morning summary when critical issues exist
- **3-layer rate limiting** - Global hourly limit, per-device cooldown, mass offline grouping (no notification storms)

### Sidebar Panel
A full-page dashboard pinned to your HA sidebar with 5 views:
- **Overview** - Health score ring, summary cards, recent notifications, flaky device list
- **Unavailable** - Sortable/filterable table with expandable rows, 30-day timeline bars
- **Battery** - Battery bars with prediction badges, trend charts
- **Signal** - 5-bar signal indicators, signal trend charts
- **Maintenance** - Manage devices under maintenance and permanently ignored devices

All views support search, area filtering, severity filtering, and CSV export.

### Per-Device Ignore (v1.1.0)
Permanently hide specific devices from all monitoring views with one click. Unlike Maintenance (temporary with expiration), Ignore is permanent until manually cleared.
- Click **Ignore** on any expanded device row (Unavailable, Battery, or Signal views)
- Ignored devices disappear from all views and health score calculations
- Manage all ignored devices from the **Maintenance** tab with Un-ignore / Clear All
- Persists across HA restarts

### Additional Capabilities
- Device-level tracking (shows devices, not individual sensors)
- Smart unavailable detection (only flags devices where ALL entities are unavailable)
- Zigbee2MQTT override (always monitors Z2M even if integration is excluded)
- Advanced exclusions (wildcards, integrations, areas)
- Persistent history across HA restarts
- Handles 300+ devices with scans under 5 seconds

## Support the Project

If you find Cardio4HA helpful, consider supporting its development:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/nenadjokic)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/nenadjokicRS)

Star this repo on GitHub if you find it useful!

---

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click **Integrations** tab
3. Click the three-dot menu (top right) -> **Custom repositories**
4. Add repository: `https://github.com/nenadjokic/Cardio4HA`, category: **Integration**
5. Click **Add**, close the dialog
6. Click **+ Explore & Download Repositories**
7. Search for **Cardio4HA**, click it, click **Download**
8. **Restart Home Assistant**

### Method 2: Manual

1. Download the latest release from [GitHub Releases](https://github.com/nenadjokic/Cardio4HA/releases)
2. Copy the `cardio4ha` folder to `config/custom_components/`
3. Restart Home Assistant

## Setup

1. Go to **Settings** -> **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Cardio4HA**
4. Click **Submit**
5. Done! Cardio4HA appears in your sidebar and starts monitoring immediately.

No configuration needed. All defaults are sensible for any installation.

## What You Get

### Sidebar Panel

After setup, **Cardio4HA** appears in your sidebar (like Energy or Map). Click it to open the full dashboard with all 5 views, health score ring, expandable device rows, and timeline bars.

### 9 Sensor Entities

| Sensor | Description |
|--------|-------------|
| `sensor.cardio4ha_health_score` | Overall health score (0-100%) |
| `sensor.cardio4ha_unavailable_devices` | Number of offline devices |
| `sensor.cardio4ha_low_battery_devices` | Number of low battery devices |
| `sensor.cardio4ha_weak_signal_devices` | Number of weak signal devices |
| `sensor.cardio4ha_flaky_devices` | Number of flaky/unstable devices |
| `sensor.cardio4ha_critical_issues` | Total critical problems |
| `sensor.cardio4ha_warning_issues` | Total warnings |
| `sensor.cardio4ha_healthy_devices` | Number of healthy devices |
| `sensor.cardio4ha_last_scan_duration` | Scan time in seconds |

Each sensor includes detailed device lists in its attributes for use in automations and templates.

### Services

| Service | Description |
|---------|-------------|
| `cardio4ha.force_scan` | Trigger an immediate scan |
| `cardio4ha.mark_as_maintenance` | Mark a device as under maintenance |
| `cardio4ha.clear_history` | Clear unavailable tracking history |
| `cardio4ha.clear_device_history` | Clear 30-day device event history |
| `cardio4ha.set_ignore` | Permanently ignore a device from monitoring |
| `cardio4ha.clear_ignore` | Un-ignore a device or clear all ignored |

## Configuration

Configuration is optional - Cardio4HA works great with defaults. To customize:

1. Go to **Settings** -> **Devices & Services**
2. Find **Cardio4HA** -> **Configure**

### Step 1: Thresholds & Exclusions

| Setting | Default | Description |
|---------|---------|-------------|
| Update Interval | 60s | How often to scan |
| Battery Critical | 15% | Critical battery level |
| Battery Warning | 30% | Warning battery level |
| Battery Low | 50% | Low battery level |
| Link Quality Warning | 100 | Zigbee LQI threshold |
| RSSI Warning | -70 dBm | WiFi signal threshold |
| Unavailable Warning | 1 hour | Duration before warning |
| Unavailable Critical | 6 hours | Duration before critical |
| Exclude Entity Wildcards | - | Comma-separated patterns (e.g., `sensor.temp_*`) |
| Exclude Integrations | - | Select integrations to skip |
| Exclude Areas | - | Select areas to skip |
| Monitor Zigbee2MQTT | On | Always monitor Z2M entities |

### Step 2: Notifications

| Setting | Default | Description |
|---------|---------|-------------|
| Notification Service | persistent_notification | Which notify service to use |
| Instant Alerts | On | Alert on device offline / critical battery |
| Offline Threshold | 15 min | Minutes before offline alert fires |
| Battery Critical Level | 10% | Battery level that triggers alert |
| Mass Offline Threshold | 3 | Devices offline simultaneously to group alert |
| Daily Digest | On | Morning summary when issues exist |
| Daily Digest Time | 07:00 | When to send digest |
| Recovery Notifications | On | Alert when devices come back online |
| Rate Limit | 10/hr | Max notifications per hour |
| Device Cooldown | 30 min | Min time between alerts for same device |
| History Retention | 30 days | How long to keep device history |

## Automations

### Alert on Health Score Drop

```yaml
alias: "Alert on Low Health Score"
trigger:
  - platform: numeric_state
    entity_id: sensor.cardio4ha_health_score
    below: 70
action:
  - service: notify.mobile_app
    data:
      title: "Device Health Warning"
      message: >
        Health score dropped to {{ states('sensor.cardio4ha_health_score') }}%.
        {{ states('sensor.cardio4ha_critical_issues') }} critical issues.
```

### Alert on Critical Issues

```yaml
alias: "Alert on Critical Device Issues"
trigger:
  - platform: state
    entity_id: sensor.cardio4ha_critical_issues
    from: "0"
action:
  - service: notify.mobile_app
    data:
      title: "Critical Device Issues"
      message: >
        {{ states('sensor.cardio4ha_critical_issues') }} critical issues need attention!
```

### Alert on Flaky Devices

```yaml
alias: "Alert on Flaky Devices"
trigger:
  - platform: state
    entity_id: sensor.cardio4ha_flaky_devices
    from: "0"
action:
  - service: notify.mobile_app
    data:
      title: "Flaky Devices Detected"
      message: >
        {{ states('sensor.cardio4ha_flaky_devices') }} devices are unstable
        and need investigation.
```

## Dashboard Cards

While the sidebar panel is the primary interface, you can still add sensor cards to your Lovelace dashboard:

```yaml
type: entities
title: Device Health
entities:
  - entity: sensor.cardio4ha_health_score
    name: Health Score
    icon: mdi:heart-pulse
  - entity: sensor.cardio4ha_critical_issues
    name: Critical Issues
    icon: mdi:alert
  - entity: sensor.cardio4ha_unavailable_devices
    name: Unavailable
    icon: mdi:alert-circle-outline
  - entity: sensor.cardio4ha_low_battery_devices
    name: Low Battery
    icon: mdi:battery-alert
  - entity: sensor.cardio4ha_weak_signal_devices
    name: Weak Signal
    icon: mdi:signal-off
  - entity: sensor.cardio4ha_flaky_devices
    name: Flaky Devices
    icon: mdi:swap-horizontal
```

## Performance

Cardio4HA is designed for large installations:
- Handles **300+ devices** easily
- Scans complete in **< 5 seconds**
- 30-day history storage stays under **1 MB**
- Minimal CPU/memory usage with smart deduplication

## Upgrading from v1.0.0

The upgrade is automatic:
- New ignore storage initializes empty
- All existing stores (unavailable tracking, maintenance, device history) are preserved
- New "Ignore" buttons appear on expanded device rows
- New "Ignored Devices" section appears in the Maintenance tab
- Two new services: `set_ignore` and `clear_ignore`

## Upgrading from v0.3.0

The upgrade is automatic:
- Config flow migrates to v2 (new notification settings get defaults)
- Existing stores (unavailable tracking, maintenance) are preserved
- New stores (device history) initialize empty and populate over time
- Battery predictions appear after ~5 battery readings (a few hours)
- Flaky detection improves as history accumulates over 30 days
- The old Lovelace card has been removed - use the sidebar panel instead

## FAQ

**Q: Will this slow down my Home Assistant?**
No. Scans run every 60 seconds by default and complete in under 5 seconds even with 300+ devices.

**Q: Does it work with all integrations?**
Yes. It monitors any entity in Home Assistant regardless of integration.

**Q: What happens if I restart Home Assistant?**
All history is persisted to disk and restored automatically.

**Q: Can I exclude certain devices?**
Yes. Use wildcards, integration exclusions, or area exclusions in the options flow. You can also click "Ignore" on any device row to permanently hide it from all views.

**Q: What's the difference between Maintenance and Ignore?**
Maintenance is temporary (expires after a set duration). Ignore is permanent until you manually un-ignore the device from the Maintenance tab.

**Q: When will battery predictions start working?**
After approximately 5 battery readings (a few hours of operation). More readings = more accurate predictions.

**Q: When will flaky detection kick in?**
It needs offline events to analyze. Devices are flagged as flaky when they have 3+ offline events that exceed the statistical threshold across all your devices.

**Q: How does the health score work?**
It starts at 100 and deducts points based on the ratio of problematic devices: unavailable (40% weight), low battery (25%), weak signal (20%), flaky (15%).

## Troubleshooting

### Integration doesn't appear after restart
1. Check logs: **Settings** -> **System** -> **Logs**
2. Look for errors mentioning "cardio4ha"
3. Make sure the folder is in `config/custom_components/cardio4ha/`

### Sensors show "Unknown"
1. Wait 60 seconds for first scan
2. Check `sensor.cardio4ha_last_scan_duration` - if it shows a number, scanning works

### Panel not showing in sidebar
1. Check that `frontend`, `http`, `panel_custom`, `websocket_api` are available
2. Try clearing browser cache / hard refresh

### Battery devices not detected
1. Entity needs `device_class: battery` or "battery" in its name
2. Battery level must be between 0-100

## Contributing

- [Report Issues](https://github.com/nenadjokic/Cardio4HA/issues)
- [Request Features](https://github.com/nenadjokic/Cardio4HA/issues)
- [Submit Pull Requests](https://github.com/nenadjokic/Cardio4HA/pulls)

## License

MIT License - Free and open source!

---

**Made with care for the Home Assistant community**

Questions? Open an [issue](https://github.com/nenadjokic/Cardio4HA/issues)!
